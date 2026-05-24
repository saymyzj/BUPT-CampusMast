"""
文件说明：
这是密码安全工具文件。
组长后续应在这里统一处理密码哈希与校验，不要把密码逻辑散落到路由层。
"""
from __future__ import annotations

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

