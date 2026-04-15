"""
文件说明：
这是聊天路由文件。
负责会话列表、任务消息列表、HTTP 兜底发消息和已读同步接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageCreateRequest, ChatReadRequest
from app.services.chat_service import (
    create_message,
    list_conversations as list_conversations_service,
    list_task_messages,
    mark_conversation_read,
    push_message_events,
    push_read_event,
)
from app.utils.response import success

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return success(list_conversations_service(db, user_id=user.id))


@router.get("/tasks/{task_id}/messages")
def get_task_messages(
    task_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = list_task_messages(db, user_id=user.id, task_id=task_id, page=page, limit=limit)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.post("/tasks/{task_id}/messages", status_code=201)
async def send_task_message(
    task_id: str,
    payload: ChatMessageCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    message = create_message(db, user_id=user.id, task_id=task_id, content=payload.content, client_message_id=payload.clientMessageId)
    await push_message_events(db, task_id=task_id, message=message)
    return success(message)


@router.patch("/conversations/{id}/read")
async def mark_read(
    id: str,
    payload: ChatReadRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = mark_conversation_read(db, user_id=user.id, conversation_id=id, last_read_message_id=payload.lastReadMessageId)
    await push_read_event(task_id=result["taskId"], payload=result)
    return success(result)
