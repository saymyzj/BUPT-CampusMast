"""
文件说明：
这是信用与评价模块的 Schema 文件。
用于统一评价提交和信用分展示结构。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RatingCreateRequest(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str | None = None


class RatingResponse(BaseModel):
    id: str
    taskId: str
    fromUserId: str
    toUserId: str
    score: int
    comment: str | None = None
    createdAt: str


class CreditProfileResponse(BaseModel):
    requesterCreditScore: float
    helperCreditScore: float
    overallCreditScore: float

