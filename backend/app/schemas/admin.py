"""
文件说明：
这是后台管理模块的 Schema 文件。
覆盖争议裁决、审核复审、用户调整等后台操作的请求结构。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdminResolveDisputeRequest(BaseModel):
    resolution: str
    splitRatio: float | None = Field(default=None, ge=0, le=1)
    note: str


class AdminReviewModerationRequest(BaseModel):
    decision: str
    note: str | None = None


class AdminUpdateUserRequest(BaseModel):
    isActive: bool | None = None
    requesterCreditScore: float | None = None
    helperCreditScore: float | None = None

