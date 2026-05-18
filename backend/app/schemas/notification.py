"""
文件说明：
这是通知模块的 Schema 文件。
站内通知列表查询、已读操作和未读数展示都应以这里的结构为准。
"""
from __future__ import annotations

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str
    relatedTaskId: str | None = None
    isRead: bool
    createdAt: str


class NotificationUnreadResponse(BaseModel):
    unreadCount: int
