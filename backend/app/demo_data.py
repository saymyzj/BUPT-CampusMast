from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.init_data import ADMIN_ACCOUNT, DEFAULT_PASSWORD, initialize_database
from app.models.base import SessionLocal
from app.models.enums import HomepageBlockType, ModerationResult, TaskCategory
from app.models.chat import ChatConversation
from app.models.task import Task
from app.models.user import User, UserProfile
from app.schemas.admin import AdminResolveDisputeRequest, AdminReviewModerationRequest
from app.schemas.config import ConfigUpdateRequest, HomepageBlockUpsertRequest
from app.schemas.credit import RatingCreateRequest
from app.schemas.task import TaskCreateRequest, TaskProofRequest
from app.services.admin_service import resolve_dispute
from app.services.chat_service import create_message, mark_conversation_read
from app.services.config_service import update_config, upsert_homepage_block
from app.services.credit_service import rate_task_partner, recalculate_user_credit
from app.services.moderation_service import create_moderation_record, review_moderation_record
from app.services.notification_service import create_notification
from app.services.recommendation_service import list_recommended_tasks
from app.services.task_service import (
    abandon_task,
    accept_task,
    cancel_task,
    confirm_task,
    create_task,
    dispute_in_progress_task,
    expire_task,
    reject_task,
    submit_task_proof,
)
from app.services.wallet_service import top_up, withdraw
from app.utils.serialization import json_dumps
from app.osm_buildings import seed_default_buildings


