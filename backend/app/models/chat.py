"""
文件说明：
这是任务内 IM 的模型文件。
会话、参与者和消息的最小结构都在这里，后续组长可直接扩展为生产级聊天模型。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(25), ForeignKey("tasks.id"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(25), ForeignKey("chat_conversations.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    unread_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_read_message_id: Mapped[str | None] = mapped_column(String(25))
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(25), ForeignKey("chat_conversations.id"), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="TEXT", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

