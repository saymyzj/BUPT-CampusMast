"""
文件说明：
这是钱包路由占位文件。
B 同学后续应在这里补充余额、流水、充值和提现接口逻辑。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.wallet_service import build_stub_wallet
from app.utils.response import success

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance")
def get_balance() -> dict:
    return success(build_stub_wallet())


@router.get("/transactions")
def list_transactions() -> dict:
    return success([], meta={"page": 1, "limit": 20, "total": 0})

