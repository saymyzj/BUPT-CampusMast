from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.models import *  # noqa: F403
from app.models.base import Base
from app.models.enums import TaskStatus
from app.models.task import Task
from app.models.user import User
from app.models.wallet import Wallet
from app.services.task_service import accept_task, cancel_task, confirm_task, create_task, submit_task_proof

MYSQL_TEST_URL = os.getenv("CAMPUSMAST_MYSQL_TEST_URL")

pytestmark = pytest.mark.skipif(
    not MYSQL_TEST_URL,
    reason="Set CAMPUSMAST_MYSQL_TEST_URL to run real MySQL concurrency integration tests.",
)


def _reset_mysql_schema(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            for table_name in inspect(connection).get_table_names():
                connection.execute(text(f"DROP TABLE `{table_name}`"))
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    finally:
        engine.dispose()


def _create_schema(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    try:
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()


@pytest.fixture
def mysql_session_factory():
    engine = create_engine(MYSQL_TEST_URL, future=True, isolation_level="READ COMMITTED")
    engine.dispose()
    _reset_mysql_schema(MYSQL_TEST_URL)
    _create_schema(MYSQL_TEST_URL)
    engine = create_engine(MYSQL_TEST_URL, future=True, isolation_level="READ COMMITTED")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    try:
        yield SessionLocal
    finally:
        engine.dispose()
        _reset_mysql_schema(MYSQL_TEST_URL)


def test_mysql_model_schema_creates_frozen_constraints_and_indexes(mysql_session_factory) -> None:
    engine = mysql_session_factory.kw["bind"]
    inspector = inspect(engine)

    rating_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("ratings")
    }
    transaction_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("transactions")
    }
    task_indexes = {index["name"] for index in inspector.get_indexes("tasks")}
    transaction_indexes = {index["name"] for index in inspector.get_indexes("transactions")}
    recommendation_indexes = {index["name"] for index in inspector.get_indexes("recommendation_snapshots")}

    assert "uq_ratings_task_id_from_user_id" in rating_constraints
    assert "uq_transactions_settlement_key" in transaction_constraints
    assert "ix_tasks_status_created_at" in task_indexes
    assert "ix_tasks_building_code_status" in task_indexes
    assert "ix_transactions_wallet_id_created_at" in transaction_indexes
    assert "ix_recommendation_snapshots_user_id_snapshot_date" in recommendation_indexes


def add_user(session, user_id: str, *, available: str = "0.00") -> None:
    session.add(
        User(
            id=user_id,
            student_email=f"{user_id}@bupt.edu.cn",
            password_hash="hash",
            nickname=user_id,
        )
    )
    session.add(
        Wallet(
            id=f"wallet_{user_id}",
            user_id=user_id,
            available=Decimal(available),
            frozen=Decimal("0.00"),
        )
    )
    session.commit()


def task_payload(reward: str = "20.00") -> SimpleNamespace:
    return SimpleNamespace(
        title="MySQL concurrency task",
        description="Task for real MySQL integration testing.",
        category="package",
        reward=reward,
        deadline=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        buildingCode="BUPT_MAIN",
        locationDetail="Gate",
        imageUrls=[],
    )


def setup_accept_case(SessionLocal) -> str:
    session = SessionLocal()
    try:
        add_user(session, "requester", available="100.00")
        add_user(session, "helper_a")
        add_user(session, "helper_b")
        task = create_task(session, "requester", task_payload("20.00"))
        return task.id
    finally:
        session.close()


def test_mysql_concurrent_accept_allows_only_one_helper(mysql_session_factory) -> None:
    task_id = setup_accept_case(mysql_session_factory)

    def try_accept(helper_id: str) -> str:
        session = mysql_session_factory()
        try:
            accept_task(session, task_id, helper_id)
            return "ok"
        except Exception:
            return "rejected"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(try_accept, ["helper_a", "helper_b"]))

    verify = mysql_session_factory()
    try:
        stored = verify.get(Task, task_id)
        assert results.count("ok") == 1
        assert results.count("rejected") == 1
        assert stored.status == TaskStatus.IN_PROGRESS
        assert stored.helper_id in {"helper_a", "helper_b"}
    finally:
        verify.close()


def test_mysql_duplicate_confirm_settles_once(mysql_session_factory) -> None:
    session = mysql_session_factory()
    try:
        add_user(session, "requester", available="100.00")
        add_user(session, "helper")
        task = create_task(session, "requester", task_payload("20.00"))
        accept_task(session, task.id, "helper")
        submit_task_proof(
            session,
            task.id,
            "helper",
            SimpleNamespace(proofNote="done", proofImageUrls=[]),
        )
        task_id = task.id
    finally:
        session.close()

    def try_confirm() -> str:
        local = mysql_session_factory()
        try:
            confirm_task(local, task_id, "requester")
            return "ok"
        except Exception:
            return "rejected"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _i: try_confirm(), range(2)))

    verify = mysql_session_factory()
    try:
        helper_wallet = verify.query(Wallet).filter_by(user_id="helper").one()
        assert results.count("ok") == 1
        assert results.count("rejected") == 1
        assert Decimal(str(helper_wallet.available)) == Decimal("20.00")
    finally:
        verify.close()


def test_mysql_cancel_and_accept_race_has_single_terminal_outcome(mysql_session_factory) -> None:
    task_id = setup_accept_case(mysql_session_factory)

    def try_cancel() -> str:
        session = mysql_session_factory()
        try:
            cancel_task(session, task_id, "requester")
            return "cancelled"
        except Exception:
            return "rejected"
        finally:
            session.close()

    def try_accept() -> str:
        session = mysql_session_factory()
        try:
            accept_task(session, task_id, "helper_a")
            return "accepted"
        except Exception:
            return "rejected"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        cancel_future = executor.submit(try_cancel)
        accept_future = executor.submit(try_accept)
        results = [cancel_future.result(), accept_future.result()]

    verify = mysql_session_factory()
    try:
        stored = verify.get(Task, task_id)
        assert sorted(results).count("rejected") == 1
        assert stored.status in {TaskStatus.CANCELLED, TaskStatus.IN_PROGRESS}
    finally:
        verify.close()
