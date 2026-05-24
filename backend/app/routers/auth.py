"""
文件说明：
这是认证路由文件。
负责注册、登录、刷新令牌和当前用户资料接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, TokenRefreshRequest, UserUpdateRequest
from app.services.auth_service import get_current_user_payload, login_user, refresh_access_token, register_user, update_current_user
from app.utils.response import success

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> dict:
    return success(register_user(db, payload).model_dump())


@router.post("/login")
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> dict:
    return success(login_user(db, payload).model_dump())


@router.post("/refresh")
def refresh_token(payload: TokenRefreshRequest, db: Session = Depends(get_db)) -> dict:
    return success(refresh_access_token(db, payload.refreshToken))


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return success(get_current_user_payload(db, user).model_dump())


@router.put("/me")
def update_me(
    payload: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return success(update_current_user(db, user, payload).model_dump())
