"""
文件说明：
这是后台路由占位文件。
组长后续应在这里继续填充用户管理、任务管理、争议裁决、审核复审和配置管理接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.admin_service import build_stub_admin_stats
from app.services.auth_service import build_stub_auth_payload
from app.services.config_service import build_stub_config_item
from app.services.moderation_service import build_stub_moderation_record
from app.utils.response import success

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def admin_list_users() -> dict:
    return success([build_stub_auth_payload()["user"]], meta={"page": 1, "limit": 20, "total": 1})


@router.get("/moderation/records")
def admin_list_moderation_records() -> dict:
    return success([build_stub_moderation_record()], meta={"page": 1, "limit": 20, "total": 1})


@router.get("/configs")
def admin_list_configs() -> dict:
    return success([build_stub_config_item()])


@router.get("/stats")
def admin_get_stats() -> dict:
    return success(build_stub_admin_stats())

