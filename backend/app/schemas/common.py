"""
文件说明：
这是后端公共响应模型文件。
统一定义成功响应、错误响应和分页元数据，避免不同路由返回结构不一致。
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = 0
    page: int = 1
    limit: int = 20


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: dict[str, Any] | PaginationMeta | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorInfo

