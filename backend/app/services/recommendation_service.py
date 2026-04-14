"""
文件说明：
这是智能推荐服务占位文件。
B 同学后续应在这里实现规则加权推荐，并结合 Redis 做短期缓存。
"""
from __future__ import annotations

from app.services.task_service import build_stub_task


def build_stub_recommendation() -> dict:
    return {
        "task": build_stub_task(),
        "scoreTotal": 88.5,
        "scoreCategory": 22.0,
        "scoreDistance": 21.5,
        "scoreSuccessRate": 23.0,
        "scoreActiveTime": 22.0,
    }

