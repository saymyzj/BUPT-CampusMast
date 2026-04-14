"""
文件说明：
这是任务路由占位文件。
B 同学后续应在这里把创建、接单、提交完成、验收、争议等 HTTP 接口全部填充完整。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.task_service import build_stub_task
from app.utils.response import success

router = APIRouter(prefix="/tasks", tags=["Task"])


@router.get("")
def list_tasks() -> dict:
    return success([build_stub_task()], meta={"page": 1, "limit": 20, "total": 1})


@router.post("")
def create_task() -> dict:
    return success(build_stub_task())


@router.get("/{task_id}")
def get_task(task_id: str) -> dict:
    task = build_stub_task()
    task["id"] = task_id
    task["logs"] = []
    task["proofNote"] = None
    task["proofImageUrls"] = []
    return success(task)

