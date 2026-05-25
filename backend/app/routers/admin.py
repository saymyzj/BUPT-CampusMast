"""
文件说明：
这是后台路由文件。
负责用户管理、任务管理、审核复审、系统配置与首页配置接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import require_admin
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.admin import AdminResolveDisputeRequest, AdminReviewModerationRequest, AdminUpdateUserRequest
from app.schemas.config import ConfigUpdateRequest, HomepageBlockUpsertRequest
from app.services.admin_service import build_admin_stats, list_tasks, list_users, resolve_dispute, update_user
from app.services.config_service import list_configs, list_homepage_blocks, update_config, upsert_homepage_block
from app.services.moderation_service import list_moderation_records, review_moderation_record
from app.utils.response import success
from app.websockets.manager import manager

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def admin_list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = list_users(db, page=page, limit=limit, keyword=keyword)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.patch("/users/{id}")
def admin_update_user(
    id: str,
    payload: AdminUpdateUserRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return success(update_user(db, user_id=id, payload=payload))


@router.get("/tasks")
def admin_list_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    needsAdminReview: bool | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = list_tasks(db, page=page, limit=limit, status_filter=status, needs_admin_review=needsAdminReview)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.patch("/tasks/{id}/resolve")
def admin_resolve_dispute(
    id: str,
    payload: AdminResolveDisputeRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return success(resolve_dispute(db, task_id=id, payload=payload, admin_id=admin.id))


@router.get("/moderation/records")
def admin_list_moderation_records(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    riskLevel: str | None = None,
    adminReviewStatus: str | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = list_moderation_records(
        db,
        page=page,
        limit=limit,
        risk_level=riskLevel,
        admin_review_status=adminReviewStatus,
    )
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.patch("/moderation/records/{id}/review")
def admin_review_moderation_record(
    id: str,
    payload: AdminReviewModerationRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return success(review_moderation_record(db, record_id=id, payload=payload, admin_id=admin.id))


@router.get("/configs")
def admin_list_configs(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return success(list_configs(db))


@router.put("/configs/{key}")
def admin_update_config(
    key: str,
    payload: ConfigUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return success(update_config(db, key=key, payload=payload, admin_id=admin.id))


@router.get("/homepage/blocks")
def admin_list_homepage_blocks(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return success(list_homepage_blocks(db))


@router.put("/homepage/blocks/{id}")
def admin_update_homepage_block(
    id: str,
    payload: HomepageBlockUpsertRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return success(upsert_homepage_block(db, block_id=id, payload=payload, admin_id=admin.id))


@router.get("/stats")
def admin_get_stats(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return success(build_admin_stats(db))


@router.get("/ws/connections")
def admin_get_ws_connections(_: User = Depends(require_admin)) -> dict:
    return success(manager.snapshot())
