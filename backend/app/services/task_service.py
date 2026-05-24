"""
文件说明：
这是任务服务占位文件。
B 同学后续应在这里填充状态机、并发接单、争议处理和任务详情聚合逻辑。
"""
from __future__ import annotations


def build_stub_task() -> dict:
    return {
        "id": "task_stub",
        "title": "脚手架任务",
        "description": "这是一个用于脚手架联调的占位任务。",
        "category": "package",
        "reward": "10.00",
        "status": "PENDING",
        "buildingCode": "BUPT_MAIN",
        "locationDetail": "主楼门口",
        "requester": {"id": "u_requester", "nickname": "需求方", "overallCreditScore": 95},
        "helper": None,
        "moderationResult": "ALLOW",
        "needsAdminReview": False,
    }

