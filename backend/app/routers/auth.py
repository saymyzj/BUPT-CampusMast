"""
文件说明：
这是认证路由占位文件。
组长后续应在这里继续实现注册、登录、刷新令牌和当前用户资料接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.auth_service import build_stub_auth_payload
from app.utils.response import success

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register() -> dict:
    return success(build_stub_auth_payload())


@router.post("/login")
def login() -> dict:
    return success(build_stub_auth_payload())


@router.post("/refresh")
def refresh_token() -> dict:
    return success({"accessToken": build_stub_auth_payload()["accessToken"]})


@router.get("/me")
def get_me() -> dict:
    return success(build_stub_auth_payload()["user"])

