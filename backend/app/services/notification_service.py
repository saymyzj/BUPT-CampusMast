"""
文件说明：
这是通知服务占位文件。
组长后续应把通知落库、未读统计和 WebSocket 推送统一收口到这里。
"""
from __future__ import annotations


def build_stub_notification() -> dict:
    return {
        "id": "notify_stub",
        "type": "SYSTEM_NOTICE",
        "title": "脚手架通知",
        "body": "这是一个用于前后端联调的通知占位。",
        "relatedTaskId": None,
        "isRead": False,
        "createdAt": "2026-04-14T00:00:00Z",
    }

