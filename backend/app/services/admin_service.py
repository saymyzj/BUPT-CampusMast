"""
文件说明：
这是后台服务占位文件。
组长后续应在这里统一实现用户管理、任务管理、审核管理、首页配置和统计逻辑。
"""
from __future__ import annotations


def build_stub_admin_stats() -> dict:
    return {
        "userCount": 0,
        "taskCount": 0,
        "messageCount": 0,
        "moderationReviewPending": 0,
    }

