"""
文件说明：
这是 OSS 工具文件占位。
组长后续应在这里补充真实的预签名上传逻辑，而不是在上传路由里直接写 SDK 调用。
"""
from __future__ import annotations


def build_placeholder_upload_payload(filename: str) -> dict[str, str]:
    return {
        "uploadUrl": f"https://example.com/upload/{filename}",
        "fileKey": f"uploads/dev/{filename}",
        "fileUrl": f"https://cdn.example.com/uploads/dev/{filename}",
    }

