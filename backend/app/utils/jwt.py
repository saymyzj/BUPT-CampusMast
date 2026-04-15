"""
文件说明：
这是 JWT 工具文件。
当前只保留最小生成逻辑占位，组长后续可以在此补充 accessToken 与 refreshToken 的
负载结构和校验细节。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def create_token(subject: str, expires_in_minutes: int, token_type: str = "access") -> str:
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    return create_token(subject, settings.access_token_expire_minutes, token_type="access")


def create_refresh_token(subject: str) -> str:
    return create_token(subject, settings.refresh_token_expire_days * 24 * 60, token_type="refresh")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
