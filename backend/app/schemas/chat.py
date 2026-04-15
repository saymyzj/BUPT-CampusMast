"""
文件说明：
这是聊天模块的 Schema 文件。
用于统一会话列表、消息列表、已读同步和 HTTP 兜底发送消息结构。
"""
from __future__ import annotations

from pydantic import BaseModel


class ChatMessageCreateRequest(BaseModel):
    clientMessageId: str | None = None
    content: str


class ChatReadRequest(BaseModel):
    lastReadMessageId: str | None = None


class ChatMessageResponse(BaseModel):
    id: str
    conversationId: str
    taskId: str
    senderId: str
    content: str
    createdAt: str


class ChatConversationResponse(BaseModel):
    id: str
    taskId: str
    unreadCount: int
    latestMessage: ChatMessageResponse | None = None
