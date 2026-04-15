"""
文件说明：
这是系统配置与首页内容配置服务文件。
负责统一读取与更新系统配置和首页配置模块。
"""
from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.models.config import HomepageBlock, SystemConfig
from app.schemas.config import HomepageBlockUpsertRequest
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.serialization import json_dumps, json_loads, to_iso8601


def list_configs(db: Session) -> list[dict[str, Any]]:
    rows = db.query(SystemConfig).order_by(SystemConfig.config_group.asc(), SystemConfig.config_key.asc()).all()
    return [serialize_config(row) for row in rows]


def update_config(db: Session, *, key: str, config_value: dict[str, Any], admin_id: str) -> dict[str, Any]:
    row = db.get(SystemConfig, key)
    if row is None:
        raise AppError("CONFIG_NOT_FOUND", "配置项不存在", status.HTTP_404_NOT_FOUND)
    row.config_value = json_dumps(config_value)
    row.updated_by = admin_id
    db.commit()
    db.refresh(row)
    return serialize_config(row)


def list_homepage_blocks(db: Session) -> list[dict[str, Any]]:
    rows = db.query(HomepageBlock).order_by(HomepageBlock.sort_order.asc(), HomepageBlock.updated_at.desc()).all()
    return [serialize_homepage_block(row) for row in rows]


def upsert_homepage_block(
    db: Session,
    *,
    block_id: str,
    payload: HomepageBlockUpsertRequest,
    admin_id: str,
) -> dict[str, Any]:
    row = db.get(HomepageBlock, block_id)
    if row is None:
        row = HomepageBlock(id=block_id or generate_id("home"))
        db.add(row)

    row.block_type = payload.blockType
    row.title = payload.title
    row.content = json_dumps(payload.content)
    row.sort_order = payload.sortOrder
    row.is_active = payload.isActive
    row.updated_by = admin_id
    db.commit()
    db.refresh(row)
    return serialize_homepage_block(row)


def serialize_config(row: SystemConfig) -> dict[str, Any]:
    return {
        "configKey": row.config_key,
        "configGroup": row.config_group,
        "configValue": json_loads(row.config_value, {}),
        "description": row.description,
        "updatedAt": to_iso8601(row.updated_at),
    }


def serialize_homepage_block(row: HomepageBlock) -> dict[str, Any]:
    return {
        "id": row.id,
        "blockType": row.block_type,
        "title": row.title,
        "content": json_loads(row.content, {}),
        "sortOrder": row.sort_order,
        "isActive": row.is_active,
        "updatedAt": to_iso8601(row.updated_at),
    }
