from __future__ import annotations

from app.bootstrap import ensure_seed_data
from app.models.base import Base, SessionLocal, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_seed_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
