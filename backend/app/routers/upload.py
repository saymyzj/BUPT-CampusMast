"""
文件说明：
这是上传路由占位文件。
组长后续应在这里接入 OSS 预签名 URL 生成能力，并保持页面层只通过接口获取上传凭证。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.utils.oss import build_placeholder_upload_payload
from app.utils.response import success

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/sign")
def get_upload_sign() -> dict:
    return success(build_placeholder_upload_payload("placeholder.png"))

