"""
文件说明：
这是统一响应工具文件。
Router 层如需快速返回成功结构，可直接复用这里的包装函数，减少手写重复代码。
"""
from __future__ import annotations

from typing import Any


def success(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "meta": meta}


def failure(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message, "details": details}}

