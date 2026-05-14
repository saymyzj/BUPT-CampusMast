"""
文件说明：
这是 AI 审核服务占位文件。
组长后续应在这里接入 DeepSeek，同步返回 ALLOW / REVIEW / BLOCK 结果。
"""
from __future__ import annotations


def build_stub_moderation_record() -> dict:
    return {
        "id": "mod_stub",
        "taskId": "task_stub",
        "userId": "u_stub",
        "provider": "DEEPSEEK",
        "riskLevel": "ALLOW",
        "hitTags": [],
        "adminReviewStatus": "PENDING",
        "adminReviewNote": None,
        "createdAt": "2026-04-14T00:00:00Z",
    }

