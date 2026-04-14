"""
文件说明：
这是系统配置与首页内容配置的 Schema 文件。
组长后续在后台页里修改信用权重、审核阈值和首页内容时都应复用这里的结构。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConfigUpdateRequest(BaseModel):
    configValue: dict[str, Any]


class ConfigItemResponse(BaseModel):
    configKey: str
    configGroup: str
    configValue: dict[str, Any]
    description: str | None = None
    updatedAt: str


class HomepageBlockResponse(BaseModel):
    id: str
    blockType: str
    title: str
    content: dict[str, Any]
    sortOrder: int
    isActive: bool

