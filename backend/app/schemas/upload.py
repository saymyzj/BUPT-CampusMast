"""
文件说明：
这是上传模块的 Schema 文件。
本地验收版直接把任务图片保存到后端 uploads 目录，并返回可访问地址。
"""
from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    fileKey: str
    fileUrl: str
