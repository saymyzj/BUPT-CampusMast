"""
文件说明：
这是地图服务占位文件。
组长后续应在这里补充楼宇点位读取、距离计算和附近任务查询逻辑。
"""
from __future__ import annotations


def build_stub_building() -> dict:
    return {
        "code": "BUPT_MAIN",
        "name": "北邮主楼",
        "campusZone": "校本部",
        "xCoord": 120.0,
        "yCoord": 280.0,
    }

