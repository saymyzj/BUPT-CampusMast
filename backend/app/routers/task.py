from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.schemas.credit import RatingCreateRequest
from app.schemas.task import TaskCreateRequest, TaskProofRequest, TaskRejectRequest
from app.services.credit_service import CreditError, rate_task_partner, rating_to_dict
from app.services.task_service import (
    TaskError,
    accept_task,
    abandon_task,
    cancel_task,
    confirm_task,
    create_task as create_task_service,
    get_task_by_id,
    list_pending_tasks,
    list_user_tasks,
    reject_task,
    submit_task_proof,
    task_to_dict,
)
from app.utils.response import failure, success

router = APIRouter(prefix="/tasks", tags=["Task"])


def _error_response(exc: TaskError, status_code: int = status.HTTP_409_CONFLICT) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=failure(exc.code, exc.message),
    )


def _credit_error_response(exc: CreditError, status_code: int = status.HTTP_409_CONFLICT) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=failure(exc.code, exc.message),
    )


@router.get("")
def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    keyword: str | None = Query(None),
    buildingCode: str | None = Query(None),
    nearBuildingCode: str | None = Query(None),
    sortBy: str | None = Query(None, pattern="^(newest|rewardDesc|rewardAsc|deadlineAsc|distanceAsc)$"),
    db: Session = Depends(get_db),
) -> dict:
    try:
        rows, total = list_pending_tasks(
            db,
            page=page,
            limit=limit,
            category=category,
            keyword=keyword,
            building_code=buildingCode,
            near_building_code=nearBuildingCode,
            sort_by=sortBy,
        )
    except TaskError as exc:
        return _error_response(exc)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = create_task_service(db, current_user["id"], payload)
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.get("/my/posted")
def list_my_posted_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        rows, total = list_user_tasks(
            db,
            current_user["id"],
            role="posted",
            page=page,
            limit=limit,
            status_filter=status_filter,
        )
    except TaskError as exc:
        return _error_response(exc)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.get("/my/accepted")
def list_my_accepted_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        rows, total = list_user_tasks(
            db,
            current_user["id"],
            role="accepted",
            page=page,
            limit=limit,
            status_filter=status_filter,
        )
    except TaskError as exc:
        return _error_response(exc)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        task = get_task_by_id(db, task_id)
    except TaskError as exc:
        return _error_response(exc, status.HTTP_404_NOT_FOUND)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/accept")
def accept_task_route(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = accept_task(db, task_id, current_user["id"])
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/submit")
def submit_task_route(
    task_id: str,
    payload: TaskProofRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = submit_task_proof(db, task_id, current_user["id"], payload)
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/confirm")
def confirm_task_route(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = confirm_task(db, task_id, current_user["id"])
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/reject")
def reject_task_route(
    task_id: str,
    payload: TaskRejectRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = reject_task(db, task_id, current_user["id"], payload.reason)
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/cancel")
def cancel_task_route(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = cancel_task(db, task_id, current_user["id"])
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.patch("/{task_id}/abandon")
def abandon_task_route(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        task = abandon_task(db, task_id, current_user["id"])
    except TaskError as exc:
        return _error_response(exc)
    return success(task_to_dict(db, task, include_logs=True))


@router.post("/{task_id}/rating", status_code=status.HTTP_201_CREATED)
def rate_task_route(
    task_id: str,
    payload: RatingCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        rating = rate_task_partner(db, task_id, current_user["id"], payload)
    except CreditError as exc:
        return _credit_error_response(exc)
    return success(rating_to_dict(rating))
