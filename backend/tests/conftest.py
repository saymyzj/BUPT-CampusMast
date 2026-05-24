"""
文件说明：
这是后端测试公共夹具文件。
当前先提供 FastAPI TestClient，后续你和 B 同学可以在这里继续补数据库、Redis
 和鉴权相关测试夹具。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

