from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.models.base import Base, SessionLocal, engine
from app.models.enums import Role
from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.utils.ids import generate_id
from app.utils.security import hash_password

ADMIN_ACCOUNT = "Admin"
NORMAL_ACCOUNT = "user01"
DEFAULT_PASSWORD = "12345"


def _set_foreign_key_checks(db: Session, enabled: bool) -> None:
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "mysql":
        db.execute(text(f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"))
    elif dialect == "sqlite":
        db.execute(text(f"PRAGMA foreign_keys = {'ON' if enabled else 'OFF'}"))


def _clear_application_tables(db: Session) -> None:
    _set_foreign_key_checks(db, False)
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    finally:
        _set_foreign_key_checks(db, True)


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

    db.add(UserProfile(user_id=user.id))
    db.add(Wallet(id=generate_id("wallet"), user_id=user.id, available=Decimal("200.00"), frozen=Decimal("0.00")))
    return user


def reset_database() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _clear_application_tables(db)
        _create_user(db, account=ADMIN_ACCOUNT, nickname="Admin", role=Role.ADMIN)
        _create_user(db, account=NORMAL_ACCOUNT, nickname="user01", role=Role.USER)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    reset_database()
    print("Database reset complete.")
    print(f"Admin account: {ADMIN_ACCOUNT} / {DEFAULT_PASSWORD}")
    print(f"User account: {NORMAL_ACCOUNT} / {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
