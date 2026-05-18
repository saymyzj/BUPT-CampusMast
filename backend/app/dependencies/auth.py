"""
文件说明：
这是鉴权依赖文件。
当前只提供最小的当前用户和管理员依赖占位，后续组长可在此补齐 JWT 校验、
用户查询和 WebSocket 鉴权逻辑。
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, WebSocket, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models.user import User
from app.utils.jwt import decode_token

security = HTTPBearer(auto_error=False)


def _load_current_user(token: str, db: Session) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="访问令牌类型错误")

    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已停用")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return _load_current_user(credentials.credentials, db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.value != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_current_user_for_websocket(websocket: WebSocket, db: Session) -> User:
    token = websocket.query_params.get("accessToken")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="缺少 accessToken")

    try:
        return _load_current_user(token, db)
    except HTTPException as exc:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc.detail)) from exc
