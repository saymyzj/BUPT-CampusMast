"""
文件说明：
这是认证服务文件。
负责注册、登录、刷新令牌、当前用户资料读取与更新逻辑。
"""
from __future__ import annotations

from fastapi import status
from sqlalchemy.orm import Session

from app.models.enums import Role
from app.models.user import User, UserProfile
from app.schemas.auth import AuthLoginRequest, AuthPayload, AuthRegisterRequest, PasswordChangeRequest, UserPublicResponse, UserResponse, UserUpdateRequest
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.utils.security import hash_password, verify_password
from app.utils.serialization import decimal_to_float

BUPT_EMAIL_SUFFIX = "@bupt.edu.cn"


def register_user(db: Session, payload: AuthRegisterRequest) -> AuthPayload:
    email = payload.studentEmail.lower().strip()
    if not email.endswith(BUPT_EMAIL_SUFFIX):
        raise AppError("INVALID_EMAIL_DOMAIN", "仅支持北京邮电大学邮箱注册", status.HTTP_400_BAD_REQUEST)

    existing = db.query(User).filter(User.student_email == email).one_or_none()
    if existing is not None:
        raise AppError("EMAIL_ALREADY_EXISTS", "该邮箱已注册", status.HTTP_409_CONFLICT)

    user = User(
        id=generate_id("u"),
        student_email=email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname.strip(),
        role=Role.USER,
        requester_credit_score=100,
        helper_credit_score=100,
        overall_credit_score=100,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return build_auth_payload(db, user)


def login_user(db: Session, payload: AuthLoginRequest) -> AuthPayload:
    account = payload.studentEmail.strip()
    normalized_account = account.lower() if "@" in account else account
    user = db.query(User).filter(User.student_email == normalized_account).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "邮箱或密码错误", status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise AppError("USER_DISABLED", "账号已停用", status.HTTP_403_FORBIDDEN)
    return build_auth_payload(db, user)


def refresh_access_token(db: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise AppError("INVALID_REFRESH_TOKEN", "刷新令牌无效", status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get("type") != "refresh":
        raise AppError("INVALID_REFRESH_TOKEN", "刷新令牌类型错误", status.HTTP_401_UNAUTHORIZED)

    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise AppError("USER_DISABLED", "账号不存在或已停用", status.HTTP_401_UNAUTHORIZED)

    return {"accessToken": create_access_token(user.id)}


def change_current_user_password(db: Session, user: User, payload: PasswordChangeRequest) -> dict[str, str]:
    if not verify_password(payload.currentPassword, user.password_hash):
        raise AppError("INVALID_CURRENT_PASSWORD", "当前密码错误", status.HTTP_400_BAD_REQUEST)
    if len(payload.newPassword) < 6:
        raise AppError("INVALID_PASSWORD", "新密码至少 6 位", status.HTTP_400_BAD_REQUEST)

    user.password_hash = hash_password(payload.newPassword)
    db.commit()
    return {"message": "密码已修改"}


def get_current_user_payload(db: Session, user: User) -> UserResponse:
    return serialize_user(db, user)


def update_current_user(db: Session, user: User, payload: UserUpdateRequest) -> UserResponse:
    profile = db.get(UserProfile, user.id)
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    if payload.nickname is not None:
        user.nickname = payload.nickname.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.avatarUrl is not None:
        user.avatar_url = payload.avatarUrl.strip() or None
    if payload.defaultBuildingCode is not None:
        profile.default_building_code = payload.defaultBuildingCode.strip() or None

    db.commit()
    db.refresh(user)
    return serialize_user(db, user)


def get_public_user_profile(db: Session, user_id: str) -> UserPublicResponse:
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError("USER_NOT_FOUND", "用户不存在或已停用", status.HTTP_404_NOT_FOUND)
    return UserPublicResponse(
        id=user.id,
        nickname=user.nickname,
        role=user.role.value,
        phone=user.phone,
        avatarUrl=user.avatar_url,
        requesterCreditScore=decimal_to_float(user.requester_credit_score) or 0,
        helperCreditScore=decimal_to_float(user.helper_credit_score) or 0,
        overallCreditScore=decimal_to_float(user.overall_credit_score) or 0,
    )


def build_auth_payload(db: Session, user: User) -> AuthPayload:
    return AuthPayload(
        accessToken=create_access_token(user.id),
        refreshToken=create_refresh_token(user.id),
        user=serialize_user(db, user),
    )


def serialize_user(db: Session, user: User) -> UserResponse:
    profile = db.get(UserProfile, user.id)
    return UserResponse(
        id=user.id,
        studentEmail=user.student_email,
        nickname=user.nickname,
        role=user.role.value,
        phone=user.phone,
        requesterCreditScore=decimal_to_float(user.requester_credit_score) or 0,
        helperCreditScore=decimal_to_float(user.helper_credit_score) or 0,
        overallCreditScore=decimal_to_float(user.overall_credit_score) or 0,
        isActive=user.is_active,
        avatarUrl=user.avatar_url,
        defaultBuildingCode=profile.default_building_code if profile else None,
    )
