from __future__ import annotations

import asyncio
import contextlib
import json
from collections import defaultdict
from uuid import uuid4
from typing import Any

from fastapi import WebSocket
from redis import asyncio as redis_async
from redis.exceptions import RedisError

from app.config import settings

PROCESS_ID = uuid4().hex
REDIS_CHANNEL_PREFIX = "campusmast:ws:"
REDIS_CHANNEL_PATTERN = f"{REDIS_CHANNEL_PREFIX}*"


class ConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._channels[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        sockets = self._channels.get(channel)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._channels.pop(channel, None)

    async def broadcast(self, channel: str, event: str, payload: dict[str, Any]) -> None:
        message = {"event": event, "channel": channel, "payload": payload}
        await self.deliver(message)
        await publish_realtime_message(message)

    async def deliver(self, message: dict[str, Any]) -> None:
        channel = str(message.get("channel") or "")
        sockets = list(self._channels.get(channel, set()))
        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(message)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(channel, socket)

    def snapshot(self) -> dict[str, Any]:
        channels = [
            {"channel": channel, "connections": len(sockets)}
            for channel, sockets in sorted(self._channels.items())
        ]
        return {
            "processId": PROCESS_ID,
            "totalConnections": sum(item["connections"] for item in channels),
            "channels": channels,
            "redisEnabled": bool(settings.redis_url),
        }


manager = ConnectionManager()

_redis_listener_task: asyncio.Task[None] | None = None
_redis_publish_client: redis_async.Redis | None = None


async def _publish_client() -> redis_async.Redis:
    global _redis_publish_client
    if _redis_publish_client is None:
        _redis_publish_client = redis_async.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_publish_client


async def publish_realtime_message(message: dict[str, Any]) -> None:
    try:
        client = await _publish_client()
        envelope = json.dumps({"source": PROCESS_ID, "message": message}, ensure_ascii=False)
        await client.publish(f"{REDIS_CHANNEL_PREFIX}{message['channel']}", envelope)
    except (RedisError, OSError, ValueError):
        # Redis is part of the full architecture, but local demo should still
        # work if Redis is temporarily unavailable. Local delivery already ran.
        return


async def start_realtime_listener() -> None:
    global _redis_listener_task
    if _redis_listener_task is not None and not _redis_listener_task.done():
        return
    _redis_listener_task = asyncio.create_task(_redis_listener_loop())


async def stop_realtime_listener() -> None:
    global _redis_listener_task, _redis_publish_client
    if _redis_listener_task is not None:
        _redis_listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _redis_listener_task
        _redis_listener_task = None
    if _redis_publish_client is not None:
        await _redis_publish_client.aclose()
        _redis_publish_client = None


async def _redis_listener_loop() -> None:
    while True:
        client: redis_async.Redis | None = None
        pubsub = None
        try:
            client = redis_async.Redis.from_url(settings.redis_url, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.psubscribe(REDIS_CHANNEL_PATTERN)
            async for raw in pubsub.listen():
                if raw.get("type") != "pmessage":
                    continue
                try:
                    envelope = json.loads(raw.get("data") or "{}")
                    if envelope.get("source") == PROCESS_ID:
                        continue
                    message = envelope.get("message")
                    if isinstance(message, dict):
                        await manager.deliver(message)
                except (TypeError, ValueError):
                    continue
        except asyncio.CancelledError:
            raise
        except (RedisError, OSError):
            await asyncio.sleep(2)
        finally:
            if pubsub is not None:
                with contextlib.suppress(Exception):
                    await pubsub.aclose()
            if client is not None:
                with contextlib.suppress(Exception):
                    await client.aclose()
