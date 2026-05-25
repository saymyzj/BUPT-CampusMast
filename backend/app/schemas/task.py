"""
文件说明：
这是任务模块的 Schema 文件。
它覆盖任务创建、任务摘要、任务详情、完成证明和争议请求等核心载荷。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    category: str
    reward: str
    deadline: str
    buildingCode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    locationDetail: str | None = None
    imageUrls: list[str] = []


class TaskProofRequest(BaseModel):
    proofNote: str | None = None
    proofImageUrls: list[str] = []


class TaskRejectRequest(BaseModel):
    reason: str


class UserSummary(BaseModel):
    id: str
    nickname: str
    overallCreditScore: float


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    reward: str
    status: str
    buildingCode: str
    latitude: float | None = None
    longitude: float | None = None
    locationDetail: str | None = None
    requester: UserSummary
    helper: UserSummary | None = None
    moderationResult: str
    needsAdminReview: bool
    distanceMeters: float | None = None
    recommendation: dict | None = None


class TaskLogResponse(BaseModel):
    id: str
    fromStatus: str
    toStatus: str
    actorId: str
    remark: str | None = None
    createdAt: str


class TaskDetailResponse(TaskResponse):
    proofNote: str | None = None
    proofImageUrls: list[str] = []
    logs: list[TaskLogResponse] = []
