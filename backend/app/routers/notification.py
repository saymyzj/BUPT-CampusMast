"""
文件说明：
这是通知路由占位文件。
组长后续应在这里继续实现通知分页、单条已读和全部已读接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.notification_service import build_stub_notification
from app.utils.response import success

router = APIRouter(prefix="/notifications", tags=["Notification"])


@router.get("")
def list_notifications() -> dict:
    return success([build_stub_notification()], meta={"page": 1, "limit": 20, "total": 1})


@router.patch("/read-all")
def mark_all_notifications_read() -> dict:
    return success({"updatedCount": 1})

