"""
文件说明：
这是鉴权依赖文件。
当前只提供最小的当前用户和管理员依赖占位，后续组长可在此补齐 JWT 校验、
用户查询和 WebSocket 鉴权逻辑。
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    return {
        "id": "u_stub",
        "role": "ADMIN",
        "nickname": "脚手架用户",
    }


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user

