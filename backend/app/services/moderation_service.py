"""
文件说明：
这是 AI 审核服务文件。
负责审核结果生成、审核记录留痕、用户侧查询与管理员复审。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import AdminReviewStatus, ModerationResult, TaskStatus
from app.models.moderation import ModerationRecord
from app.models.task import Task, TaskLog
from app.schemas.admin import AdminReviewModerationRequest
from app.services.wallet_service import new_id, unfreeze_funds
from app.utils.errors import AppError
from app.utils.ids import generate_id
from app.utils.serialization import json_dumps, json_loads, to_iso8601

BLOCK_KEYWORDS = ["诈骗", "毒品", "枪", "约炮", "裸聊", "色情", "违法"]
REVIEW_KEYWORDS = ["代写", "外挂", "刷单", "辱骂", "赌博", "高仿", "办证"]
VALID_RISK_HINTS = {"LOW", "MEDIUM", "HIGH"}


@dataclass(frozen=True)
class ModerationDecision:
    result: ModerationResult
    hit_tags: list[str]
    reason: str
    ai_result: str
    risk_hint: str | None = None
    provider: str = "DEEPSEEK"


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
        _sync_task_after_admin_review(db, record, approved=True, admin_id=admin_id, note=payload.note)
    elif payload.decision.lower() == "reject":
        record.admin_review_status = AdminReviewStatus.REJECTED.value
        _sync_task_after_admin_review(db, record, approved=False, admin_id=admin_id, note=payload.note)
    else:
        raise AppError("INVALID_REVIEW_DECISION", "无效的复审决策", status.HTTP_400_BAD_REQUEST)

    record.admin_review_note = payload.note
    record.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(record)
    return serialize_moderation_record(record)


def moderate_task_content(
    *,
    user_id: str,
    title: str,
    description: str,
    image_urls: list[str] | None = None,
) -> ModerationDecision:
    block_hits = _sensitive_keyword_hits(title, description)
    if block_hits:
        return ModerationDecision(
            result=ModerationResult.BLOCK,
            hit_tags=block_hits,
            reason="本地敏感词规则命中，任务不予发布",
            ai_result="sensitive_keyword_block",
            risk_hint="HIGH",
            provider="LOCAL_KEYWORD",
        )

    if settings.deepseek_api_key:
        try:
            response = httpx.post(
                f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是校园任务审核助手。仅返回 JSON："
                                '{"decision":"accept|reject|refuse","risk":"low|medium|high","reason":"简短原因"}。'
                                "accept 表示可直接发布，reject 表示拒绝发布，refuse 表示可先发布但需人工复审。"
                            ),
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
            )
            return _parse_ai_decision(content)
        except Exception:
            pass

    fallback_result, hit_tags, reason = _keyword_fallback(title, description)
    if fallback_result == ModerationResult.BLOCK:
        ai_result = "sensitive_keyword_block"
        risk_hint = "HIGH"
    elif fallback_result == ModerationResult.REVIEW:
        ai_result = "refuse"
        risk_hint = "MEDIUM"
    else:
        return ModerationDecision(
            result=ModerationResult.REVIEW,
            hit_tags=["deepseek-unavailable"],
            reason="DeepSeek 未配置或调用失败，关键词未命中，按 refuse/MEDIUM 进入人工复审",
            ai_result="refuse",
            risk_hint="MEDIUM",
            provider="FALLBACK",
        )
    return ModerationDecision(
        result=fallback_result,
        hit_tags=hit_tags,
        reason=reason,
        ai_result=ai_result,
        risk_hint=risk_hint,
        provider="LOCAL_KEYWORD",
    )


def _sensitive_keyword_hits(title: str, description: str) -> list[str]:
    text = f"{title}\n{description}".lower()
    return [word for word in BLOCK_KEYWORDS if word in text]


def _keyword_fallback(title: str, description: str) -> tuple[ModerationResult, list[str], str]:
    text = f"{title}\n{description}".lower()
    hit_tags = _sensitive_keyword_hits(title, description)
    if hit_tags:
        return ModerationResult.BLOCK, hit_tags, "本地规则命中高危关键词"

    review_hits = [word for word in REVIEW_KEYWORDS if word in text]
    if review_hits:
        return ModerationResult.REVIEW, review_hits, "本地规则命中待复审关键词"

    return ModerationResult.ALLOW, [], "关键词兜底未命中风险"


def _parse_ai_decision(content: str) -> ModerationDecision:
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        lowered = content.strip().lower()
        if lowered in {"accept", "allow"}:
            parsed = {"decision": "accept", "reason": content}
        elif lowered in {"reject", "block"}:
            parsed = {"decision": "reject", "risk": "high", "reason": content}
        elif lowered in {"refuse", "review"}:
            parsed = {"decision": "refuse", "risk": "medium", "reason": content}

    decision = str(parsed.get("decision", "refuse")).strip().lower()
    risk_hint = str(parsed.get("risk", "medium")).strip().upper()
    if risk_hint not in VALID_RISK_HINTS:
        risk_hint = "MEDIUM"
    reason = str(parsed.get("reason") or content or "AI 未返回明确理由")

    if decision == "accept":
        return ModerationDecision(ModerationResult.ALLOW, [], reason, "accept")
    if decision == "reject":
        return ModerationDecision(ModerationResult.BLOCK, [f"risk:{risk_hint}"], reason, "reject", risk_hint)
    return ModerationDecision(ModerationResult.REVIEW, [f"risk:{risk_hint}"], reason, "refuse", risk_hint)


def normalize_moderation_decision(raw: Any) -> ModerationDecision:
    if isinstance(raw, ModerationDecision):
        return raw
    if isinstance(raw, tuple):
        result, hit_tags, reason = raw[:3]
        if not isinstance(result, ModerationResult):
            result = ModerationResult(result)
        risk_hint = raw[3] if len(raw) > 3 else None
        ai_result = "accept" if result == ModerationResult.ALLOW else "reject" if result == ModerationResult.BLOCK else "refuse"
        return ModerationDecision(result, list(hit_tags), str(reason), ai_result, risk_hint)
    raise TypeError("Invalid moderation decision")


def create_moderation_record(
    db: Session,
    *,
    user_id: str,
    task_id: str | None,
    risk_level: ModerationResult | str,
    hit_tags: list[str],
    model_output: str,
    risk_hint: str | None = None,
    ai_result: str | None = None,
    provider: str = "DEEPSEEK",
    admin_review_status: str | None = None,
) -> ModerationRecord:
    if not isinstance(risk_level, ModerationResult):
        risk_level = ModerationResult(risk_level)
    status_by_result = {
        ModerationResult.ALLOW: AdminReviewStatus.APPROVED.value,
        ModerationResult.BLOCK: AdminReviewStatus.REJECTED.value,
        ModerationResult.REVIEW: AdminReviewStatus.PENDING.value,
    }
    tags = hit_tags.copy()
    if risk_hint and not any(tag.startswith("risk:") for tag in tags):
        tags.append(f"risk:{risk_hint.upper()}")
    output = json_dumps(
        {
            "aiResult": ai_result,
            "riskHint": risk_hint,
            "reason": model_output,
        }
    )
    record = ModerationRecord(
        id=generate_id("mod"),
        task_id=task_id,
        user_id=user_id,
        provider=provider,
        risk_level=risk_level.value,
        hit_tags=json_dumps(tags),
        model_output=output,
        admin_review_status=admin_review_status or status_by_result[risk_level],
    )
    db.add(record)
    db.flush()
    return record


def serialize_moderation_record(record: ModerationRecord) -> dict[str, Any]:
    try:
        output = json_loads(record.model_output, {})
    except json.JSONDecodeError:
        output = {}
    try:
        hit_tags = json_loads(record.hit_tags, [])
    except json.JSONDecodeError:
        hit_tags = []
    risk_hint = output.get("riskHint") if isinstance(output, dict) else None
    if risk_hint is None:
        risk_tags = [tag for tag in hit_tags if isinstance(tag, str) and tag.startswith("risk:")]
        risk_hint = risk_tags[0].split(":", 1)[1] if risk_tags else None
    return {
        "id": record.id,
        "taskId": record.task_id,
        "userId": record.user_id,
        "provider": record.provider,
        "riskLevel": record.risk_level,
        "hitTags": hit_tags,
        "aiResult": output.get("aiResult") if isinstance(output, dict) else None,
        "riskHint": risk_hint,
        "modelOutput": output.get("reason") if isinstance(output, dict) else record.model_output,
        "adminReviewStatus": record.admin_review_status,
        "adminReviewNote": record.admin_review_note,
        "createdAt": to_iso8601(record.created_at),
        "reviewedAt": to_iso8601(record.reviewed_at),
    }


def _sync_task_after_admin_review(
    db: Session,
    record: ModerationRecord,
    *,
    approved: bool,
    admin_id: str,
    note: str | None,
) -> None:
    if record.task_id is None:
        return
    task = db.get(Task, record.task_id)
    if task is None:
        return
    task.needs_admin_review = False
    if approved:
        return
    if task.status != TaskStatus.PENDING:
        return
    from_status = task.status
    task.status = TaskStatus.CLOSED_BY_ADMIN
    task.version += 1
    db.add(
        TaskLog(
            id=new_id("log"),
            task_id=task.id,
            from_status=from_status,
            to_status=TaskStatus.CLOSED_BY_ADMIN,
            actor_id=admin_id,
            remark=note or "管理员复审未通过，任务下架",
        )
    )
    unfreeze_funds(db, task.requester_id, task.reward, related_task_id=task.id, description="审核下架退款")
