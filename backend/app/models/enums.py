"""
文件说明：
这是后端统一枚举定义文件。
状态机、审核结果、消息类型、首页内容类型等跨模块共享的枚举都应在这里集中维护，
以避免任务、通知、后台和 API 文档之间出现不一致。
"""
from __future__ import annotations

import enum


class Role(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    CLOSED_BY_ADMIN = "CLOSED_BY_ADMIN"


class TaskCategory(str, enum.Enum):
    PACKAGE = "package"
    FOOD = "food"
    MOVE = "move"
    OTHER = "other"


class TransactionType(str, enum.Enum):
    TOP_UP = "TOP_UP"
    WITHDRAW = "WITHDRAW"
    FREEZE = "FREEZE"
    UNFREEZE = "UNFREEZE"
    SETTLE_OUT = "SETTLE_OUT"
    SETTLE_IN = "SETTLE_IN"
    SETTLE_SPLIT = "SETTLE_SPLIT"


class ModerationResult(str, enum.Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class AdminReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChatMessageType(str, enum.Enum):
    TEXT = "TEXT"


class HomepageBlockType(str, enum.Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    BANNER = "BANNER"
    RECOMMEND_SLOT = "RECOMMEND_SLOT"

