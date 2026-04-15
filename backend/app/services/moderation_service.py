"""
文件说明：
这是 AI 审核服务文件。
负责审核结果生成、审核记录留痕、用户侧查询与管理员复审。
"""
from __future__ import annotations

from typing import Any

import httpx
from fastapi import status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import AdminReviewStatus, ModerationResult
from app.models.moderation import ModerationRecord
from app.schemas.admin import AdminReviewModerationRequest
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.serialization import json_dumps, json_loads, to_iso8601

BLOCK_KEYWORDS = ["诈骗", "毒品", "枪", "约炮", "裸聊", "色情", "违法"]
REVIEW_KEYWORDS = ["代写", "外挂", "刷单", "辱骂", "赌博", "高仿", "办证"]


def list_user_moderation_records(db: Session, user_id: str) -> list[dict[str, Any]]:
    records = (
        db.query(ModerationRecord)
        .filter(ModerationRecord.user_id == user_id)
        .order_by(ModerationRecord.created_at.desc())
        .all()
    )
    return [serialize_moderation_record(item) for item in records]


def list_moderation_records(
    db: Session,
    *,
    page: int,
    limit: int,
    risk_level: str | None = None,
    admin_review_status: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    query = db.query(ModerationRecord)
    if risk_level:
        query = query.filter(ModerationRecord.risk_level == risk_level)
    if admin_review_status:
        query = query.filter(ModerationRecord.admin_review_status == admin_review_status)

    total = query.count()
    rows = query.order_by(ModerationRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return [serialize_moderation_record(item) for item in rows], total


def review_moderation_record(
    db: Session,
    *,
    record_id: str,
    payload: AdminReviewModerationRequest,
    admin_id: str,
) -> dict[str, Any]:
    record = db.get(ModerationRecord, record_id)
    if record is None:
        raise AppError("MODERATION_RECORD_NOT_FOUND", "审核记录不存在", status.HTTP_404_NOT_FOUND)

    if payload.decision.lower() == "approve":
        record.admin_review_status = AdminReviewStatus.APPROVED.value
    elif payload.decision.lower() == "reject":
        record.admin_review_status = AdminReviewStatus.REJECTED.value
    else:
        raise AppError("INVALID_REVIEW_DECISION", "无效的复审决策", status.HTTP_400_BAD_REQUEST)

    record.admin_review_note = payload.note
    db.commit()
    db.refresh(record)
    return serialize_moderation_record(record)


def moderate_task_content(
    *,
    user_id: str,
    title: str,
    description: str,
    image_urls: list[str] | None = None,
) -> tuple[ModerationResult, list[str], str]:
    text = f"{title}\n{description}".lower()
    hit_tags = [word for word in BLOCK_KEYWORDS if word in text]
    if hit_tags:
        return ModerationResult.BLOCK, hit_tags, "本地规则命中高危关键词"

    review_hits = [word for word in REVIEW_KEYWORDS if word in text]
    if review_hits:
        return ModerationResult.REVIEW, review_hits, "本地规则命中待复审关键词"

    if not settings.deepseek_api_key:
        return ModerationResult.REVIEW, ["deepseek-unavailable"], "未配置 DeepSeek，按 REVIEW 兜底"

    try:
        response = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是校园任务审核助手。仅返回 ALLOW、REVIEW、BLOCK 三个结果中的一个。",
                    },
                    {
                        "role": "user",
                        "content": json_dumps(
                            {"title": title, "description": description, "imageUrls": image_urls or []}
                        ),
                    },
                ],
            },
            timeout=settings.deepseek_timeout_seconds,
        )
        response.raise_for_status()
        content = (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "REVIEW")
            .strip()
            .upper()
        )
        result = ModerationResult(content) if content in ModerationResult._value2member_map_ else ModerationResult.REVIEW
        return result, [], f"DeepSeek 返回 {result.value}"
    except Exception:
        return ModerationResult.REVIEW, ["deepseek-timeout"], "DeepSeek 调用失败，按 REVIEW 兜底"


def create_moderation_record(
    db: Session,
    *,
    user_id: str,
    task_id: str | None,
    risk_level: ModerationResult,
    hit_tags: list[str],
    model_output: str,
) -> ModerationRecord:
    record = ModerationRecord(
        id=generate_id("mod"),
        task_id=task_id,
        user_id=user_id,
        provider="DEEPSEEK",
        risk_level=risk_level.value,
        hit_tags=json_dumps(hit_tags),
        model_output=model_output,
        admin_review_status=AdminReviewStatus.PENDING.value,
    )
    db.add(record)
    db.flush()
    return record


def serialize_moderation_record(record: ModerationRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "taskId": record.task_id,
        "userId": record.user_id,
        "provider": record.provider,
        "riskLevel": record.risk_level,
        "hitTags": json_loads(record.hit_tags, []),
        "adminReviewStatus": record.admin_review_status,
        "adminReviewNote": record.admin_review_note,
        "createdAt": to_iso8601(record.created_at),
    }
