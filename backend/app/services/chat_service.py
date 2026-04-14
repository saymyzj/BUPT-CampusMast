"""
文件说明：
这是聊天服务占位文件。
组长后续应把会话创建、消息持久化、离线未读和已读同步逻辑统一放在这里。
"""
from __future__ import annotations


def build_stub_message() -> dict:
    return {
        "id": "msg_stub",
        "conversationId": "conv_stub",
        "senderId": "u_stub",
        "content": "脚手架消息",
        "createdAt": "2026-04-14T00:00:00Z",
    }

