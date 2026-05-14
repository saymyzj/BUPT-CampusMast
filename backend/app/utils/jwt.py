"""
文件说明：
这是 JWT 工具文件。
当前只保留最小生成逻辑占位，组长后续可以在此补充 accessToken 与 refreshToken 的
负载结构和校验细节。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings


def create_token(subject: str, expires_in_minutes: int) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

