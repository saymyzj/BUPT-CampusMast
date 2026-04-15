"""
文件说明：
这是上传路由文件。
负责生成 OSS 预签名上传地址。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.upload import UploadSignRequest
from app.utils.oss import build_signed_upload_payload
from app.utils.response import success

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/sign")
def get_upload_sign(payload: UploadSignRequest, _: User = Depends(get_current_user)) -> dict:
    return success(build_signed_upload_payload(payload.filename, payload.contentType))
