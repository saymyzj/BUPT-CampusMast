"""
文件说明：
这是 WebSocket 网关占位文件。
当前提供最小连接能力，后续组长应在这里补充鉴权、房间管理、事件分发和 Redis 广播。
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "event": "SYSTEM_NOTICE",
            "channel": channel,
            "message": "WebSocket 脚手架已连接，后续可在此继续接入通知与聊天逻辑。",
        }
    )
    try:
        while True:
            payload = await websocket.receive_text()
            await websocket.send_text(payload)
    except WebSocketDisconnect:
        return

