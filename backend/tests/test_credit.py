from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models import *  # noqa: F403
from app.models.base import Base
from app.models.config import SystemConfig
from app.models.enums import TaskStatus
from app.models.rating import CreditSnapshot, Rating
from app.models.task import TaskLog
from app.models.user import User
from app.models.wallet import Wallet
from app.routers.credit import router as credit_router
from app.routers.task import router as task_router
import app.services.credit_service as credit_service
from app.services.credit_service import (
    CreditError,
    get_credit_profile,
    list_received_ratings,
    rate_task_partner,
    recalculate_user_credit,
)
from app.services.task_service import (
    TaskError,
    accept_task,
    abandon_task,
    confirm_task,
    create_task,
    dispute_in_progress_task,
    reject_task,
    resolve_dispute_for_helper,
    resolve_dispute_for_requester,
    submit_task_proof,
)


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


def add_user(db_session, user_id: str, available: str = "0.00") -> None:
    db_session.add(
        User(
            id=user_id,
            student_email=f"{user_id}@bupt.edu.cn",
            password_hash="hash",
            nickname=user_id,
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


def set_credit_weights(db_session, value: dict | str) -> None:
    db_session.merge(
        SystemConfig(
            config_key="credit.weights",
            config_group="credit",
            config_value=json.dumps(value) if isinstance(value, dict) else value,
            description="Credit weights for tests",
        )
    )
    db_session.commit()


def task_payload() -> SimpleNamespace:
    return SimpleNamespace(
        title="Pick up package",
        description="Pick up a package from the school gate.",
        category="package",
        reward="20.00",
        deadline=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        buildingCode="BUPT_MAIN",
        locationDetail="Gate",
        imageUrls=[],
    )


def proof_payload() -> SimpleNamespace:
    return SimpleNamespace(proofNote="Delivered.", proofImageUrls=[])


def rating_payload(score: int = 5, comment: str = "Good") -> SimpleNamespace:
    return SimpleNamespace(score=score, comment=comment)


def completed_task(db_session):
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    task = create_task(db_session, "requester", task_payload())
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())
    confirm_task(db_session, task.id, "requester")
    return task


def abandoned_task(db_session, requester_id: str, helper_id: str):
    db_session.get(User, helper_id).helper_credit_score = Decimal("100.00")
    db_session.commit()
    task = create_task(db_session, requester_id, task_payload())
    accept_task(db_session, task.id, helper_id)
    abandon_task(db_session, task.id, helper_id)
    return task


def helper_lost_dispute_task(db_session, requester_id: str, helper_id: str):
    db_session.get(User, helper_id).helper_credit_score = Decimal("100.00")
    db_session.commit()
    task = create_task(db_session, requester_id, task_payload())
    accept_task(db_session, task.id, helper_id)
    dispute_in_progress_task(db_session, task.id, requester_id, "service abnormal")
    resolve_dispute_for_requester(db_session, task.id, "requester", "support requester")
    return task


def requester_lost_dispute_task(db_session, requester_id: str, helper_id: str):
    db_session.get(User, helper_id).helper_credit_score = Decimal("100.00")
    db_session.commit()
    task = create_task(db_session, requester_id, task_payload())
    accept_task(db_session, task.id, helper_id)
    submit_task_proof(db_session, task.id, helper_id, proof_payload())
    reject_task(db_session, task.id, requester_id, "malicious reject")
    resolve_dispute_for_helper(db_session, task.id, "admin", "support helper")
    return task


@pytest.fixture
def rating_api_client(db_session):
    app = FastAPI()
    app.include_router(task_router)
    current_user = SimpleNamespace(id="requester", role="USER", nickname="requester")

    def override_db():
        yield db_session

    def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client, current_user


def test_requester_can_rate_helper_after_task_completed(db_session) -> None:
    task = completed_task(db_session)

    rating = rate_task_partner(db_session, task.id, "requester", rating_payload(5, "Great helper"))

    stored = db_session.query(Rating).one()
    assert rating.id == stored.id
    assert stored.task_id == task.id
    assert stored.from_user_id == "requester"
    assert stored.to_user_id == "helper"
    assert stored.score == 5


def test_helper_can_rate_requester_after_task_completed(db_session) -> None:
    task = completed_task(db_session)

    rating = rate_task_partner(db_session, task.id, "helper", rating_payload(4, "Clear request"))

    assert rating.from_user_id == "helper"
    assert rating.to_user_id == "requester"
    assert rating.score == 4


def test_rating_api_writes_rating_response(rating_api_client, db_session) -> None:
    client, current_user = rating_api_client
    task = completed_task(db_session)

    current_user.id = "requester"
    response = client.post(f"/tasks/{task.id}/rating", json={"score": 5, "comment": "Great"})

    body = response.json()
    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["taskId"] == task.id
    assert body["data"]["fromUserId"] == "requester"
    assert body["data"]["toUserId"] == "helper"
    assert db_session.query(Rating).count() == 1


def test_rating_rejects_duplicate_from_same_user(db_session) -> None:
    task = completed_task(db_session)
    rate_task_partner(db_session, task.id, "requester", rating_payload())

    with pytest.raises(CreditError) as exc:
        rate_task_partner(db_session, task.id, "requester", rating_payload(4, "Again"))

    assert exc.value.code == "DUPLICATE_RATING"
    assert db_session.query(Rating).count() == 1


def test_rating_maps_database_unique_conflict_to_duplicate_error(db_session, monkeypatch) -> None:
    task = completed_task(db_session)
    rate_task_partner(db_session, task.id, "requester", rating_payload())
    monkeypatch.setattr(credit_service, "_ensure_not_rated", lambda *_args, **_kwargs: None)

    with pytest.raises(CreditError) as exc:
        rate_task_partner(db_session, task.id, "requester", rating_payload(4, "Again"))

    assert exc.value.code == "DUPLICATE_RATING"
    assert db_session.query(Rating).count() == 1


def test_legacy_credit_rating_stub_endpoint_is_not_registered() -> None:
    app = FastAPI()
    app.include_router(credit_router)

    with TestClient(app) as client:
        response = client.post("/credit/ratings", json={"score": 5, "comment": "fake"})

    assert response.status_code == 404


def test_credit_profile_service_returns_current_user_scores(db_session) -> None:
    add_user(db_session, "user")

    assert get_credit_profile(db_session, "user") == {
        "requesterCreditScore": 100.0,
        "helperCreditScore": 100.0,
        "overallCreditScore": 100.0,
    }


def test_rating_rejects_non_participant(db_session) -> None:
    task = completed_task(db_session)
    add_user(db_session, "outsider")

    with pytest.raises(CreditError) as exc:
        rate_task_partner(db_session, task.id, "outsider", rating_payload())

    assert exc.value.code == "RATING_USER_NOT_TASK_PARTICIPANT"


def test_rating_rejects_uncompleted_task(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper")
    task = create_task(db_session, "requester", task_payload())
    accept_task(db_session, task.id, "helper")

    with pytest.raises(CreditError) as exc:
        rate_task_partner(db_session, task.id, "requester", rating_payload())

    assert exc.value.code == "TASK_NOT_COMPLETED"
    assert db_session.get(type(task), task.id).status == TaskStatus.IN_PROGRESS


def test_rating_score_must_be_between_one_and_five(rating_api_client, db_session) -> None:
    client, current_user = rating_api_client
    task = completed_task(db_session)
    current_user.id = "requester"

    response = client.post(f"/tasks/{task.id}/rating", json={"score": 6, "comment": "Too high"})

    assert response.status_code == 422
    assert db_session.query(Rating).count() == 0


def test_credit_calculation_can_read_received_ratings(db_session) -> None:
    task = completed_task(db_session)
    rate_task_partner(db_session, task.id, "requester", rating_payload(5, "Great helper"))

    ratings = list_received_ratings(db_session, "helper")

    assert len(ratings) == 1
    assert ratings[0].score == 5
    assert ratings[0].to_user_id == "helper"


def test_credit_recalculation_defaults_to_full_score_without_history(db_session) -> None:
    add_user(db_session, "new_user")

    profile = recalculate_user_credit(db_session, "new_user")

    user = db_session.get(User, "new_user")
    snapshots = db_session.query(CreditSnapshot).filter_by(user_id="new_user").all()
    assert profile == {
        "requesterCreditScore": 100.0,
        "helperCreditScore": 100.0,
        "overallCreditScore": 100.0,
    }
    assert float(user.requester_credit_score) == 100.0
    assert float(user.helper_credit_score) == 100.0
    assert float(user.overall_credit_score) == 100.0
    assert sorted(snapshot.role_scope for snapshot in snapshots) == ["helper", "requester"]
    assert all(float(snapshot.calculated_score) == 100.0 for snapshot in snapshots)


def test_credit_recalculation_reads_weights_from_system_configs(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    completed = create_task(db_session, "requester", task_payload())
    accept_task(db_session, completed.id, "helper")
    submit_task_proof(db_session, completed.id, "helper", proof_payload())
    confirm_task(db_session, completed.id, "requester")
    abandoned_task(db_session, "requester", "helper")
    set_credit_weights(
        db_session,
        {
            "helper": {
                "completion_rate": "1.00",
                "average_rating": "0.00",
                "timeout_rate": "0.00",
                "abandon_rate": "0.00",
                "dispute_lose_rate": "0.00",
            },
            "overall": {"helper": "1.00", "requester": "0.00"},
        },
    )

    profile = recalculate_user_credit(db_session, "helper")

    assert profile["helperCreditScore"] == 50.0
    assert profile["requesterCreditScore"] == 100.0
    assert profile["overallCreditScore"] == 50.0


def test_credit_weights_fallback_to_defaults_when_config_is_invalid(db_session) -> None:
    add_user(db_session, "new_user")
    set_credit_weights(
        db_session,
        {
            "helper": {"completion_rate": "not-a-number"},
            "requester": "bad-shape",
            "overall": {"helper": "-1.00", "requester": "bad"},
        },
    )

    profile = recalculate_user_credit(db_session, "new_user")

    assert profile == {
        "requesterCreditScore": 100.0,
        "helperCreditScore": 100.0,
        "overallCreditScore": 100.0,
    }


def test_credit_recalculation_updates_user_scores_and_snapshots_from_history(db_session) -> None:
    add_user(db_session, "requester", "200.00")
    add_user(db_session, "helper", "0.00")
    add_user(db_session, "admin")
    completed = create_task(db_session, "requester", task_payload())
    accept_task(db_session, completed.id, "helper")
    submit_task_proof(db_session, completed.id, "helper", proof_payload())
    confirm_task(db_session, completed.id, "requester")
    rate_task_partner(db_session, completed.id, "requester", rating_payload(5, "Great"))
    abandoned_task(db_session, "requester", "helper")
    helper_lost_dispute_task(db_session, "requester", "helper")
    requester_lost_dispute_task(db_session, "requester", "helper")

    profile = recalculate_user_credit(db_session, "helper")
    user = db_session.get(User, "helper")
    helper_snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="helper", role_scope="helper")
        .filter(CreditSnapshot.calculated_score == Decimal("76.25"))
        .first()
    )

    assert profile["helperCreditScore"] == 76.25
    assert profile["requesterCreditScore"] == 100.0
    assert profile["overallCreditScore"] == 85.75
    assert float(user.helper_credit_score) == 76.25
    assert float(user.requester_credit_score) == 100.0
    assert float(user.overall_credit_score) == 85.75
    assert float(helper_snapshot.completion_rate) == 50.0
    assert float(helper_snapshot.average_rating) == 100.0
    assert float(helper_snapshot.abandon_rate) == 25.0
    assert float(helper_snapshot.dispute_lose_rate) == 25.0
    assert float(helper_snapshot.calculated_score) == 76.25


def test_requester_credit_recalculation_tracks_malicious_dispute_loss(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    add_user(db_session, "admin")
    task = requester_lost_dispute_task(db_session, "requester", "helper")
    rate_task_partner(db_session, task.id, "helper", rating_payload(4, "ok"))

    profile = recalculate_user_credit(db_session, "requester")
    requester_snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="requester", role_scope="requester")
        .filter(CreditSnapshot.calculated_score == Decimal("80.00"))
        .first()
    )

    assert profile["requesterCreditScore"] == 80.0
    assert profile["helperCreditScore"] == 100.0
    assert profile["overallCreditScore"] == 92.0
    assert float(requester_snapshot.completion_rate) == 100.0
    assert float(requester_snapshot.average_rating) == 80.0
    assert float(requester_snapshot.malicious_dispute_rate) == 100.0
    assert float(requester_snapshot.calculated_score) == 80.0


