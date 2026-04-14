"""
文件说明：
这是聊天路由占位文件。
组长后续应在这里维护聊天会话、聊天消息和已读同步的 HTTP 兜底接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.chat_service import build_stub_message
from app.utils.response import success

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations")
def list_conversations() -> dict:
    return success([{"id": "conv_stub", "taskId": "task_stub", "unreadCount": 1, "latestMessage": build_stub_message()}])

