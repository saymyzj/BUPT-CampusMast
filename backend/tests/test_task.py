from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models import *  # noqa: F403
from app.models.base import Base
from app.models.config import SystemConfig
from app.models.enums import TaskCategory, TaskStatus
from app.models.map import CampusBuilding
from app.models.task import Task, TaskLog
from app.models.user import User
from app.models.wallet import Wallet
from app.routers.task import router as task_router
import app.services.task_service as task_service_module
from app.services.task_service import (
    ALLOWED_TRANSITIONS,
    TaskError,
    accept_task,
    abandon_task,
    cancel_task,
    close_dispute_by_admin,
    confirm_task,
    create_task,
    dispute_in_progress_task,
    expire_pending_tasks,
    expire_task,
    reject_task,
    resolve_dispute_for_helper,
    resolve_dispute_for_requester,
    resolve_dispute_split,
    submit_task_proof,
    task_to_dict,
)
from app.models.enums import Role
from app.models.rating import CreditSnapshot
from app.models.wallet import Transaction
from app.services.wallet_service import WalletError, wallet_to_dict


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def add_user(db_session, user_id: str, *, helper_score: str = "100.00", available: str = "0.00") -> None:
    db_session.add(
        User(
            id=user_id,
            student_email=f"{user_id}@bupt.edu.cn",
            password_hash="hash",
            nickname=user_id,
            helper_credit_score=Decimal(helper_score),
        )
    )
    db_session.add(
        Wallet(
            id=f"wallet_{user_id}",
            user_id=user_id,
            available=Decimal(available),
            frozen=Decimal("0.00"),
        )
    )
    db_session.commit()


def add_admin(db_session, user_id: str = "admin") -> None:
    db_session.add(
        User(
            id=user_id,
            student_email=f"{user_id}@bupt.edu.cn",
            password_hash="hash",
            nickname=user_id,
            role=Role.ADMIN,
        )
    )
    db_session.commit()


def add_building(db_session, code: str, x: float, y: float) -> None:
    db_session.add(CampusBuilding(code=code, name=code, x_coord=x, y_coord=y, is_active=True))
    db_session.commit()


def set_helper_credit_threshold(db_session, value: str) -> None:
    db_session.merge(
        SystemConfig(
            config_key="task.acceptance.helperCreditThreshold",
            config_group="task",
            config_value=value,
            description="Helper credit threshold for tests",
        )
    )
    db_session.commit()


def task_payload(reward: str = "20.00") -> SimpleNamespace:
    return SimpleNamespace(
        title="Pick up package",
        description="Pick up a package from the school gate.",
        category="package",
        reward=reward,
        deadline=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        buildingCode="BUPT_MAIN",
        locationDetail="Gate",
        imageUrls=[],
    )


def proof_payload() -> SimpleNamespace:
    return SimpleNamespace(proofNote="Delivered to requester.", proofImageUrls=[])


def task_payload_json(reward: str = "20.00") -> dict:
    payload = task_payload(reward)
    return {
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "reward": payload.reward,
        "deadline": payload.deadline,
        "buildingCode": payload.buildingCode,
        "locationDetail": payload.locationDetail,
        "imageUrls": payload.imageUrls,
    }


@pytest.fixture
def task_api_client(db_session):
    app = FastAPI()
    app.include_router(task_router)
    current_user = {"id": "requester", "role": "USER", "nickname": "requester"}

    def override_db():
        yield db_session

    def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client, current_user


def test_create_task_freezes_reward_and_writes_initial_log(db_session) -> None:
    add_user(db_session, "requester", available="100.00")

    task = create_task(db_session, "requester", task_payload("30.00"))

    wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert task.status == TaskStatus.PENDING
    assert wallet_to_dict(wallet) == {"available": "70.00", "frozen": "30.00", "total": "100.00"}
    logs = db_session.query(TaskLog).filter_by(task_id=task.id).all()
    assert len(logs) == 1


