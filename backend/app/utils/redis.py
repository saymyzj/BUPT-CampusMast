"""
文件说明：
这是 Redis 客户端工厂文件。
通知未读、聊天未读、在线状态和推荐缓存都通过这里统一获取 Redis 连接。
"""
from __future__ import annotations

import redis

from app.config import settings


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)
