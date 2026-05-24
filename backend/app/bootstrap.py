from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.config import HomepageBlock, SystemConfig
from app.models.enums import AdminReviewStatus, HomepageBlockType, ModerationResult, Role, TaskCategory, TaskStatus
from app.models.map import CampusBuilding
from app.models.moderation import ModerationRecord
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User, UserProfile
from app.models.wallet import Wallet
from app.utils.ids import generate_id
from app.utils.security import hash_password
from app.utils.serialization import json_dumps


def ensure_seed_data(db: Session) -> None:
    admin = _ensure_user(
        db,
        email=settings.seed_admin_email,
        nickname=settings.seed_admin_nickname,
        password=settings.seed_admin_password,
        role=Role.ADMIN,
        default_building_code="BUPT_MAIN",
    )
    demo_user = _ensure_user(
        db,
        email=settings.seed_demo_user_email,
        nickname=settings.seed_demo_user_nickname,
        password=settings.seed_demo_user_password,
        role=Role.USER,
        default_building_code="BUPT_MAIN",
    )
    _ensure_buildings(db)
    task = _ensure_demo_task(db, admin.id, demo_user.id)
    _ensure_notifications(db, admin.id, demo_user.id, task.id)
    _ensure_chat(db, admin.id, demo_user.id, task.id)
    _ensure_moderation(db, admin.id, task.id)
    _ensure_configs(db, admin.id)
    _ensure_homepage_blocks(db, admin.id)
    db.commit()


def _ensure_user(db: Session, *, email: str, nickname: str, password: str, role: Role, default_building_code: str) -> User:
    user = db.query(User).filter(User.student_email == email).one_or_none()
    if user is None:
        user = User(
            id=generate_id("u"),
            student_email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            role=role,
            requester_credit_score=100,
            helper_credit_score=100,
            overall_credit_score=100,
            is_active=True,
        )
        db.add(user)
        db.flush()

    profile = db.get(UserProfile, user.id)
    if profile is None:
        db.add(
            UserProfile(
                user_id=user.id,
                default_building_code=default_building_code,
                preferred_categories=json_dumps(["package", "food"]),
                active_time_slots=json_dumps(["morning", "afternoon"]),
                helper_success_rate=96,
            )
        )

    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).one_or_none()
    if wallet is None:
        db.add(Wallet(id=generate_id("wallet"), user_id=user.id, available=200, frozen=0))

    return user


def _ensure_buildings(db: Session) -> None:
    rows = [
        {
            "code": "BUPT_MAIN",
            "name": "北邮主楼",
            "campus_zone": "校本部",
            "latitude": 39.96003,
            "longitude": 116.35097,
            "polygon_json": json_dumps([[39.96010, 116.35075], [39.95982, 116.35118], [39.95960, 116.35095]]),
        },
        {
            "code": "BUPT_LIBRARY",
            "name": "图书馆",
            "campus_zone": "校本部",
            "latitude": 39.96088,
            "longitude": 116.35217,
            "polygon_json": None,
        },
        {
            "code": "BUPT_DORM_10",
            "name": "学生10号公寓",
            "campus_zone": "宿舍区",
            "latitude": 39.95844,
            "longitude": 116.35165,
            "polygon_json": None,
        },
    ]
    for payload in rows:
        if db.get(CampusBuilding, payload["code"]) is None:
            db.add(CampusBuilding(**payload, is_active=True))


def _ensure_demo_task(db: Session, requester_id: str, helper_id: str) -> Task:
    task = db.query(Task).filter(Task.title == "帮取中通快递").one_or_none()
    if task is None:
        task = Task(
            id=generate_id("task"),
            title="帮取中通快递",
            description="快递已到驿站，晚上九点前送到学生10号公寓门口即可。",
            category=TaskCategory.PACKAGE,
            reward=8.50,
            status=TaskStatus.PENDING,
            building_code="BUPT_MAIN",
            location_detail="学生10号公寓门口",
            deadline=datetime.now(timezone.utc) + timedelta(days=1),
            image_urls=json_dumps([]),
            requester_id=requester_id,
            helper_id=helper_id,
            proof_note="已到宿舍楼下。",
            proof_image_urls=json_dumps([]),
            moderation_result=ModerationResult.REVIEW,
            needs_admin_review=True,
        )
        db.add(task)
        db.flush()
    return task


