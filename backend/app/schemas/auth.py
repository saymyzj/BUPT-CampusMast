"""
文件说明：
这是认证与用户资料相关的 Schema 文件。
组长后续应把真实的认证返回、用户资料展示和前端联调字段继续补齐到这里。
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class AuthRegisterRequest(BaseModel):
    studentEmail: EmailStr
    password: str
    nickname: str


class AuthLoginRequest(BaseModel):
    studentEmail: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refreshToken: str


class UserResponse(BaseModel):
    id: str
    studentEmail: EmailStr
    nickname: str
    role: str
    requesterCreditScore: float
    helperCreditScore: float
    overallCreditScore: float
    avatarUrl: str | None = None
    defaultBuildingCode: str | None = None


class AuthPayload(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserResponse

