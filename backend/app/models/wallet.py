"""
文件说明：
这是钱包与流水模型文件。
它支撑冻结、解冻、结算和拆分结算事务。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import TransactionType


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(25), ForeignKey("users.id"), unique=True, nullable=False)
    available: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    frozen: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("settlement_key", name="uq_transactions_settlement_key"),
        Index("ix_transactions_wallet_id_created_at", "wallet_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(25), primary_key=True)
    wallet_id: Mapped[str] = mapped_column(String(25), ForeignKey("wallets.id"), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String(25))
    settlement_key: Mapped[str | None] = mapped_column(String(25))
    description: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