def _ensure_notifications(db: Session, admin_id: str, user_id: str, task_id: str) -> None:
    if db.query(Notification).count() > 0:
        return
    db.add_all(
        [
            Notification(
                id=generate_id("notify"),
                user_id=user_id,
                type="SYSTEM_NOTICE",
                title="欢迎使用 CampusMast",
                body="演示数据已初始化，你可以直接联调通知与聊天。",
            ),
            Notification(
                id=generate_id("notify"),
                user_id=admin_id,
                type="MODERATION_REVIEW",
                title="存在待复审任务",
                body="任务需要管理员复审，请在后台审核管理中处理。",
                related_task_id=task_id,
            ),
        ]
    )


def _ensure_chat(db: Session, requester_id: str, helper_id: str, task_id: str) -> None:
    conversation = db.query(ChatConversation).filter(ChatConversation.task_id == task_id).one_or_none()
    if conversation is None:
        conversation = ChatConversation(id=generate_id("conv"), task_id=task_id, status="ACTIVE")
        db.add(conversation)
        db.flush()
        db.add_all(
            [
                ChatParticipant(id=generate_id("part"), conversation_id=conversation.id, user_id=requester_id, unread_count=0),
                ChatParticipant(id=generate_id("part"), conversation_id=conversation.id, user_id=helper_id, unread_count=1),
                ChatMessage(
                    id=generate_id("msg"),
                    conversation_id=conversation.id,
                    sender_id=requester_id,
                    message_type="TEXT",
                    content="到驿站后麻烦直接送到宿舍门口，谢谢。",
                ),
            ]
        )


def _ensure_moderation(db: Session, user_id: str, task_id: str) -> None:
    existing = db.query(ModerationRecord).filter(ModerationRecord.task_id == task_id).one_or_none()
    if existing is None:
        db.add(
            ModerationRecord(
                id=generate_id("mod"),
                task_id=task_id,
                user_id=user_id,
                provider="DEEPSEEK",
                risk_level=ModerationResult.REVIEW.value,
                hit_tags=json_dumps(["manual-review"]),
                model_output="演示数据：无真实模型输出。",
                admin_review_status=AdminReviewStatus.PENDING.value,
            )
        )


def _ensure_configs(db: Session, admin_id: str) -> None:
    defaults = [
        ("helperCreditThreshold", "credit", {"value": 60}, "接单最低信用分"),
        ("moderationFailurePolicy", "moderation", {"fallback": "REVIEW"}, "审核异常时的兜底策略"),
        ("homepageBannerRotationSeconds", "homepage", {"value": 6}, "首页轮播间隔"),
    ]
    for config_key, config_group, config_value, description in defaults:
        if db.get(SystemConfig, config_key) is None:
            db.add(
                SystemConfig(
                    config_key=config_key,
                    config_group=config_group,
                    config_value=json_dumps(config_value),
                    description=description,
                    updated_by=admin_id,
                )
            )


def _ensure_homepage_blocks(db: Session, admin_id: str) -> None:
    if db.query(HomepageBlock).count() > 0:
        return
    db.add_all(
        [
            HomepageBlock(
                id=generate_id("home"),
                block_type=HomepageBlockType.ANNOUNCEMENT.value,
                title="开学季公告",
                content=json_dumps({"text": "欢迎体验 CampusMast 演示环境。"}),
                sort_order=1,
                is_active=True,
                updated_by=admin_id,
            ),
            HomepageBlock(
                id=generate_id("home"),
                block_type=HomepageBlockType.BANNER.value,
                title="地图任务 Banner",
                content=json_dumps({"imageUrl": "https://example.com/banner.png", "link": "/map"}),
                sort_order=2,
                is_active=True,
                updated_by=admin_id,
            ),
        ]
    )

    # 使用 sqlite 作本地开发兜底，便于在没有 MySQL 服务或凭据的机器上快速联调
    database_url: str = "sqlite:///./campusmast.db"
