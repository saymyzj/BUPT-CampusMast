"""
文件说明：
这是上传模块的 Schema 文件。
组长后续应在 OSS 直传方案稳定后，把真实签名返回结构继续补到这里。
"""
from __future__ import annotations

from pydantic import BaseModel


class UploadSignRequest(BaseModel):
    filename: str
    contentType: str


class UploadSignResponse(BaseModel):
    uploadUrl: str
    fileKey: str
    fileUrl: str

