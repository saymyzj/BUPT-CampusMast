"""
文件说明：
这是智能推荐路由占位文件。
B 同学后续应在这里提供推荐任务列表与推荐得分解释接口。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.services.recommendation_service import RecommendationError, list_recommended_tasks
from app.utils.response import failure, success

router = APIRouter(prefix="/recommendations", tags=["Recommendation"])


def _error_response(exc: RecommendationError, status_code: int = status.HTTP_404_NOT_FOUND) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=failure(exc.code, exc.message))


@router.get("/tasks")
def list_recommended_task_route(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        rows = list_recommended_tasks(db, current_user["id"], limit=limit)
    except RecommendationError as exc:
        return _error_response(exc)
    return success(rows)
