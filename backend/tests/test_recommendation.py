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
from app.models.enums import TaskCategory, TaskStatus
from app.models.map import CampusBuilding
from app.models.recommendation import RecommendationSnapshot
from app.models.task import Task
from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.routers.recommendation import router as recommendation_router
import app.services.recommendation_service as recommendation_service
from app.services.recommendation_service import list_recommended_tasks
from app.services.task_service import create_task


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


@pytest.fixture(autouse=True)
def disable_redis_cache(monkeypatch):
    class UnavailableRedis:
        def get(self, _key: str):
            raise recommendation_service.RedisError("redis disabled for isolated tests")

        def setex(self, _key: str, _ttl: int, _value: str):
            raise recommendation_service.RedisError("redis disabled for isolated tests")

    monkeypatch.setattr(recommendation_service, "get_redis_client", lambda: UnavailableRedis())


def add_user(db_session, user_id: str, available: str = "200.00") -> None:
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


def add_building(db_session, code: str, x: float, y: float) -> None:
    db_session.add(CampusBuilding(code=code, name=code, latitude=x, longitude=y, is_active=True))
    db_session.commit()


def add_profile(
    db_session,
    user_id: str,
    *,
    default_building_code: str | None = None,
    preferred_categories: list[str] | None = None,
    active_hours: list[int] | None = None,
    helper_success_rate: str | None = None,
) -> None:
    db_session.add(
        UserProfile(
            user_id=user_id,
            default_building_code=default_building_code,
            preferred_categories=json.dumps(preferred_categories) if preferred_categories is not None else None,
            active_time_slots=json.dumps(active_hours) if active_hours is not None else None,
            helper_success_rate=Decimal(helper_success_rate) if helper_success_rate is not None else None,
        )
    )
    db_session.commit()


def set_recommendation_weights(db_session, value: dict | str) -> None:
    db_session.merge(
        SystemConfig(
            config_key="recommendation.weights",
            config_group="recommendation",
            config_value=json.dumps(value) if isinstance(value, dict) else value,
            description="Recommendation weights for tests",
        )
    )
    db_session.commit()


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value


