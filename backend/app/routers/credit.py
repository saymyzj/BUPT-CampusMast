from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.credit_service import (
    CreditError,
    get_credit_profile_with_stats,
    list_received_ratings,
    rating_to_dict,
)
from app.utils.response import failure, success

router = APIRouter(prefix="/credit", tags=["Credit"])


def _error_response(exc: CreditError, status_code: int = status.HTTP_404_NOT_FOUND) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=failure(exc.code, exc.message))


@router.get("/profile/me")
def get_my_credit_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    try:
        profile = get_credit_profile_with_stats(db, user.id)
    except CreditError as exc:
        return _error_response(exc)
    return success(profile)


@router.get("/profile/{user_id}")
def get_user_credit_profile(
    user_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        profile = get_credit_profile_with_stats(db, user_id)
    except CreditError as exc:
        return _error_response(exc)
    return success(profile)


@router.get("/ratings/{user_id}")
def list_user_received_ratings(
    user_id: str,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        ratings = list_received_ratings(db, user_id)
    except CreditError as exc:
        return _error_response(exc)
    return success([rating_to_dict(row) for row in ratings])
