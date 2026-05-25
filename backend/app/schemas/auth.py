"""
文件说明：
这是认证与用户资料相关的 Schema 文件。
组长后续应把真实的认证返回、用户资料展示和前端联调字段继续补齐到这里。
"""
from __future__ import annotations

from pydantic import BaseModel


class AuthRegisterRequest(BaseModel):
    studentEmail: str
    password: str
    nickname: str


class AuthLoginRequest(BaseModel):
    studentEmail: str
    password: str


class TokenRefreshRequest(BaseModel):
    refreshToken: str


class PasswordResetRequest(BaseModel):
    studentEmail: str
    newPassword: str


class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    phone: str | None = None
    avatarUrl: str | None = None
    defaultBuildingCode: str | None = None


class UserResponse(BaseModel):
    id: str
    studentEmail: str
    nickname: str
    role: str
    phone: str | None = None
    requesterCreditScore: float
    helperCreditScore: float
    overallCreditScore: float
    isActive: bool = True
    avatarUrl: str | None = None
    defaultBuildingCode: str | None = None


class UserPublicResponse(BaseModel):
    id: str
    nickname: str
    role: str
    phone: str | None = None
    avatarUrl: str | None = None
    requesterCreditScore: float
    helperCreditScore: float
    overallCreditScore: float


class AuthPayload(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserResponse
