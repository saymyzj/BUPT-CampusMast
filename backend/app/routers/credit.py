"""
文件说明：
这是信用与评价路由占位文件。
B 同学后续应在这里补充互评提交和信用分快照查询接口。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.credit_service import build_stub_rating
from app.utils.response import success

router = APIRouter(prefix="/credit", tags=["Credit"])


@router.post("/ratings")
def create_rating() -> dict:
    return success(build_stub_rating())

