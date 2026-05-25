"""
文件说明：
这是本地验收版的图片上传工具。任务图片保存到后端本地 uploads 目录，
并通过 /uploads/... 静态路径访问。
"""
from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile, status

from app.config import settings
from app.utils.errors import AppError
from app.utils.ids import generate_id

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def upload_dir() -> Path:
    configured = Path(settings.local_upload_dir)
    return configured if configured.is_absolute() else BACKEND_ROOT / configured


def upload_base_url() -> str:
    return "/" + settings.local_upload_base_url.strip("/")


async def save_local_upload(file: UploadFile) -> dict[str, str]:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError("UPLOAD_TYPE_NOT_ALLOWED", "仅支持 JPG / PNG 图片", status.HTTP_400_BAD_REQUEST)

    max_bytes = settings.local_upload_max_size_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise AppError("UPLOAD_FILE_TOO_LARGE", f"单张图片不能超过 {settings.local_upload_max_size_mb}MB", status.HTTP_400_BAD_REQUEST)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ALLOWED_CONTENT_TYPES[content_type]

    directory = upload_dir()
    directory.mkdir(parents=True, exist_ok=True)

    filename = f"{generate_id('file')}{suffix}"
    target = directory / filename
    target.write_bytes(content)

    file_key = f"uploads/{filename}"
    return {
        "fileKey": file_key,
        "fileUrl": f"{upload_base_url()}/{filename}",
    }
