"""
文件说明：
这是模型包出口文件。
集中导入所有 ORM 模型，方便 Alembic 和应用启动时一次性加载元数据。
"""
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.config import HomepageBlock, SystemConfig
from app.models.map import CampusBuilding
from app.models.moderation import ModerationRecord
from app.models.notification import Notification
from app.models.rating import CreditSnapshot, Rating
from app.models.recommendation import RecommendationSnapshot
from app.models.task import Task, TaskLog
from app.models.user import User, UserProfile
from app.models.wallet import Transaction, Wallet

__all__ = [
    "ChatConversation",
    "ChatMessage",
    "ChatParticipant",
    "HomepageBlock",
    "SystemConfig",
    "CampusBuilding",
    "ModerationRecord",
    "Notification",
    "CreditSnapshot",
    "Rating",
    "RecommendationSnapshot",
    "Task",
    "TaskLog",
    "User",
    "UserProfile",
    "Transaction",
    "Wallet",
]
