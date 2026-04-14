"""
文件说明：
这是系统配置服务占位文件。
组长后续应在这里接入信用权重、审核阈值、推荐参数和首页内容的统一读写逻辑。
"""
from __future__ import annotations


def build_stub_config_item() -> dict:
    return {
        "configKey": "helperCreditThreshold",
        "configGroup": "credit",
        "configValue": {"value": 60},
        "description": "接单最低信用分",
        "updatedAt": "2026-04-14T00:00:00Z",
    }

