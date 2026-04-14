"""
文件说明：
这是后端最小冒烟测试文件。
脚手架阶段只验证应用能启动和健康检查接口存在，后续 B 同学可继续新增状态机、
 钱包事务、推荐与审核相关测试。
"""
from __future__ import annotations


def test_healthcheck(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