def task_payload(
    *,
    category: str = "package",
    building_code: str = "B1",
    deadline_hour: int = 9,
    reward: str = "10.00",
) -> SimpleNamespace:
    deadline = datetime.utcnow().replace(hour=deadline_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return SimpleNamespace(
        title=f"{category}-{building_code}-{deadline_hour}",
        description="Recommendation candidate.",
        category=category,
        reward=reward,
        deadline=deadline.isoformat(),
        buildingCode=building_code,
        locationDetail=building_code,
        imageUrls=[],
    )


def pending_task(db_session, requester_id: str, **kwargs) -> Task:
    return create_task(db_session, requester_id, task_payload(**kwargs))


@pytest.fixture
def recommendation_api_client(db_session):
    app = FastAPI()
    app.include_router(recommendation_router)
    current_user = SimpleNamespace(id="helper", role="USER", nickname="helper")

    def override_db():
        yield db_session

    def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client, current_user


def test_recommendation_sorts_by_explainable_weighted_score(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester_a")
    add_user(db_session, "requester_b")
    add_building(db_session, "B1", 0, 0)
    add_building(db_session, "B2", 1000, 0)
    add_profile(
        db_session,
        "helper",
        default_building_code="B1",
        preferred_categories=["package"],
        active_hours=[9],
        helper_success_rate="80.00",
    )
    best = pending_task(db_session, "requester_a", category="package", building_code="B1", deadline_hour=9)
    weak = pending_task(db_session, "requester_b", category="food", building_code="B2", deadline_hour=21)

    rows = list_recommended_tasks(db_session, "helper")

    assert [row["task"]["id"] for row in rows] == [best.id, weak.id]
    assert rows[0]["scoreTotal"] == 95.0
    assert rows[0]["scoreCategory"] == 25.0
    assert rows[0]["scoreDistance"] == 25.0
    assert rows[0]["scoreSuccessRate"] == 20.0
    assert rows[0]["scoreActiveTime"] == 25.0
    assert rows[0]["recommendation"]["scoreTotal"] == 95.0
    assert rows[0]["recommendation"]["signals"]["distance"] == 25.0
    assert rows[0]["recommendation"]["reason"]
    assert rows[1]["scoreTotal"] == 20.0


def test_recommendation_only_returns_pending_tasks_not_created_by_current_user(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    add_building(db_session, "B1", 0, 0)
    visible = pending_task(db_session, "requester", category="package", building_code="B1")
    own = pending_task(db_session, "helper", category="package", building_code="B1")
    completed = pending_task(db_session, "requester", category="food", building_code="B1")
    completed.status = TaskStatus.COMPLETED
    db_session.commit()

    rows = list_recommended_tasks(db_session, "helper")

    assert [row["task"]["id"] for row in rows] == [visible.id]
    assert own.id not in [row["task"]["id"] for row in rows]
    assert completed.id not in [row["task"]["id"] for row in rows]


def test_recommendation_uses_default_scores_when_profile_data_is_missing(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    task = pending_task(db_session, "requester", category="package", building_code="UNKNOWN", deadline_hour=12)

    rows = list_recommended_tasks(db_session, "helper")

    assert rows[0]["task"]["id"] == task.id
    assert rows[0]["scoreCategory"] == 12.5
    assert rows[0]["scoreDistance"] == 12.5
    assert rows[0]["scoreSuccessRate"] == 25.0
    assert rows[0]["scoreActiveTime"] == 12.5
    assert rows[0]["scoreTotal"] == 62.5


def test_recommendation_writes_snapshots_for_returned_items(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    task = pending_task(db_session, "requester")

    list_recommended_tasks(db_session, "helper")

    snapshot = db_session.query(RecommendationSnapshot).filter_by(user_id="helper", task_id=task.id).one()
    assert float(snapshot.score_total) == 62.5
    assert float(snapshot.score_category) == 12.5
    assert float(snapshot.score_distance) == 12.5
    assert float(snapshot.score_success_rate) == 25.0
    assert float(snapshot.score_active_time) == 12.5


def test_recommendation_weights_allow_partial_invalid_and_non_100_config(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    add_building(db_session, "B1", 0, 0)
    add_profile(
        db_session,
        "helper",
        default_building_code="B1",
        preferred_categories=["package"],
        active_hours=[9],
        helper_success_rate="100.00",
    )
    set_recommendation_weights(
        db_session,
        {
            "category": "10.00",
            "distance": "bad",
            "successRate": "-1.00",
            "activeTime": "5.00",
        },
    )
    pending_task(db_session, "requester", category="package", building_code="B1", deadline_hour=9)

    rows = list_recommended_tasks(db_session, "helper")

    assert rows[0]["scoreCategory"] == 10.0
    assert rows[0]["scoreDistance"] == 25.0
    assert rows[0]["scoreSuccessRate"] == 25.0
    assert rows[0]["scoreActiveTime"] == 5.0
    assert rows[0]["scoreTotal"] == 65.0
    assert set(rows[0]) == {
        "task",
        "scoreTotal",
        "scoreCategory",
        "scoreDistance",
        "scoreSuccessRate",
        "scoreActiveTime",
        "recommendation",
    }


def test_recommendation_weights_use_defaults_when_config_is_bad_shape(db_session) -> None:
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    set_recommendation_weights(db_session, "[]")
    pending_task(db_session, "requester")

    rows = list_recommended_tasks(db_session, "helper")

    assert rows[0]["scoreTotal"] == 62.5
    assert rows[0]["scoreCategory"] == 12.5
    assert rows[0]["scoreDistance"] == 12.5
    assert rows[0]["scoreSuccessRate"] == 25.0
    assert rows[0]["scoreActiveTime"] == 12.5


def test_recommendation_uses_redis_cache_when_available(db_session, monkeypatch) -> None:
    fake_redis = FakeRedis()
    monkeypatch.setattr(recommendation_service, "get_redis_client", lambda: fake_redis)
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    first_task = pending_task(db_session, "requester")

    first_rows = list_recommended_tasks(db_session, "helper")
    first_snapshot_count = db_session.query(RecommendationSnapshot).count()
    second_task = pending_task(db_session, "requester", category="food")
    second_rows = list_recommended_tasks(db_session, "helper")

    assert first_rows == second_rows
    assert first_rows[0]["task"]["id"] == first_task.id
    assert second_task.id not in [row["task"]["id"] for row in second_rows]
    assert db_session.query(RecommendationSnapshot).count() == first_snapshot_count
    assert "recommend:user:helper" in fake_redis.store


def test_recommendation_api_field_contract_does_not_drift(recommendation_api_client, db_session) -> None:
    client, _current_user = recommendation_api_client
    add_user(db_session, "helper")
    add_user(db_session, "requester")
    pending_task(db_session, "requester")

    response = client.get("/recommendations/tasks")

    assert response.status_code == 200
    item = response.json()["data"][0]
    assert set(item) == {
        "task",
        "scoreTotal",
        "scoreCategory",
        "scoreDistance",
        "scoreSuccessRate",
        "scoreActiveTime",
        "recommendation",
    }
    assert set(item["recommendation"]) == {"scoreTotal", "reason", "signals"}
    assert set(item["recommendation"]["signals"]) == {"category", "distance", "successRate", "activeTime"}
    assert set(item["task"]) >= {
        "id",
        "title",
        "description",
        "category",
        "reward",
        "status",
        "buildingCode",
        "locationDetail",
        "requester",
        "helper",
        "moderationResult",
        "needsAdminReview",
        "createdAt",
    }
