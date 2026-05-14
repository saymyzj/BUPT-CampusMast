"""
文件说明：
这是后台路由占位文件。
组长后续应在这里继续填充用户管理、任务管理、争议裁决、审核复审和配置管理接口。
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.schemas.admin import AdminResolveDisputeRequest
from app.services.admin_service import build_stub_admin_stats
from app.services.auth_service import build_stub_auth_payload
from app.services.config_service import build_stub_config_item
from app.services.moderation_service import build_stub_moderation_record
from app.services.task_service import (
    TaskError,
    close_dispute_by_admin,
    resolve_dispute_for_helper,
    resolve_dispute_for_requester,
    resolve_dispute_split,
    task_to_dict,
)
from app.utils.response import failure, success

router = APIRouter(prefix="/admin", tags=["Admin"])


def _error_response(exc: TaskError, status_code: int = status.HTTP_409_CONFLICT) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=failure(exc.code, exc.message))


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


@router.patch("/tasks/{task_id}/resolve")
def admin_resolve_dispute(
    task_id: str,
    payload: AdminResolveDisputeRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
) -> dict:
    try:
        if payload.resolution == "refund":
            task = resolve_dispute_for_requester(db, task_id, admin_user["id"], payload.note)
        elif payload.resolution == "settle":
            task = resolve_dispute_for_helper(db, task_id, admin_user["id"], payload.note)
        elif payload.resolution == "split":
            if payload.splitRatio is None:
                raise TaskError("SPLIT_RATIO_REQUIRED", "splitRatio is required when resolution is split")
            task = resolve_dispute_split(db, task_id, admin_user["id"], Decimal(str(payload.splitRatio)), payload.note)
        elif payload.resolution == "close":
            task = close_dispute_by_admin(db, task_id, admin_user["id"], payload.note)
        else:
            raise TaskError("INVALID_DISPUTE_RESOLUTION", "Invalid dispute resolution")
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))
