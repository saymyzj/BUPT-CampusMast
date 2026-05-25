from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.config import settings


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return config


def _table_names(database_url: str) -> set[str]:
    engine = sa.create_engine(database_url)
    try:
        return set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _column_names(database_url: str, table_name: str) -> set[str]:
    engine = sa.create_engine(database_url)
    try:
        return {column["name"] for column in sa.inspect(engine).get_columns(table_name)}
    finally:
        engine.dispose()


def _create_legacy_000001_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            INSERT INTO alembic_version(version_num) VALUES ('20260415_000001');

            CREATE TABLE users (
                id VARCHAR(25) NOT NULL PRIMARY KEY,
                student_email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                nickname VARCHAR(50) NOT NULL
            );

            CREATE TABLE tasks (
                id VARCHAR(25) NOT NULL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                reward NUMERIC(10, 2) NOT NULL,
                deadline DATETIME NOT NULL,
                requester_id VARCHAR(25) NOT NULL
            );

            CREATE TABLE wallets (
                id VARCHAR(25) NOT NULL PRIMARY KEY,
                user_id VARCHAR(25) NOT NULL UNIQUE,
                available NUMERIC(10, 2) NOT NULL
            );

            CREATE TABLE transactions (
                id VARCHAR(25) NOT NULL PRIMARY KEY,
                wallet_id VARCHAR(25) NOT NULL,
                type VARCHAR(20) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                balance_after NUMERIC(10, 2) NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def test_alembic_upgrade_head_creates_current_schema_from_empty_database(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty.sqlite3'}"
    monkeypatch.setattr(settings, "database_url", database_url)

    command.upgrade(_alembic_config(), "head")

    tables = _table_names(database_url)
    assert {
        "users",
        "tasks",
        "wallets",
        "transactions",
        "notifications",
        "chat_conversations",
        "chat_messages",
        "ratings",
        "recommendation_snapshots",
        "moderation_records",
    }.issubset(tables)
    assert {"latitude", "longitude", "location_detail", "image_urls"}.issubset(_column_names(database_url, "tasks"))


def test_alembic_upgrade_head_backfills_legacy_000001_schema(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    _create_legacy_000001_database(database_path)
    database_url = f"sqlite+pysqlite:///{database_path}"
    monkeypatch.setattr(settings, "database_url", database_url)

    command.upgrade(_alembic_config(), "head")

    tables = _table_names(database_url)
    assert {"notifications", "chat_conversations", "ratings", "recommendation_snapshots"}.issubset(tables)
    assert {"role", "requester_credit_score", "helper_credit_score", "overall_credit_score", "is_active"}.issubset(
        _column_names(database_url, "users")
    )
    assert {
        "category",
        "status",
        "building_code",
        "latitude",
        "longitude",
        "location_detail",
        "image_urls",
        "moderation_result",
        "needs_admin_review",
        "version",
    }.issubset(_column_names(database_url, "tasks"))
    assert {"frozen", "updated_at"}.issubset(_column_names(database_url, "wallets"))
    assert {"related_task_id", "settlement_key", "description", "created_at"}.issubset(
        _column_names(database_url, "transactions")
    )
