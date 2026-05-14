from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.schemas.wallet import WalletAmountRequest
from app.services.wallet_service import (
    WalletError,
    get_or_create_wallet,
    list_transactions as list_wallet_transactions,
    top_up,
    wallet_to_dict,
    withdraw,
)
from app.utils.response import failure, success

router = APIRouter(prefix="/wallet", tags=["Wallet"])


def _error_response(exc: WalletError, status_code: int = status.HTTP_409_CONFLICT) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=failure(exc.code, exc.message),
    )


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    wallet = get_or_create_wallet(db, current_user["id"])
    db.commit()
    db.refresh(wallet)
    return success(wallet_to_dict(wallet))


@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        rows, total = list_wallet_transactions(db, current_user["id"], page=page, limit=limit)
    except WalletError as exc:
        return _error_response(exc)
    return success(rows, meta={"page": page, "limit": limit, "total": total})


@router.post("/topup")
def topup_wallet(
    payload: WalletAmountRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        wallet = top_up(db, current_user["id"], payload.amount)
    except WalletError as exc:
        return _error_response(exc)
    return success(wallet_to_dict(wallet))


@router.post("/withdraw")
def withdraw_wallet(
    payload: WalletAmountRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    try:
        wallet = withdraw(db, current_user["id"], payload.amount)
    except WalletError as exc:
        return _error_response(exc)
    return success(wallet_to_dict(wallet))
