from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.models import *  # noqa: F403
from app.models.base import Base
from app.models.enums import Role, TaskStatus
from app.models.notification import Notification
from app.models.user import User
from app.models.wallet import Wallet
from app.routers.admin import router as admin_router
from app.utils.errors import AppError
from app.utils.response import failure
from app.services.task_service import accept_task, create_task, dispute_in_progress_task
from app.services.wallet_service import wallet_to_dict


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


def add_user(db_session, user_id: str, *, role: Role = Role.USER, available: str = "0.00") -> None:
    db_session.add(
        User(
            id=user_id,
            student_email=f"{user_id}@bupt.edu.cn",
            password_hash="hash",
            nickname=user_id,
            role=role,
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


def task_payload(reward: str = "20.00") -> SimpleNamespace:
    return SimpleNamespace(
        title="Disputed task",
        description="Task for dispute resolution.",
        category="package",
        reward=reward,
        deadline=(datetime.utcnow() + timedelta(days=1)).isoformat(),
        buildingCode="BUPT_MAIN",
        locationDetail="Gate",
        imageUrls=[],
    )


def disputed_task(db_session):
    add_user(db_session, "admin", role=Role.ADMIN)
    add_user(db_session, "requester", available="100.00")
    add_user(db_session, "helper", available="5.00")
    task = create_task(db_session, "requester", task_payload("20.00"))
    accept_task(db_session, task.id, "helper")
    dispute_in_progress_task(db_session, task.id, "requester", "service abnormal")
    return task


@pytest.fixture
def admin_client(db_session):
    app = FastAPI()
    app.include_router(admin_router)

    @app.exception_handler(AppError)
    async def handle_app_error(_request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=failure(exc.code, exc.message, exc.details))

    def override_db():
        yield db_session

    def override_admin():
        return SimpleNamespace(id="admin", role="ADMIN", nickname="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_admin] = override_admin
    with TestClient(app) as client:
        yield client


def test_admin_resolve_dispute_settle_endpoint_updates_task_funds_and_notifications(admin_client, db_session) -> None:
    task = disputed_task(db_session)

    response = admin_client.patch(
        f"/admin/tasks/{task.id}/resolve",
        json={"resolution": "settle", "note": "support helper"},
    )

    requester_wallet = db_session.query(Wallet).filter_by(user_id="requester").one()
    helper_wallet = db_session.query(Wallet).filter_by(user_id="helper").one()
    notifications = db_session.query(Notification).filter_by(type="DISPUTE_RESOLVED", related_task_id=task.id).all()
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "COMPLETED"
    assert db_session.get(type(task), task.id).status == TaskStatus.COMPLETED
    assert wallet_to_dict(requester_wallet) == {"available": "80.00", "frozen": "0.00", "total": "80.00"}
    assert wallet_to_dict(helper_wallet) == {"available": "25.00", "frozen": "0.00", "total": "25.00"}
    assert sorted(row.user_id for row in notifications) == ["helper", "requester"]


def test_admin_resolve_dispute_split_requires_ratio(admin_client, db_session) -> None:
    task = disputed_task(db_session)

    response = admin_client.patch(
        f"/admin/tasks/{task.id}/resolve",
        json={"resolution": "split", "note": "missing ratio"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SPLIT_RATIO_REQUIRED"
    assert db_session.get(type(task), task.id).status == TaskStatus.DISPUTED


def test_task_event_writes_notifications(db_session) -> None:
    task = disputed_task(db_session)

    response_task = db_session.get(type(task), task.id)
    notifications = db_session.query(Notification).filter_by(type="TASK_DISPUTED", related_task_id=task.id).all()

    assert response_task.status == TaskStatus.DISPUTED
    assert sorted(row.user_id for row in notifications) == ["helper", "requester"]
    assert {row.title for row in notifications} == {"任务进入争议"}
