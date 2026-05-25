from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.models.base import Base, SessionLocal, engine
from app.models.enums import Role
from app.osm_buildings import seed_default_buildings
from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.utils.ids import generate_id
from app.utils.security import hash_password

DEFAULT_PASSWORD = "12345"
ADMIN_ACCOUNT = "admin"
USER_COUNT = 10


def _drop_and_create_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _create_user(db: Session, *, account: str, nickname: str, role: Role) -> User:
    user = User(
        id=generate_id("u"),
        student_email=account,
        password_hash=hash_password(DEFAULT_PASSWORD),
        nickname=nickname,
        role=role,
        requester_credit_score=Decimal("100.00"),
        helper_credit_score=Decimal("100.00"),
        overall_credit_score=Decimal("100.00"),
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            default_building_code="BUPT_MAIN",
            preferred_categories='["package", "food", "move", "other"]',
            active_time_slots="[9, 12, 18, 20]",
            helper_success_rate=Decimal("100.00"),
        )
    )
    db.add(
        Wallet(
            id=generate_id("wallet"),
            user_id=user.id,
            available=Decimal("200.00"),
            frozen=Decimal("0.00"),
        )
    )
    return user


def initialize_database(*, user_count: int = USER_COUNT) -> None:
    _drop_and_create_schema()
    db = SessionLocal()
    try:
        _create_user(db, account=ADMIN_ACCOUNT, nickname="管理员", role=Role.ADMIN)
        for index in range(1, user_count + 1):
            account = f"user{index:02d}"
            _create_user(db, account=account, nickname=f"用户{index:02d}", role=Role.USER)
        db.commit()
        seed_default_buildings(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    initialize_database()
    print("Database initialized.")
    print(f"Admin account: {ADMIN_ACCOUNT} / {DEFAULT_PASSWORD}")
    print(f"User accounts: user01-user{USER_COUNT:02d} / {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
