"""
文件说明：
这是聊天服务文件。
负责会话读取、消息持久化、未读更新和 WebSocket 广播。
"""
from __future__ import annotations

from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.task import Task
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.serialization import to_iso8601
from app.websockets.events import CHAT_MESSAGE, CHAT_READ, UNREAD_SYNC
from app.websockets.manager import manager


def list_conversations(db: Session, *, user_id: str) -> list[dict[str, Any]]:
    participant_rows = db.query(ChatParticipant).filter(ChatParticipant.user_id == user_id).all()
    conversations: list[dict[str, Any]] = []
    for participant in participant_rows:
        conversation = db.get(ChatConversation, participant.conversation_id)
        if conversation is None:
            continue
        latest_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        conversations.append(serialize_conversation(conversation, participant, latest_message))
    return conversations


def list_task_messages(db: Session, *, user_id: str, task_id: str, page: int, limit: int) -> tuple[list[dict[str, Any]], int]:
    conversation = _require_conversation_for_task(db, task_id)
    participant = _require_participant(db, conversation.id, user_id)
    query = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation.id)
    total = query.count()
    messages = query.order_by(ChatMessage.created_at.asc()).offset((page - 1) * limit).limit(limit).all()
    return [serialize_message(message, conversation.task_id) for message in messages], total


def create_message(
    db: Session,
    *,
    user_id: str,
    task_id: str,
    content: str,
    client_message_id: str | None = None,
) -> dict[str, Any]:
    conversation = _require_conversation_for_task(db, task_id)
    _require_participant(db, conversation.id, user_id)
    cleaned_content = content.strip()
    if not cleaned_content:
        raise AppError("EMPTY_CHAT_MESSAGE", "消息内容不能为空", status.HTTP_400_BAD_REQUEST)

    message = ChatMessage(
        id=generate_id("msg"),
        conversation_id=conversation.id,
        sender_id=user_id,
        message_type="TEXT",
        content=cleaned_content,
        client_message_id=client_message_id,
    )
    db.add(message)

    participants = db.query(ChatParticipant).filter(ChatParticipant.conversation_id == conversation.id).all()
    for participant in participants:
        if participant.user_id != user_id:
            participant.unread_count += 1
    db.commit()
    db.refresh(message)

    serialized = serialize_message(message, conversation.task_id)
    return serialized


def mark_conversation_read(
    db: Session,
    *,
    user_id: str,
    conversation_id: str,
    last_read_message_id: str | None = None,
) -> dict[str, Any]:
    participant = _require_participant(db, conversation_id, user_id)
    participant.last_read_message_id = last_read_message_id
    participant.unread_count = 0
    db.commit()
    conversation = db.get(ChatConversation, conversation_id)
    if conversation is None:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", status.HTTP_404_NOT_FOUND)
    return {"conversationId": conversation_id, "taskId": conversation.task_id, "lastReadMessageId": last_read_message_id}


async def push_message_events(db: Session, *, task_id: str, message: dict[str, Any]) -> None:
    await manager.broadcast(f"chat:{task_id}", CHAT_MESSAGE, message)
    conversation = _require_conversation_for_task(db, task_id)
    participants = db.query(ChatParticipant).filter(ChatParticipant.conversation_id == conversation.id).all()
    for participant in participants:
        await manager.broadcast(
            f"notification:{participant.user_id}",
            UNREAD_SYNC,
            {"scope": "chat", "unreadCount": participant.unread_count},
        )


async def push_read_event(*, task_id: str, payload: dict[str, Any]) -> None:
    await manager.broadcast(f"chat:{task_id}", CHAT_READ, payload)


def serialize_conversation(
    conversation: ChatConversation,
    participant: ChatParticipant,
    latest_message: ChatMessage | None,
) -> dict[str, Any]:
    return {
        "id": conversation.id,
        "taskId": conversation.task_id,
        "unreadCount": participant.unread_count,
        "latestMessage": serialize_message(latest_message, conversation.task_id) if latest_message else None,
    }


def serialize_message(message: ChatMessage | None, task_id: str) -> dict[str, Any] | None:
    if message is None:
        return None
    return {
        "id": message.id,
        "conversationId": message.conversation_id,
        "taskId": task_id,
        "senderId": message.sender_id,
        "content": message.content,
        "createdAt": to_iso8601(message.created_at),
    }


def _require_conversation_for_task(db: Session, task_id: str) -> ChatConversation:
    conversation = db.query(ChatConversation).filter(ChatConversation.task_id == task_id).one_or_none()
    if conversation is None:
        raise AppError("CONVERSATION_NOT_FOUND", "任务会话不存在", status.HTTP_404_NOT_FOUND)
    return conversation


def _require_participant(db: Session, conversation_id: str, user_id: str) -> ChatParticipant:
    participant = (
        db.query(ChatParticipant)
        .filter(ChatParticipant.conversation_id == conversation_id, ChatParticipant.user_id == user_id)
        .one_or_none()
    )
    if participant is None:
        raise AppError("CHAT_ACCESS_DENIED", "当前用户不在该会话中", status.HTTP_403_FORBIDDEN)
    return participant
