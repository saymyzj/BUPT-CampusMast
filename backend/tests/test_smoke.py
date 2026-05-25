"""
文件说明：
这是后端最小冒烟测试文件。
本地验收版只验证应用能启动和健康检查接口存在，业务回归由各模块测试覆盖。
"""
from __future__ import annotations


def test_healthcheck(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