def test_full_task_flow_settles_funds_once_completed(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")

    task = create_task(db_session, "requester", task_payload("25.00"))
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())
    completed = confirm_task(db_session, task.id, "requester")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    assert completed.status == TaskStatus.COMPLETED
    assert wallet_to_dict(requester_wallet) == {"available": "75.00", "frozen": "0.00", "total": "75.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "30.00", "frozen": "0.00", "total": "30.00"}
    assert task_to_dict(db_session, completed)["status"] == "COMPLETED"


def test_cancel_pending_task_unfreezes_reward(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    task = create_task(db_session, "requester", task_payload("40.00"))

    cancelled = cancel_task(db_session, task.id, "requester")

    wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert cancelled.status == TaskStatus.CANCELLED
    assert wallet_to_dict(wallet) == {"available": "100.00", "frozen": "0.00", "total": "100.00"}


def test_accept_requires_helper_credit_threshold(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", helper_score="59.99")
    task = create_task(db_session, "requester", task_payload("20.00"))

    with pytest.raises(TaskError):
        accept_task(db_session, task.id, "helper")

    db_session.rollback()
    stored = db_session.get(Task, task.id)
    assert stored.status == TaskStatus.PENDING
    assert stored.helper_id is None


def test_accept_uses_helper_credit_threshold_from_system_configs(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", helper_score="75.00")
    set_helper_credit_threshold(db_session, "80.00")
    task = create_task(db_session, "requester", task_payload("20.00"))

    with pytest.raises(TaskError) as exc:
        accept_task(db_session, task.id, "helper")
    db_session.rollback()

    assert exc.value.code == "HELPER_CREDIT_TOO_LOW"
    assert db_session.get(Task, task.id).status == TaskStatus.PENDING


def test_accept_threshold_falls_back_to_default_for_invalid_config(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", helper_score="75.00")
    set_helper_credit_threshold(db_session, '"invalid"')
    task = create_task(db_session, "requester", task_payload("20.00"))

    accepted = accept_task(db_session, task.id, "helper")

    assert accepted.status == TaskStatus.IN_PROGRESS


def test_concurrent_accept_allows_only_one_helper(tmp_path) -> None:
    db_path = tmp_path / "task_concurrency.sqlite3"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    setup = SessionLocal()
    add_user(setup, "requester", available="100.00")
    add_user(setup, "helper_a")
    add_user(setup, "helper_b")
    task = create_task(setup, "requester", task_payload("20.00"))
    task_id = task.id
    setup.close()

    def try_accept(helper_id: str) -> str:
        session = SessionLocal()
        try:
            accept_task(session, task_id, helper_id)
            return "ok"
        except TaskError:
            return "rejected"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(try_accept, ["helper_a", "helper_b"]))

    verify = SessionLocal()
    stored = verify.get(Task, task_id)
    verify.close()
    assert results.count("ok") == 1
    assert results.count("rejected") == 1
    assert stored.status == TaskStatus.IN_PROGRESS
    assert stored.helper_id in {"helper_a", "helper_b"}


def test_mysql_acceptance_lock_and_version_guard_sql_is_generated() -> None:
    lock_sql = str(
        select(Task).where(Task.id == "task_1").with_for_update().compile(dialect=mysql.dialect())
    )
    update_sql = str(
        update(Task)
        .where(
            Task.id == "task_1",
            Task.status == TaskStatus.PENDING,
            Task.helper_id.is_(None),
            Task.version == 1,
        )
        .values(helper_id="helper", status=TaskStatus.IN_PROGRESS, version=2)
        .compile(dialect=mysql.dialect())
    )

    assert "FOR UPDATE" in lock_sql
    assert "version" in update_sql
    assert "helper_id IS NULL" in update_sql


def test_task_detail_api_contains_frozen_fields(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")

    create_response = client.post("/tasks", json=task_payload_json("20.00"))
    assert create_response.status_code == 201
    assert create_response.json()["success"] is True
    task_id = create_response.json()["data"]["id"]

    response = client.get(f"/tasks/{task_id}")
    data = response.json()["data"]
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert data["deadline"]
    assert data["createdAt"]
    assert data["proofNote"] is None
    assert data["proofImageUrls"] == []
    assert isinstance(data["logs"], list)
    assert data["logs"][0]["fromStatus"] == "PENDING"
    assert current_user["id"] == "requester"


def test_create_task_api_returns_201_success_response(task_api_client, db_session) -> None:
    client, _current_user = task_api_client
    add_user(db_session, "requester", available="100.00")

    response = client.post("/tasks", json=task_payload_json("15.00"))

    body = response.json()
    assert response.status_code == 201
    assert body["success"] is True
    assert body["meta"] is None
    assert body["data"]["status"] == "PENDING"


def test_task_list_api_supports_frozen_filters_and_sort(task_api_client, db_session) -> None:
    client, _current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    add_building(db_session, "NEAR", 0, 0)
    add_building(db_session, "FAR", 1000, 0)
    near = create_task(db_session, "requester", task_payload("10.00"))
    near.title = "Near package"
    near.building_code = "NEAR"
    far = create_task(db_session, "requester", task_payload("30.00"))
    far.title = "Far food"
    far.category = TaskCategory.FOOD
    far.building_code = "FAR"
    db_session.commit()

    response = client.get("/tasks", params={"category": "package", "keyword": "Near", "buildingCode": "NEAR"})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["data"]] == [near.id]

    reward_response = client.get("/tasks", params={"sortBy": "rewardDesc"})
    assert [row["id"] for row in reward_response.json()["data"]][:2] == [far.id, near.id]

    distance_response = client.get("/tasks", params={"nearBuildingCode": "NEAR", "sortBy": "distanceAsc"})
    assert [row["id"] for row in distance_response.json()["data"]][:2] == [near.id, far.id]


def test_my_task_api_lists_posted_and_accepted_tasks(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    posted = create_task(db_session, "requester", task_payload("20.00"))
    accepted = create_task(db_session, "requester", task_payload("30.00"))
    accept_task(db_session, accepted.id, "helper")

    current_user["id"] = "requester"
    posted_response = client.get("/tasks/my/posted", params={"status": "PENDING"})
    assert posted_response.status_code == 200
    assert [row["id"] for row in posted_response.json()["data"]] == [posted.id]
    assert posted_response.json()["meta"]["total"] == 1

    current_user["id"] = "helper"
    accepted_response = client.get("/tasks/my/accepted", params={"status": "IN_PROGRESS"})
    assert accepted_response.status_code == 200
    assert [row["id"] for row in accepted_response.json()["data"]] == [accepted.id]
    assert accepted_response.json()["meta"]["total"] == 1


def test_accept_task_api_rejects_duplicate_accept(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper_a")
    add_user(db_session, "helper_b")
    task = create_task(db_session, "requester", task_payload("20.00"))

    current_user["id"] = "helper_a"
    assert client.patch(f"/tasks/{task.id}/accept").status_code == 200

    current_user["id"] = "helper_b"
    response = client.patch(f"/tasks/{task.id}/accept")
    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "TASK_NOT_AVAILABLE_FOR_ACCEPTANCE"


def test_accept_task_api_rejects_requester_accepting_own_task(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    task = create_task(db_session, "requester", task_payload("20.00"))

    current_user["id"] = "requester"
    response = client.patch(f"/tasks/{task.id}/accept")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CANNOT_ACCEPT_OWN_TASK"


def test_accept_task_api_rejects_low_credit_helper(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", helper_score="59.99")
    task = create_task(db_session, "requester", task_payload("20.00"))

    current_user["id"] = "helper"
    response = client.patch(f"/tasks/{task.id}/accept")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "HELPER_CREDIT_TOO_LOW"


def test_accept_task_api_expires_overdue_task_and_unfreezes_reward(task_api_client, db_session) -> None:
    client, current_user = task_api_client
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    task.deadline = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    current_user["id"] = "helper"
    response = client.patch(f"/tasks/{task.id}/accept")

    wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    stored = db_session.get(Task, task.id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TASK_EXPIRED"
    assert stored.status == TaskStatus.EXPIRED
    assert wallet_to_dict(wallet) == {"available": "100.00", "frozen": "0.00", "total": "100.00"}


def test_confirm_task_rejects_duplicate_confirmation_without_duplicate_settlement(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("25.00"))
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())

    confirm_task(db_session, task.id, "requester")
    with pytest.raises(TaskError) as exc:
        confirm_task(db_session, task.id, "requester")
    db_session.rollback()

    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    assert exc.value.code == "TASK_NOT_PENDING_REVIEW"
    assert wallet_to_dict(helper_wallet) == {"available": "30.00", "frozen": "0.00", "total": "30.00"}


def test_cancel_task_rejects_non_pending_task(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")

    with pytest.raises(TaskError) as exc:
        cancel_task(db_session, task.id, "requester")

    assert exc.value.code == "ONLY_PENDING_TASK_CAN_BE_CANCELLED"


def test_abandon_task_requires_assigned_helper(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    add_user(db_session, "other_helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")

    with pytest.raises(TaskError) as exc:
        abandon_task(db_session, task.id, "other_helper")

    assert exc.value.code == "ONLY_ASSIGNED_HELPER_CAN_ABANDON"


def test_transition_rule_table_matches_frozen_document() -> None:
    assert ALLOWED_TRANSITIONS == {
        (TaskStatus.PENDING, TaskStatus.IN_PROGRESS),
        (TaskStatus.PENDING, TaskStatus.CANCELLED),
        (TaskStatus.PENDING, TaskStatus.EXPIRED),
        (TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW),
        (TaskStatus.IN_PROGRESS, TaskStatus.PENDING),
        (TaskStatus.IN_PROGRESS, TaskStatus.DISPUTED),
        (TaskStatus.PENDING_REVIEW, TaskStatus.COMPLETED),
        (TaskStatus.PENDING_REVIEW, TaskStatus.DISPUTED),
        (TaskStatus.DISPUTED, TaskStatus.COMPLETED),
        (TaskStatus.DISPUTED, TaskStatus.CANCELLED),
        (TaskStatus.DISPUTED, TaskStatus.CLOSED_BY_ADMIN),
    }


def test_expire_pending_tasks_batch_only_expires_overdue_pending_tasks(db_session) -> None:
    add_user(db_session, "system")
    add_user(db_session, "requester", available="100.00")
    expired_task = create_task(db_session, "requester", task_payload("20.00"))
    future_task = create_task(db_session, "requester", task_payload("30.00"))
    expired_task.deadline = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    expired = expire_pending_tasks(db_session, "system")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert [task.id for task in expired] == [expired_task.id]
    assert db_session.get(Task, expired_task.id).status == TaskStatus.EXPIRED
    assert db_session.get(Task, future_task.id).status == TaskStatus.PENDING
    assert wallet_to_dict(requester_wallet) == {"available": "70.00", "frozen": "30.00", "total": "100.00"}


def test_expire_task_rejects_non_pending_without_mutating_wallet_or_logs(db_session) -> None:
    add_user(db_session, "system")
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    before_wallet = wallet_to_dict(db_session.query(Wallet).filter_by(user_id="requester").one())
    before_transactions = db_session.query(Transaction).count()
    before_logs = db_session.query(TaskLog).filter_by(task_id=task.id).count()

    with pytest.raises(TaskError) as exc:
        expire_task(db_session, task.id, "system")
    db_session.rollback()

    stored = db_session.get(Task, task.id)
    assert exc.value.code == "ONLY_PENDING_TASK_CAN_EXPIRE"
    assert stored.status == TaskStatus.IN_PROGRESS
    assert wallet_to_dict(db_session.query(Wallet).filter_by(user_id="requester").one()) == before_wallet
    assert db_session.query(Transaction).count() == before_transactions
    assert db_session.query(TaskLog).filter_by(task_id=task.id).count() == before_logs


def test_in_progress_task_can_enter_dispute_with_log(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")

    disputed = dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    assert disputed.status == TaskStatus.DISPUTED
    assert db_session.query(TaskLog).filter_by(task_id=task.id, to_status=TaskStatus.DISPUTED).count() == 1


def test_pending_review_task_can_enter_dispute_with_log(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())

    disputed = reject_task(db_session, task.id, "requester", "proof rejected")

    assert disputed.status == TaskStatus.DISPUTED
    assert db_session.query(TaskLog).filter_by(task_id=task.id, to_status=TaskStatus.DISPUTED).count() == 1


def test_admin_can_resolve_dispute_for_helper_and_settle_reward(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    resolved = resolve_dispute_for_helper(db_session, task.id, "admin", "support helper")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    assert resolved.status == TaskStatus.COMPLETED
    assert wallet_to_dict(requester_wallet) == {"available": "80.00", "frozen": "0.00", "total": "80.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "25.00", "frozen": "0.00", "total": "25.00"}


def test_admin_can_resolve_dispute_for_requester_and_refund_reward(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    resolved = resolve_dispute_for_requester(db_session, task.id, "admin", "support requester")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert resolved.status == TaskStatus.CANCELLED
    assert wallet_to_dict(requester_wallet) == {"available": "100.00", "frozen": "0.00", "total": "100.00"}


def test_admin_can_close_dispute_and_refund_frozen_reward(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    closed = close_dispute_by_admin(db_session, task.id, "admin", "custom close")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert closed.status == TaskStatus.CLOSED_BY_ADMIN
    assert wallet_to_dict(requester_wallet) == {"available": "100.00", "frozen": "0.00", "total": "100.00"}


def test_admin_can_split_dispute_settlement(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    resolved = resolve_dispute_split(db_session, task.id, "admin", "0.25", "split settlement")

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    transactions = db_session.query(Transaction).filter_by(related_task_id=task.id).all()
    assert resolved.status == TaskStatus.CLOSED_BY_ADMIN
    assert wallet_to_dict(requester_wallet) == {"available": "95.00", "frozen": "0.00", "total": "95.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "10.00", "frozen": "0.00", "total": "10.00"}
    assert sorted(row.type.value for row in transactions) == ["FREEZE", "SETTLE_SPLIT", "SETTLE_SPLIT"]


def test_admin_helper_resolution_updates_requester_credit_snapshot(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())
    reject_task(db_session, task.id, "requester", "reject proof")

    resolve_dispute_for_helper(db_session, task.id, "admin", "support helper")

    snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="requester", role_scope="requester")
        .order_by(CreditSnapshot.calculated_at.desc(), CreditSnapshot.id.desc())
        .first()
    )
    requester = db_session.get(User, "requester")
    assert snapshot is not None
    assert float(snapshot.malicious_dispute_rate) == 100.0
    assert float(snapshot.calculated_score) == 85.0
    assert float(requester.requester_credit_score) == 85.0


def test_admin_requester_resolution_updates_helper_credit_snapshot(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    resolve_dispute_for_requester(db_session, task.id, "admin", "support requester")

    snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="helper", role_scope="helper")
        .order_by(CreditSnapshot.calculated_at.desc(), CreditSnapshot.id.desc())
        .first()
    )
    helper = db_session.get(User, "helper")
    assert snapshot is not None
    assert float(snapshot.dispute_lose_rate) == 100.0
    assert float(snapshot.calculated_score) == 55.0
    assert float(helper.helper_credit_score) == 55.0


def test_dispute_resolution_cannot_be_repeated_or_duplicate_funds(db_session) -> None:
    add_admin(db_session)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")

    resolve_dispute_for_helper(db_session, task.id, "admin", "support helper")
    before_transactions = db_session.query(Transaction).filter_by(related_task_id=task.id).count()
    before_helper_wallet = wallet_to_dict(db_session.query(Wallet).filter_by(user_id="helper").one())
    with pytest.raises(TaskError) as exc:
        resolve_dispute_for_helper(db_session, task.id, "admin", "repeat support helper")
    db_session.rollback()

    assert exc.value.code == "ONLY_DISPUTED_TASK_CAN_BE_RESOLVED"
    assert db_session.query(Transaction).filter_by(related_task_id=task.id).count() == before_transactions
    assert wallet_to_dict(db_session.query(Wallet).filter_by(user_id="helper").one()) == before_helper_wallet


def test_illegal_transition_does_not_mutate_task_wallet_or_ledger(db_session) -> None:
    add_user(db_session, "requester", available="100.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    before_wallet = wallet_to_dict(db_session.query(Wallet).filter_by(user_id="requester").one())
    before_transactions = db_session.query(Transaction).count()
    before_logs = db_session.query(TaskLog).filter_by(task_id=task.id).count()

    with pytest.raises(TaskError) as exc:
        confirm_task(db_session, task.id, "requester")
    db_session.rollback()

    stored = db_session.get(Task, task.id)
    assert exc.value.code == "TASK_NOT_PENDING_REVIEW"
    assert stored.status == TaskStatus.PENDING
    assert wallet_to_dict(db_session.query(Wallet).filter_by(user_id="requester").one()) == before_wallet
    assert db_session.query(Transaction).count() == before_transactions
    assert db_session.query(TaskLog).filter_by(task_id=task.id).count() == before_logs


def test_confirm_task_rolls_back_task_and_wallet_when_settlement_fails(db_session, monkeypatch) -> None:
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())

    def broken_settlement(db, requester_id, helper_id, amount, *, related_task_id):
        requester_wallet = db.query(Wallet).filter_by(user_id=requester_id).one()
        helper_wallet = db.query(Wallet).filter_by(user_id=helper_id).one()
        requester_wallet.frozen = Decimal("0.00")
        helper_wallet.available = Decimal("25.00")
        db.flush()
        raise WalletError("SIMULATED_SETTLEMENT_FAILURE", "Simulated settlement failure")

    monkeypatch.setattr(task_service_module, "settle_reward", broken_settlement)

    with pytest.raises(WalletError):
        confirm_task(db_session, task.id, "requester")
    db_session.rollback()

    stored = db_session.get(Task, task.id)
    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    assert stored.status == TaskStatus.PENDING_REVIEW
    assert wallet_to_dict(requester_wallet) == {"available": "80.00", "frozen": "20.00", "total": "100.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "5.00", "frozen": "0.00", "total": "5.00"}
    assert db_session.query(Transaction).filter(Transaction.type.in_(["SETTLE_OUT", "SETTLE_IN"])).count() == 0
