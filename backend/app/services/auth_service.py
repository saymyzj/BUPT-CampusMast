"""
文件说明：
这是认证服务占位文件。
组长后续应在这里继续实现注册、登录、刷新令牌和当前用户读取逻辑。
"""
from __future__ import annotations

from app.utils.jwt import create_token


def build_stub_auth_payload() -> dict:
    return {
        "accessToken": create_token("u_stub", 15),
        "refreshToken": create_token("u_stub_refresh", 60 * 24),
        "user": {
            "id": "u_stub",
            "studentEmail": "stub@bupt.edu.cn",
            "nickname": "脚手架用户",
            "role": "ADMIN",
            "requesterCreditScore": 100,
            "helperCreditScore": 100,
            "overallCreditScore": 100,
            "avatarUrl": None,
            "defaultBuildingCode": None,
        },
    }

