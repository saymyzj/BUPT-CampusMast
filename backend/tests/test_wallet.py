from __future__ import annotations

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
from app.models.user import User
from app.models.wallet import Transaction, Wallet
from app.routers.wallet import router as wallet_router
import app.services.wallet_service as wallet_service
from app.services.wallet_service import (
    WalletError,
    freeze_funds,
    list_transactions,
    settle_reward,
    settle_split,
    top_up,
    unfreeze_funds,
    wallet_to_dict,
    withdraw,
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


def add_user_with_wallet(db_session, user_id: str, available: str = "0.00", frozen: str = "0.00") -> None:
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
            frozen=Decimal(frozen),
        )
    )
    db_session.commit()


@pytest.fixture
def wallet_api_client(db_session):
    app = FastAPI()
    app.include_router(wallet_router)
    current_user = SimpleNamespace(id="user", role="USER", nickname="user")

    def override_db():
        yield db_session

    def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client, current_user


def test_wallet_freeze_unfreeze_and_transactions_are_consistent(db_session) -> None:
    add_user_with_wallet(db_session, "requester", "100.00")

    freeze_funds(db_session, "requester", "25.00", related_task_id="task_1")
    db_session.commit()
    wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    assert wallet_to_dict(wallet) == {"available": "75.00", "frozen": "25.00", "total": "100.00"}

    unfreeze_funds(db_session, "requester", "25.00", related_task_id="task_1")
    db_session.commit()
    assert wallet_to_dict(wallet) == {"available": "100.00", "frozen": "0.00", "total": "100.00"}
    rows = db_session.query(Transaction).order_by(Transaction.created_at).all()
    assert [row.type.value for row in rows] == ["FREEZE", "UNFREEZE"]
    assert [row.related_task_id for row in rows] == ["task_1", "task_1"]
    assert [row.description for row in rows] == ["Task reward frozen", "Task reward unfrozen"]


