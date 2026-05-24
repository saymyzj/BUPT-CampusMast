"""
文件说明：
这是 OSS 工具文件。
负责生成 OSS 直传所需的预签名地址；在未配置真实 OSS 时返回可联调的开发占位地址。
"""
from __future__ import annotations

from pathlib import Path

import oss2

from app.config import settings
from app.utils.ids import generate_id


PLACEHOLDER_VALUES = {"replace-me", "your-access-key-id", "your-access-key-secret", "changeme"}


def _is_configured(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip().lower() not in PLACEHOLDER_VALUES)


def build_signed_upload_payload(filename: str, content_type: str) -> dict[str, str]:
    suffix = Path(filename).suffix or ""
    file_key = f"uploads/{generate_id('file')}{suffix}"

    if (
        _is_configured(settings.oss_endpoint)
        and _is_configured(settings.oss_bucket_name)
        and _is_configured(settings.oss_access_key_id)
        and _is_configured(settings.oss_access_key_secret)
    ):
        auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
        bucket = oss2.Bucket(auth, f"https://{settings.oss_endpoint}", settings.oss_bucket_name)
        upload_url = bucket.sign_url(
            "PUT",
            file_key,
            settings.oss_upload_expire_seconds,
            headers={"Content-Type": content_type},
        )
        base_url = settings.oss_base_url.rstrip("/") if settings.oss_base_url else f"https://{settings.oss_bucket_name}.{settings.oss_endpoint}"
        return {"uploadUrl": upload_url, "fileKey": file_key, "fileUrl": f"{base_url}/{file_key}"}

    return {
        "uploadUrl": f"https://example.com/mock-upload/{file_key}",
        "fileKey": file_key,
        "fileUrl": f"https://cdn.example.com/{file_key}",
    }
