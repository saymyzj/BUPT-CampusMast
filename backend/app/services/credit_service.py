"""
文件说明：
这是信用与评价服务占位文件。
B 同学后续应在这里实现双分制加权算法、互评写入与信用快照刷新。
"""
from __future__ import annotations


def build_stub_rating() -> dict:
    return {
        "id": "rating_stub",
        "taskId": "task_stub",
        "fromUserId": "u_from",
        "toUserId": "u_to",
        "score": 5,
        "comment": "占位评价",
        "createdAt": "2026-04-14T00:00:00Z",
    }

