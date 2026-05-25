from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.models.base import Base, SessionLocal, engine
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.config import HomepageBlock, SystemConfig
from app.models.enums import AdminReviewStatus, HomepageBlockType, ModerationResult, Role, TaskCategory, TaskStatus, TransactionType
from app.models.map import CampusBuilding
from app.models.moderation import ModerationRecord
from app.models.notification import Notification
from app.models.rating import Rating
from app.models.task import Task, TaskLog
from app.models.user import User, UserProfile
from app.models.wallet import Transaction, Wallet
from app.utils.ids import generate_id
from app.utils.security import hash_password
from app.utils.serialization import json_dumps

DEFAULT_PASSWORD = "12345"


def _set_foreign_key_checks(db: Session, enabled: bool) -> None:
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "mysql":
        db.execute(text(f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"))
    elif dialect == "sqlite":
        db.execute(text(f"PRAGMA foreign_keys = {'ON' if enabled else 'OFF'}"))


def _clear_application_tables(db: Session) -> None:
    _set_foreign_key_checks(db, False)
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    finally:
        _set_foreign_key_checks(db, True)


def _user(db: Session, account: str, nickname: str, role: Role, building_code: str) -> User:
    user = User(
        id=generate_id("u"),
        student_email=account,
        password_hash=hash_password(DEFAULT_PASSWORD),
        nickname=nickname,
        role=role,
        requester_credit_score=Decimal("100.00"),
        helper_credit_score=Decimal("100.00"),
        overall_credit_score=Decimal("100.00"),
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            default_building_code=building_code,
            preferred_categories=json_dumps(["package", "food", "move"]),
            active_time_slots=json_dumps(["morning", "evening"]),
            helper_success_rate=Decimal("96.00"),
        )
    )
    db.add(Wallet(id=generate_id("wallet"), user_id=user.id, available=Decimal("200.00"), frozen=Decimal("0.00")))
    return user


def _building(db: Session, code: str, name: str, zone: str, lat: float, lng: float) -> None:
    db.add(CampusBuilding(code=code, name=name, campus_zone=zone, latitude=lat, longitude=lng, is_active=True))


def _task(
    db: Session,
    *,
    title: str,
    category: TaskCategory,
    reward: str,
    status: TaskStatus,
    building_code: str,
    requester: User,
    helper: User | None = None,
    needs_review: bool = False,
    days_offset: int = 1,
) -> Task:
    task = Task(
        id=generate_id("task"),
        title=title,
        description=f"{title}，用于本地联调演示。",
        category=category,
        reward=Decimal(reward),
        status=status,
        building_code=building_code,
        location_detail="楼下入口",
        deadline=datetime.utcnow() + timedelta(days=days_offset),
        image_urls=json_dumps([]),
        requester_id=requester.id,
        helper_id=helper.id if helper else None,
        proof_note="已完成，等待确认。" if status in {TaskStatus.PENDING_REVIEW, TaskStatus.COMPLETED} else None,
        proof_image_urls=json_dumps([]),
        moderation_result=ModerationResult.REVIEW if needs_review else ModerationResult.ALLOW,
        needs_admin_review=needs_review,
        completed_at=datetime.utcnow() if status == TaskStatus.COMPLETED else None,
    )
    db.add(task)
    db.flush()
    _log(db, task, status)
    return task


def _log(db: Session, task: Task, status: TaskStatus) -> None:
    db.add(
        TaskLog(
            id=generate_id("log"),
            task_id=task.id,
            from_status=TaskStatus.PENDING,
            to_status=status,
            actor_id=task.helper_id or task.requester_id,
            remark=f"演示数据状态：{status.value}",
        )
    )


def _notification(db: Session, user: User, type_: str, title: str, body: str, task: Task | None = None, unread: bool = True) -> None:
    db.add(
        Notification(
            id=generate_id("notify"),
            user_id=user.id,
            type=type_,
            title=title,
            body=body,
            related_task_id=task.id if task else None,
            is_read=not unread,
        )
    )


def _chat(db: Session, task: Task, requester: User, helper: User) -> None:
    conversation = ChatConversation(id=generate_id("conv"), task_id=task.id, status="ACTIVE")
    db.add(conversation)
    db.flush()
    db.add_all(
        [
            ChatParticipant(id=generate_id("part"), conversation_id=conversation.id, user_id=requester.id, unread_count=0),
            ChatParticipant(id=generate_id("part"), conversation_id=conversation.id, user_id=helper.id, unread_count=1),
            ChatMessage(id=generate_id("msg"), conversation_id=conversation.id, sender_id=requester.id, message_type="TEXT", content="我已经在路上了，麻烦完成后发一下证明。"),
            ChatMessage(id=generate_id("msg"), conversation_id=conversation.id, sender_id=helper.id, message_type="TEXT", content="收到，我完成后会提交。"),
        ]
    )


def _moderation(db: Session, user: User, task: Task, risk: ModerationResult, tags: list[str]) -> None:
    db.add(
        ModerationRecord(
            id=generate_id("mod"),
            task_id=task.id,
            user_id=user.id,
            provider="DEEPSEEK",
            risk_level=risk.value,
            hit_tags=json_dumps(tags),
            model_output="演示数据：真实 DeepSeek + 关键词兜底口径。",
            admin_review_status=AdminReviewStatus.PENDING.value if risk == ModerationResult.REVIEW else AdminReviewStatus.APPROVED.value,
        )
    )


def _config(db: Session, admin: User) -> None:
    rows = [
        ("helperCreditThreshold", "credit", {"value": 60}, "接单最低信用分"),
        (
            "credit.weights",
            "credit",
            {
                "helper": {"completion_rate": 0.35, "average_rating": 0.25, "timeout_rate": 0.15, "abandon_rate": 0.15, "dispute_lose_rate": 0.10},
                "requester": {"completion_rate": 0.35, "average_rating": 0.25, "timeout_rate": 0.15, "malicious_dispute_rate": 0.15, "post_accept_cancel_rate": 0.10},
                "overall": {"helper": 0.60, "requester": 0.40},
            },
            "双分制信用权重",
        ),
        ("recommendation.weights", "recommendation", {"category": 0.30, "distance": 0.30, "successRate": 0.25, "activeTime": 0.15}, "推荐排序权重"),
        ("moderation.mode", "moderation", {"provider": "DEEPSEEK", "fallback": "KEYWORD_RULES", "failurePolicy": "REVIEW"}, "AI 审核最终口径：真实 DeepSeek + 关键词兜底"),
        ("homepageBannerRotationSeconds", "homepage", {"value": 6}, "首页轮播间隔"),
    ]
    for key, group, value, description in rows:
        db.add(SystemConfig(config_key=key, config_group=group, config_value=json_dumps(value), description=description, updated_by=admin.id))

    db.add_all(
        [
            HomepageBlock(id=generate_id("home"), block_type=HomepageBlockType.ANNOUNCEMENT.value, title="联调公告", content=json_dumps({"text": "演示数据已生成，可测试任务、钱包、通知、聊天和后台审核。"}), sort_order=1, is_active=True, updated_by=admin.id),
            HomepageBlock(id=generate_id("home"), block_type=HomepageBlockType.BANNER.value, title="校园互助 Banner", content=json_dumps({"imageUrl": "/assets/hero-bupt-gate.jpg", "link": "/tasks"}), sort_order=2, is_active=True, updated_by=admin.id),
            HomepageBlock(id=generate_id("home"), block_type=HomepageBlockType.RECOMMEND_SLOT.value, title="推荐任务位", content=json_dumps({"category": "package", "limit": 3}), sort_order=3, is_active=True, updated_by=admin.id),
        ]
    )


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _clear_application_tables(db)
        admin = _user(db, "Admin", "Admin", Role.ADMIN, "BUPT_MAIN")
        user01 = _user(db, "user01", "user01", Role.USER, "BUPT_DORM_10")
        helper = _user(db, "user02", "演示接单人", Role.USER, "BUPT_LIBRARY")
        _building(db, "BUPT_MAIN", "北邮主楼", "校本部", 39.96003, 116.35097)
        _building(db, "BUPT_LIBRARY", "图书馆", "校本部", 39.96088, 116.35217)
        _building(db, "BUPT_DORM_10", "学生10号公寓", "宿舍区", 39.95844, 116.35165)
        pending = _task(db, title="帮取中通快递", category=TaskCategory.PACKAGE, reward="8.50", status=TaskStatus.PENDING, building_code="BUPT_MAIN", requester=admin)
        in_progress = _task(db, title="帮忙带一份晚餐", category=TaskCategory.FOOD, reward="12.00", status=TaskStatus.IN_PROGRESS, building_code="BUPT_LIBRARY", requester=user01, helper=helper)
        review = _task(db, title="搬一箱资料到主楼", category=TaskCategory.MOVE, reward="20.00", status=TaskStatus.PENDING_REVIEW, building_code="BUPT_DORM_10", requester=admin, helper=helper, needs_review=True)
        completed = _task(db, title="打印资料并送到教三", category=TaskCategory.OTHER, reward="6.00", status=TaskStatus.COMPLETED, building_code="BUPT_MAIN", requester=user01, helper=helper, days_offset=-1)
        disputed = _task(db, title="代取快递发生争议", category=TaskCategory.PACKAGE, reward="15.00", status=TaskStatus.DISPUTED, building_code="BUPT_LIBRARY", requester=user01, helper=helper)
        _chat(db, in_progress, user01, helper)
        _chat(db, review, admin, helper)
        _notification(db, user01, "TASK_ACCEPTED", "任务已被接单", "你的晚餐任务已被接单。", in_progress)
        _notification(db, admin, "MODERATION_REVIEW", "有任务待复审", "搬运资料任务需要管理员复审。", review)
        _notification(db, helper, "CHAT_MESSAGE", "收到新消息", "任务聊天中有一条新消息。", in_progress)
        _moderation(db, admin, pending, ModerationResult.ALLOW, [])
        _moderation(db, admin, review, ModerationResult.REVIEW, ["manual-review"])
        _moderation(db, user01, disputed, ModerationResult.REVIEW, ["争议"])
        db.add(Rating(id=generate_id("rating"), task_id=completed.id, from_user_id=user01.id, to_user_id=helper.id, score=5, comment="完成很快"))
        helper_wallet = db.query(Wallet).filter(Wallet.user_id == helper.id).one()
        db.add(Transaction(id=generate_id("tx"), wallet_id=helper_wallet.id, type=TransactionType.SETTLE_IN, amount=Decimal("6.00"), balance_after=Decimal("206.00"), related_task_id=completed.id, description="收到发布者任务赏金"))
        _config(db, admin)
        db.commit()
        print("Demo data generated.")
        print(f"Admin account: Admin / {DEFAULT_PASSWORD}")
        print(f"User account: user01 / {DEFAULT_PASSWORD}")
        print(f"Helper account: user02 / {DEFAULT_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