def test_wallet_settlement_moves_frozen_reward_to_helper(db_session) -> None:
    add_user_with_wallet(db_session, "requester", "70.00", "30.00")
    add_user_with_wallet(db_session, "helper", "5.00")

    settle_reward(db_session, "requester", "helper", "30.00", related_task_id="task_1")
    db_session.commit()

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    assert wallet_to_dict(requester_wallet) == {"available": "70.00", "frozen": "0.00", "total": "70.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "35.00", "frozen": "0.00", "total": "35.00"}
    assert [row.type.value for row in db_session.query(Transaction).order_by(Transaction.id).all()] == [
        "SETTLE_IN",
        "SETTLE_OUT",
    ] or sorted(row.type.value for row in db_session.query(Transaction).all()) == ["SETTLE_IN", "SETTLE_OUT"]


def test_wallet_rejects_duplicate_task_settlement(db_session) -> None:
    add_user_with_wallet(db_session, "requester", "70.00", "30.00")
    add_user_with_wallet(db_session, "helper", "5.00")
    settle_reward(db_session, "requester", "helper", "30.00", related_task_id="task_1")
    db_session.commit()

    with pytest.raises(WalletError) as exc:
        settle_reward(db_session, "requester", "helper", "30.00", related_task_id="task_1")

    assert exc.value.code == "DUPLICATE_TASK_SETTLEMENT"


def test_wallet_maps_database_settlement_key_conflict_to_duplicate_error(db_session, monkeypatch) -> None:
    add_user_with_wallet(db_session, "requester", "70.00", "60.00")
    add_user_with_wallet(db_session, "helper", "5.00")
    settle_reward(db_session, "requester", "helper", "30.00", related_task_id="task_1")
    db_session.commit()
    monkeypatch.setattr(wallet_service, "_ensure_no_task_settlement", lambda *_args, **_kwargs: None)

    with pytest.raises(WalletError) as exc:
        settle_split(db_session, "requester", "helper", "30.00", helper_ratio="0.50", related_task_id="task_1")

    assert exc.value.code == "DUPLICATE_TASK_SETTLEMENT"
    rows = db_session.query(Transaction).filter_by(related_task_id="task_1").all()
    assert sorted(row.type.value for row in rows) == ["SETTLE_IN", "SETTLE_OUT"]


def test_wallet_settlement_locks_helper_wallet_for_incoming_balance(db_session, monkeypatch) -> None:
    add_user_with_wallet(db_session, "requester", "70.00", "30.00")
    add_user_with_wallet(db_session, "helper", "5.00")
    calls: list[tuple[str, bool]] = []
    original = wallet_service.get_or_create_wallet

    def wrapped_get_or_create(db, user_id, *, for_update=False):
        calls.append((user_id, for_update))
        return original(db, user_id, for_update=for_update)

    monkeypatch.setattr(wallet_service, "get_or_create_wallet", wrapped_get_or_create)

    settle_reward(db_session, "requester", "helper", "30.00", related_task_id="task_1")

    assert ("helper", True) in calls


def test_wallet_split_settlement_audits_both_wallets(db_session) -> None:
    add_user_with_wallet(db_session, "requester", "80.00", "20.00")
    add_user_with_wallet(db_session, "helper", "5.00")

    settle_split(db_session, "requester", "helper", "20.00", helper_ratio="0.25", related_task_id="task_1")
    db_session.commit()

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    rows = db_session.query(Transaction).order_by(Transaction.wallet_id).all()
    assert wallet_to_dict(requester_wallet) == {"available": "95.00", "frozen": "0.00", "total": "95.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "10.00", "frozen": "0.00", "total": "10.00"}
    assert sorted(row.type.value for row in rows) == ["SETTLE_SPLIT", "SETTLE_SPLIT"]
    assert {row.related_task_id for row in rows} == {"task_1"}
    assert sorted(str(row.amount) for row in rows) == ["15.00", "5.00"]
    assert sum(Decimal(str(row.amount)) for row in rows) == Decimal("20.00")
    assert {
        row.description for row in rows
    } == {
        "Task reward split: frozen consumed 20.00, requester refund 15.00",
        "Task reward split: helper payout 5.00",
    }
    assert [row.settlement_key for row in rows].count("task_1") == 1


def test_wallet_rejects_negative_balances(db_session) -> None:
    add_user_with_wallet(db_session, "requester", "10.00")

    with pytest.raises(WalletError):
        freeze_funds(db_session, "requester", "10.01", related_task_id="task_1")

    db_session.rollback()
    with pytest.raises(WalletError):
        withdraw(db_session, "requester", "10.01")


def test_top_up_and_withdraw_public_operations_commit(db_session) -> None:
    add_user_with_wallet(db_session, "user", "0.00")

    top_up(db_session, "user", "80.00")
    withdraw(db_session, "user", "30.00")

    wallet = db_session.query(Wallet).filter_by(user_id="user").one()
    assert wallet_to_dict(wallet) == {"available": "50.00", "frozen": "0.00", "total": "50.00"}


@pytest.mark.parametrize("amount", ["0.00", "-1.00"])
def test_wallet_rejects_non_positive_amounts(db_session, amount: str) -> None:
    add_user_with_wallet(db_session, "user", "100.00")

    with pytest.raises(WalletError) as exc:
        top_up(db_session, "user", amount)

    assert exc.value.code == "INVALID_AMOUNT"


def test_wallet_rejects_amounts_with_more_than_two_decimal_places(db_session) -> None:
    add_user_with_wallet(db_session, "user", "100.00")

    with pytest.raises(WalletError) as exc:
        top_up(db_session, "user", "1.001")

    assert exc.value.code == "INVALID_AMOUNT_PRECISION"


def test_wallet_rejects_float_amounts(db_session) -> None:
    add_user_with_wallet(db_session, "user", "100.00")

    with pytest.raises(WalletError) as exc:
        top_up(db_session, "user", 1.1)

    assert exc.value.code == "INVALID_AMOUNT"


def test_wallet_outputs_money_with_two_decimal_places(db_session) -> None:
    add_user_with_wallet(db_session, "user", "1", "2")

    assert wallet_to_dict(db_session.query(Wallet).filter_by(user_id="user").one()) == {
        "available": "1.00",
        "frozen": "2.00",
        "total": "3.00",
    }


def test_wallet_transaction_list_is_paginated(db_session) -> None:
    add_user_with_wallet(db_session, "user", "100.00")
    top_up(db_session, "user", "1.00")
    top_up(db_session, "user", "2.00")
    top_up(db_session, "user", "3.00")

    rows, total = list_transactions(db_session, "user", page=2, limit=2)

    assert total == 3
    assert len(rows) == 1
    assert rows[0]["amount"] in {"1.00", "2.00", "3.00"}


def test_wallet_api_returns_error_response_with_code(wallet_api_client, db_session) -> None:
    client, _current_user = wallet_api_client
    add_user_with_wallet(db_session, "user", "5.00")

    response = client.post("/wallet/withdraw", json={"amount": "6.00"})

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "error": {
            "code": "INSUFFICIENT_AVAILABLE_BALANCE",
            "message": "Insufficient available balance",
            "details": None,
        },
    }


def test_wallet_api_rejects_invalid_amount_precision(wallet_api_client, db_session) -> None:
    client, _current_user = wallet_api_client
    add_user_with_wallet(db_session, "user", "5.00")

    response = client.post("/wallet/topup", json={"amount": "1.001"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_AMOUNT_PRECISION"
