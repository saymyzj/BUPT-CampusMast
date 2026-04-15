"""
文件说明：
这是 WebSocket 网关文件。
当前提供最小可联调版本：连接鉴权、频道连接、消息广播和已读同步。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user_for_websocket
from app.models.chat import ChatConversation, ChatParticipant
from app.dependencies.database import get_db
from app.models.user import User
from app.websockets.events import SYSTEM_NOTICE
from app.websockets.manager import manager

router = APIRouter()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str, db: Session = Depends(get_db)) -> None:
    user = get_current_user_for_websocket(websocket, db)
    _assert_channel_access(db, user, channel)
    await manager.connect(channel, websocket)
    await manager.broadcast(
        channel,
        SYSTEM_NOTICE,
        {
            "message": "WebSocket connected",
            "channel": channel,
            "userId": user.id,
        },
    )
    try:
        while True:
            payload = await websocket.receive_json()
            event = payload.get("event", SYSTEM_NOTICE)
            body = payload.get("payload", {})
            await manager.broadcast(channel, event, body)
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)


def _assert_channel_access(db: Session, user: User, channel: str) -> None:
    if channel.startswith("notification:"):
        expected = channel.split(":", 1)[1]
        if expected != user.id:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="无权订阅他人通知通道")
        return

    if channel.startswith("chat:") or channel.startswith("presence:"):
        task_id = channel.split(":", 1)[1]
        conversation = db.query(ChatConversation).filter(ChatConversation.task_id == task_id).one_or_none()
        if conversation is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="任务会话不存在")
        participant = (
            db.query(ChatParticipant)
            .filter(ChatParticipant.conversation_id == conversation.id, ChatParticipant.user_id == user.id)
            .one_or_none()
        )
        if participant is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="当前用户不在会话中")