def test_helper_credit_recalculation_tracks_completion_timeout(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    task = create_task(db_session, "requester", task_payload())
    accept_task(db_session, task.id, "helper")
    task.deadline = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()
    submit_task_proof(db_session, task.id, "helper", proof_payload())
    confirm_task(db_session, task.id, "requester")

    profile = recalculate_user_credit(db_session, "helper")
    helper_snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="helper", role_scope="helper")
        .order_by(CreditSnapshot.calculated_at.desc(), CreditSnapshot.id.desc())
        .first()
    )

    assert profile["helperCreditScore"] == 85.0
    assert helper_snapshot is not None
    assert float(helper_snapshot.timeout_rate) == 100.0


def test_requester_credit_recalculation_tracks_confirmation_timeout(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    task = create_task(db_session, "requester", task_payload())
    accept_task(db_session, task.id, "helper")
    submit_task_proof(db_session, task.id, "helper", proof_payload())
    task.deadline = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()
    confirm_task(db_session, task.id, "requester")

    profile = recalculate_user_credit(db_session, "requester")
    requester_snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="requester", role_scope="requester")
        .order_by(CreditSnapshot.calculated_at.desc(), CreditSnapshot.id.desc())
        .first()
    )

    assert profile["requesterCreditScore"] == 85.0
    assert requester_snapshot is not None
    assert float(requester_snapshot.timeout_rate) == 100.0


