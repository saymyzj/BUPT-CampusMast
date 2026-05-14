"""
文件说明：
这是钱包模块的 Schema 文件。
用于统一余额、流水以及充值提现请求结构。
"""
from __future__ import annotations

from pydantic import BaseModel


class WalletResponse(BaseModel):
    available: str
    frozen: str
    total: str


class TransactionResponse(BaseModel):
    id: str
    type: str
    amount: str
    balanceAfter: str
    relatedTaskId: str | None = None
    description: str
    createdAt: str


class WalletAmountRequest(BaseModel):
    amount: str