def _payload(
    *,
    title: str,
    description: str,
    category: TaskCategory,
    reward: str,
    building_code: str,
    location_detail: str,
    days: int = 2,
):
    return TaskCreateRequest(
        title=title,
        description=description,
        category=category.value,
        reward=reward,
        deadline=(datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
        buildingCode=building_code,
        latitude=None,
        longitude=None,
        locationDetail=location_detail,
        imageUrls=[],
    )


def _proof(note: str):
    return TaskProofRequest(proofNote=note, proofImageUrls=[])


def _rating(score: int, comment: str):
    return RatingCreateRequest(score=score, comment=comment)


def _user(db, account: str) -> User:
    user = db.query(User).filter(User.student_email == account).one()
    return user


def _set_profile(db, user: User, building_code: str, categories: list[str], slots: list[str], success_rate: str) -> None:
    profile = db.get(UserProfile, user.id)
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.default_building_code = building_code
    profile.preferred_categories = json_dumps(categories)
    profile.active_time_slots = json_dumps(slots)
    profile.helper_success_rate = Decimal(success_rate)


def _seed_buildings(db) -> None:
    seed_default_buildings(db)


def _seed_configs(db, admin: User) -> None:
    configs = [
        ("helperCreditThreshold", "credit", {"value": 60}, "接单最低信用分"),
        (
            "credit.weights",
            "credit",
            {
                "helper": {
                    "completion_rate": 0.35,
                    "average_rating": 0.25,
                    "timeout_rate": 0.15,
                    "abandon_rate": 0.15,
                    "dispute_lose_rate": 0.10,
                },
                "requester": {
                    "completion_rate": 0.35,
                    "average_rating": 0.25,
                    "timeout_rate": 0.15,
                    "malicious_dispute_rate": 0.15,
                    "post_accept_cancel_rate": 0.10,
                },
                "overall": {"helper": 0.60, "requester": 0.40},
            },
            "双分制信用权重",
        ),
        (
            "recommendation.weights",
            "recommendation",
            {"category": 0.30, "distance": 0.30, "successRate": 0.25, "activeTime": 0.15},
            "推荐排序权重",
        ),
        (
            "moderation.mode",
            "moderation",
            {"provider": "DEEPSEEK", "fallback": "KEYWORD_RULES", "failurePolicy": "REVIEW"},
            "AI 审核最终口径：真实 DeepSeek + 关键词兜底",
        ),
        ("homepageBannerRotationSeconds", "homepage", {"value": 6}, "首页轮播间隔"),
    ]
    for key, group, value, description in configs:
        update_config(
            db,
            key=key,
            payload=ConfigUpdateRequest(configValue=value, configGroup=group, description=description),
            admin_id=admin.id,
        )

    blocks = [
        (
            "home_announcement_demo",
            HomepageBlockType.ANNOUNCEMENT.value,
            "联调公告",
            {"text": "演示数据已生成，可测试任务、钱包、通知、聊天、审核、推荐和后台。"},
            1,
        ),
        (
            "home_banner_demo",
            HomepageBlockType.BANNER.value,
            "校园互助 Banner",
            {"imageUrl": "/assets/hero-bupt-gate.jpg", "link": "/tasks"},
            2,
        ),
        (
            "home_recommend_demo",
            HomepageBlockType.RECOMMEND_SLOT.value,
            "推荐任务位",
            {"category": "package", "limit": 3},
            3,
        ),
    ]
    for block_id, block_type, title, content, sort_order in blocks:
        upsert_homepage_block(
            db,
            block_id=block_id,
            payload=HomepageBlockUpsertRequest(
                blockType=block_type,
                title=title,
                content=content,
                sortOrder=sort_order,
                isActive=True,
            ),
            admin_id=admin.id,
        )


def _record_manual_moderation(
    db,
    *,
    admin: User,
    user: User,
    task_id: str | None,
    risk: ModerationResult,
    tags: list[str],
    note: str,
    decision: str | None = None,
) -> None:
    record = create_moderation_record(
        db,
        user_id=user.id,
        task_id=task_id,
        risk_level=risk,
        hit_tags=tags,
        model_output=note,
    )
    db.commit()
    if decision is not None:
        review_moderation_record(
            db,
            record_id=record.id,
            payload=AdminReviewModerationRequest(decision=decision, note=f"演示复审：{note}"),
            admin_id=admin.id,
        )


def _set_deadline_past(db, task_id: str) -> None:
    task = db.get(Task, task_id)
    task.deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
    db.commit()


def seed_demo_data() -> None:
    initialize_database()
    db = SessionLocal()
    try:
        admin = _user(db, ADMIN_ACCOUNT)
        user01 = _user(db, "user01")
        user02 = _user(db, "user02")
        user03 = _user(db, "user03")
        user04 = _user(db, "user04")
        user05 = _user(db, "user05")
        user06 = _user(db, "user06")
        user07 = _user(db, "user07")
        user08 = _user(db, "user08")
        user09 = _user(db, "user09")
        user10 = _user(db, "user10")

        _seed_buildings(db)
        _seed_configs(db, admin)

        _set_profile(db, user01, "BUPT_DORM_10", ["package", "food"], [18, 20, 21], "96.00")
        _set_profile(db, user02, "BUPT_LIBRARY", ["package", "move"], [14, 18, 20], "92.00")
        _set_profile(db, user03, "BUPT_CANTEEN", ["food", "other"], [8, 12, 13], "88.00")
        _set_profile(db, user04, "BUPT_MAIN", ["other", "move"], [15, 16, 18], "75.00")
        _set_profile(db, user05, "BUPT_EXPRESS", ["package"], [18, 19, 20], "70.00")
        db.commit()

        for user in [admin, user01, user02, user03, user04, user05, user06, user07, user08, user09, user10]:
            top_up(db, user.id, "300.00")
        withdraw(db, user10.id, "35.00")

        pending_package = create_task(
            db,
            user01.id,
            _payload(
                title="帮取中通快递",
                description="快递已到驿站，请晚上九点前送到学生10号公寓门口。",
                category=TaskCategory.PACKAGE,
                reward="8.50",
                building_code="BUPT_EXPRESS",
                location_detail="快递驿站 3 号架",
            ),
        )
        pending_food = create_task(
            db,
            user03.id,
            _payload(
                title="帮带一份晚餐",
                description="学苑餐厅二楼窗口取餐，送到图书馆东门。",
                category=TaskCategory.FOOD,
                reward="12.00",
                building_code="BUPT_CANTEEN",
                location_detail="学苑餐厅二楼",
            ),
        )

        in_progress = create_task(
            db,
            user04.id,
            _payload(
                title="搬一箱社团资料到主楼",
                description="纸质材料一箱，需从宿舍区搬到主楼大厅。",
                category=TaskCategory.MOVE,
                reward="20.00",
                building_code="BUPT_DORM_10",
                location_detail="10 号公寓楼下",
            ),
        )
        accept_task(db, in_progress.id, user02.id)

        pending_review = create_task(
            db,
            user05.id,
            _payload(
                title="打印资料并送到教三",
                description="资料已上传，请打印后送到主楼前台。",
                category=TaskCategory.OTHER,
                reward="10.00",
                building_code="BUPT_MAIN",
                location_detail="主楼前台",
            ),
        )
        accept_task(db, pending_review.id, user03.id)
        submit_task_proof(db, pending_review.id, user03.id, _proof("资料已打印并送达前台。"))

        completed = create_task(
            db,
            user06.id,
            _payload(
                title="取外卖送到宿舍",
                description="外卖在南门，请送到 10 号公寓。",
                category=TaskCategory.FOOD,
                reward="9.00",
                building_code="BUPT_CANTEEN",
                location_detail="南门外卖架",
            ),
        )
        accept_task(db, completed.id, user02.id)
        submit_task_proof(db, completed.id, user02.id, _proof("已送到宿舍楼下。"))
        confirm_task(db, completed.id, user06.id)
        rate_task_partner(db, completed.id, user06.id, _rating(5, "送达很快，沟通清楚。"))
        rate_task_partner(db, completed.id, user02.id, _rating(5, "需求描述明确，确认及时。"))

        abandoned = create_task(
            db,
            user07.id,
            _payload(
                title="帮忙借一本教材",
                description="图书馆借一本数据结构教材，今天下午送到主楼。",
                category=TaskCategory.OTHER,
                reward="7.00",
                building_code="BUPT_LIBRARY",
                location_detail="图书馆二层",
            ),
        )
        accept_task(db, abandoned.id, user04.id)
        abandon_task(db, abandoned.id, user04.id)

        rejected = create_task(
            db,
            user08.id,
            _payload(
                title="代取实验器材",
                description="从主楼取一袋实验器材送到体育馆门口。",
                category=TaskCategory.MOVE,
                reward="18.00",
                building_code="BUPT_MAIN",
                location_detail="主楼 101",
            ),
        )
        accept_task(db, rejected.id, user05.id)
        submit_task_proof(db, rejected.id, user05.id, _proof("已放到体育馆门口。"))
        reject_task(db, rejected.id, user08.id, "未按约定位置放置，需要管理员处理。")
        resolve_dispute(
            db,
            task_id=rejected.id,
            payload=AdminResolveDisputeRequest(
                resolution="split",
                splitRatio=0.40,
                note="双方各承担一部分责任，按比例拆分。",
            ),
            admin_id=admin.id,
        )

        dispute_refund = create_task(
            db,
            user09.id,
            _payload(
                title="代取快递发生争议",
                description="取件码已提供，但接单人长时间未送达。",
                category=TaskCategory.PACKAGE,
                reward="15.00",
                building_code="BUPT_EXPRESS",
                location_detail="快递驿站",
            ),
        )
        accept_task(db, dispute_refund.id, user05.id)
        dispute_in_progress_task(db, dispute_refund.id, user09.id, "接单后长时间无响应。")
        resolve_dispute(
            db,
            task_id=dispute_refund.id,
            payload=AdminResolveDisputeRequest(
                resolution="refund",
                note="支持需求方，退回赏金。",
            ),
            admin_id=admin.id,
        )

        dispute_settle = create_task(
            db,
            user10.id,
            _payload(
                title="图书馆送资料争议",
                description="帮忙把报名表送到图书馆服务台。",
                category=TaskCategory.OTHER,
                reward="11.00",
                building_code="BUPT_LIBRARY",
                location_detail="服务台",
            ),
        )
        accept_task(db, dispute_settle.id, user03.id)
        dispute_in_progress_task(db, dispute_settle.id, user10.id, "需要确认是否已送达。")
        resolve_dispute(
            db,
            task_id=dispute_settle.id,
            payload=AdminResolveDisputeRequest(
                resolution="settle",
                note="接单方提供有效证明，正常结算。",
            ),
            admin_id=admin.id,
        )

        closed = create_task(
            db,
            admin.id,
            _payload(
                title="管理员关闭争议样例",
                description="用于演示后台自定义关闭争议。",
                category=TaskCategory.OTHER,
                reward="13.00",
                building_code="BUPT_MAIN",
                location_detail="主楼大厅",
            ),
        )
        accept_task(db, closed.id, user06.id)
        dispute_in_progress_task(db, closed.id, admin.id, "演示后台关闭流程。")
        resolve_dispute(
            db,
            task_id=closed.id,
            payload=AdminResolveDisputeRequest(
                resolution="close",
                note="自定义关闭并退款。",
            ),
            admin_id=admin.id,
        )

        cancelled = create_task(
            db,
            user01.id,
            _payload(
                title="临时取消的取件任务",
                description="需求方临时不需要取件，演示取消流程。",
                category=TaskCategory.PACKAGE,
                reward="6.00",
                building_code="BUPT_EXPRESS",
                location_detail="快递驿站",
            ),
        )
        cancel_task(db, cancelled.id, user01.id)

        expired = create_task(
            db,
            user02.id,
            _payload(
                title="已过期的跑腿任务",
                description="演示系统过期关闭和解冻资金。",
                category=TaskCategory.OTHER,
                reward="5.00",
                building_code="BUPT_GYM",
                location_detail="体育馆门口",
            ),
        )
        _set_deadline_past(db, expired.id)
        expire_task(db, expired.id, admin.id)

        review_task = create_task(
            db,
            user03.id,
            _payload(
                title="帮忙代写实验报告提纲",
                description="只需要整理提纲，不涉及提交作业，但关键词会触发复审。",
                category=TaskCategory.OTHER,
                reward="16.00",
                building_code="BUPT_LIBRARY",
                location_detail="图书馆讨论室",
            ),
        )
        _record_manual_moderation(
            db,
            admin=admin,
            user=user03,
            task_id=review_task.id,
            risk=ModerationResult.REVIEW,
            tags=["代写"],
            note="演示数据：关键词兜底命中低危词，进入管理员复审。",
        )

        _record_manual_moderation(
            db,
            admin=admin,
            user=user04,
            task_id=None,
            risk=ModerationResult.BLOCK,
            tags=["诈骗"],
            note="演示数据：高危内容被拦截，未创建任务。",
        )

        create_message(db, user_id=user04.id, task_id=in_progress.id, content="资料箱在宿舍楼下，麻烦轻拿。")
        create_message(db, user_id=user02.id, task_id=in_progress.id, content="收到，我十分钟后到。")
        create_message(db, user_id=user05.id, task_id=pending_review.id, content="完成后请上传证明。")
        create_message(db, user_id=user03.id, task_id=pending_review.id, content="证明已提交，请验收。")
        mark_conversation_read(db, user_id=user04.id, conversation_id=db.query(ChatConversation).filter_by(task_id=in_progress.id).one().id)

        create_notification(db, user_id=user01.id, type_="SYSTEM_NOTICE", title="演示数据已就绪", body="你可以浏览任务、钱包、通知和个人信用。")
        create_notification(db, user_id=admin.id, type_="MODERATION_REVIEW", title="有内容待复审", body="演示任务触发了 AI 审核复审。", related_task_id=review_task.id)
        create_notification(db, user_id=user02.id, type_="CHAT_MESSAGE", title="收到新聊天消息", body="你有任务内 IM 未读消息。", related_task_id=in_progress.id)
        db.commit()

        for user in [user01, user02, user03, user04, user05, user06, user07, user08, user09, user10]:
            recalculate_user_credit(db, user.id)
        list_recommended_tasks(db, user02.id, limit=5)

        print("Demo data generated from current service layer.")
        print(f"Admin account: {ADMIN_ACCOUNT} / {DEFAULT_PASSWORD}")
        print(f"User accounts: user01-user10 / {DEFAULT_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