def test_requester_credit_recalculation_tracks_post_accept_cancel_refund(db_session) -> None:
    add_user(db_session, "requester", "100.00")
    add_user(db_session, "helper", "0.00")
    task = create_task(db_session, "requester", task_payload())
    accept_task(db_session, task.id, "helper")
    task.status = TaskStatus.CANCELLED
    db_session.add(
        TaskLog(
            id="log_refund_to_requester",
            task_id=task.id,
            from_status=TaskStatus.DISPUTED,
            to_status=TaskStatus.CANCELLED,
            actor_id="requester",
            remark="Requester-triggered refund after acceptance",
        )
    )
    db_session.commit()

    profile = recalculate_user_credit(db_session, "requester")
    requester_snapshot = (
        db_session.query(CreditSnapshot)
        .filter_by(user_id="requester", role_scope="requester")
        .order_by(CreditSnapshot.calculated_at.desc(), CreditSnapshot.id.desc())
        .first()
    )

    assert profile["requesterCreditScore"] == 55.0
    assert requester_snapshot is not None
    assert float(requester_snapshot.post_accept_cancel_rate) == 100.0


def test_credit_scores_are_clamped_between_zero_and_one_hundred(db_session) -> None:
    add_user(db_session, "requester", "500.00")
    add_user(db_session, "helper", "0.00")
    add_user(db_session, "admin")
    completed = create_task(db_session, "requester", task_payload())
    accept_task(db_session, completed.id, "helper")
    submit_task_proof(db_session, completed.id, "helper", proof_payload())
    confirm_task(db_session, completed.id, "requester")
    rate_task_partner(db_session, completed.id, "requester", rating_payload(1, "bad"))
    for _ in range(3):
        abandoned_task(db_session, "requester", "helper")
        helper_lost_dispute_task(db_session, "requester", "helper")

    profile = recalculate_user_credit(db_session, "helper")
    snapshots = db_session.query(CreditSnapshot).filter_by(user_id="helper").all()

    assert all(0 <= value <= 100 for value in profile.values())
    assert all(0 <= float(snapshot.calculated_score) <= 100 for snapshot in snapshots)


def test_low_recalculated_helper_credit_is_rejected_for_acceptance(db_session) -> None:
    add_user(db_session, "requester", "500.00")
    add_user(db_session, "helper", "0.00")
    add_user(db_session, "admin")
    completed = create_task(db_session, "requester", task_payload())
    accept_task(db_session, completed.id, "helper")
    submit_task_proof(db_session, completed.id, "helper", proof_payload())
    confirm_task(db_session, completed.id, "requester")
    rate_task_partner(db_session, completed.id, "requester", rating_payload(1, "bad"))
    for _ in range(2):
        abandoned_task(db_session, "requester", "helper")
        helper_lost_dispute_task(db_session, "requester", "helper")
    recalculate_user_credit(db_session, "helper")

    next_task = create_task(db_session, "requester", task_payload())
    with pytest.raises(TaskError) as exc:
        accept_task(db_session, next_task.id, "helper")

    assert exc.value.code == "HELPER_CREDIT_TOO_LOW"
    assert get_credit_profile(db_session, "helper")["helperCreditScore"] < 60
