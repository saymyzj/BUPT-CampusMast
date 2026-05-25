from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.wallet import Transaction, Wallet

MONEY_QUANT = Decimal("0.01")


class WalletError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


TASK_SETTLEMENT_TYPES = {
    TransactionType.SETTLE_OUT,
    TransactionType.SETTLE_IN,
    TransactionType.SETTLE_SPLIT,
}


def money(value: str | int | Decimal) -> Decimal:
    if isinstance(value, float):
        raise WalletError("INVALID_AMOUNT", "Amount must not be a float")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise WalletError("INVALID_AMOUNT", "Amount must be a valid decimal") from exc
    if isinstance(value, str) and parsed.as_tuple().exponent < -2:
        raise WalletError("INVALID_AMOUNT_PRECISION", "Amount must have at most two decimal places")
    return parsed.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def money_text(value: str | int | Decimal) -> str:
    return f"{money(value):.2f}"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def get_wallet(db: Session, user_id: str, *, for_update: bool = False) -> Wallet:
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()
    wallet = db.execute(stmt).scalar_one_or_none()
    if wallet is None:
        raise WalletError("WALLET_NOT_FOUND", "Wallet not found")
    return wallet


def get_or_create_wallet(db: Session, user_id: str, *, for_update: bool = False) -> Wallet:
    stmt = select(Wallet).where(Wallet.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()
    wallet = db.execute(stmt).scalar_one_or_none()
    if wallet is not None:
        return wallet

    wallet = Wallet(id=new_id("wallet"), user_id=user_id, available=Decimal("0.00"), frozen=Decimal("0.00"))
    db.add(wallet)
    db.flush()
    return wallet


def wallet_to_dict(wallet: Wallet) -> dict:
    available = money(wallet.available)
    frozen = money(wallet.frozen)
    return {
        "available": money_text(available),
        "frozen": money_text(frozen),
        "total": money_text(available + frozen),
    }


def transaction_to_dict(transaction: Transaction) -> dict:
    return {
        "id": transaction.id,
        "type": transaction.type.value,
        "amount": money_text(transaction.amount),
        "balanceAfter": money_text(transaction.balance_after),
        "relatedTaskId": transaction.related_task_id,
        "description": transaction.description or "",
        "createdAt": transaction.created_at.isoformat() if transaction.created_at else "",
    }


def _ensure_positive(amount: Decimal) -> None:
    if amount <= 0:
        raise WalletError("INVALID_AMOUNT", "Amount must be positive")


def _ensure_non_negative(wallet: Wallet) -> None:
    if money(wallet.available) < 0 or money(wallet.frozen) < 0:
        raise WalletError("NEGATIVE_BALANCE", "Wallet balance cannot be negative")


def _ensure_no_task_settlement(db: Session, related_task_id: str) -> None:
    exists = (
        db.query(Transaction)
        .filter(
            Transaction.related_task_id == related_task_id,
            Transaction.type.in_(TASK_SETTLEMENT_TYPES),
        )
        .first()
    )
    if exists is not None:
        raise WalletError("DUPLICATE_TASK_SETTLEMENT", "Task reward has already been settled")


def _is_duplicate_task_settlement_integrity_error(exc: IntegrityError) -> bool:
    message = str(exc.orig).lower()
    return "uq_transactions_settlement_key" in message or (
        "duplicate" in message and "settlement_key" in message
    ) or (
        "unique constraint failed" in message and "transactions.settlement_key" in message
    )


def _record_transaction(
    db: Session,
    wallet: Wallet,
    tx_type: TransactionType,
    amount: Decimal,
    *,
    related_task_id: str | None = None,
    settlement_key: str | None = None,
    description: str | None = None,
) -> Transaction:
    _ensure_non_negative(wallet)
    transaction = Transaction(
        id=new_id("tx"),
        wallet_id=wallet.id,
        type=tx_type,
        amount=amount,
        balance_after=money(Decimal(str(wallet.available)) + Decimal(str(wallet.frozen))),
        related_task_id=related_task_id,
        settlement_key=settlement_key,
        description=description or tx_type.value,
    )
    db.add(transaction)
    db.flush()
    return transaction


def top_up(db: Session, user_id: str, amount: str | Decimal) -> Wallet:
    value = money(amount)
    _ensure_positive(value)
    try:
        wallet = get_or_create_wallet(db, user_id)
        wallet.available = money(Decimal(str(wallet.available)) + value)
        _record_transaction(db, wallet, TransactionType.TOP_UP, value, description="钱包充值")
        db.commit()
        db.refresh(wallet)
        return wallet
    except Exception:
        db.rollback()
        raise


def withdraw(db: Session, user_id: str, amount: str | Decimal) -> Wallet:
    value = money(amount)
    _ensure_positive(value)
    try:
        wallet = get_wallet(db, user_id, for_update=True)
        if money(wallet.available) < value:
            raise WalletError("INSUFFICIENT_AVAILABLE_BALANCE", "Insufficient available balance")
        wallet.available = money(Decimal(str(wallet.available)) - value)
        _record_transaction(db, wallet, TransactionType.WITHDRAW, value, description="钱包提现")
        db.commit()
        db.refresh(wallet)
        return wallet
    except Exception:
        db.rollback()
        raise


def freeze_funds(
    db: Session,
    user_id: str,
    amount: str | Decimal,
    *,
    related_task_id: str | None = None,
    description: str = "Task reward frozen",
) -> Wallet:
    value = money(amount)
    _ensure_positive(value)
    wallet = get_wallet(db, user_id, for_update=True)
    if money(wallet.available) < value:
        raise WalletError("INSUFFICIENT_AVAILABLE_BALANCE", "Insufficient available balance")
    wallet.available = money(Decimal(str(wallet.available)) - value)
    wallet.frozen = money(Decimal(str(wallet.frozen)) + value)
    _record_transaction(
        db,
        wallet,
        TransactionType.FREEZE,
        value,
        related_task_id=related_task_id,
        description=description,
    )
    return wallet


def unfreeze_funds(
    db: Session,
    user_id: str,
    amount: str | Decimal,
    *,
    related_task_id: str | None = None,
    description: str = "Task reward unfrozen",
) -> Wallet:
    value = money(amount)
    _ensure_positive(value)
    wallet = get_wallet(db, user_id, for_update=True)
    if money(wallet.frozen) < value:
        raise WalletError("INSUFFICIENT_FROZEN_BALANCE", "Insufficient frozen balance")
    wallet.available = money(Decimal(str(wallet.available)) + value)
    wallet.frozen = money(Decimal(str(wallet.frozen)) - value)
    _record_transaction(
        db,
        wallet,
        TransactionType.UNFREEZE,
        value,
            related_task_id=related_task_id,
            description=description,
    )
    return wallet


def settle_reward(
    db: Session,
    requester_id: str,
    helper_id: str,
    amount: str | Decimal,
    *,
    related_task_id: str,
) -> tuple[Wallet, Wallet]:
    try:
        value = money(amount)
        _ensure_positive(value)
        _ensure_no_task_settlement(db, related_task_id)
        requester_wallet = get_wallet(db, requester_id, for_update=True)
        helper_wallet = get_or_create_wallet(db, helper_id, for_update=True)
        if money(requester_wallet.frozen) < value:
            raise WalletError("INSUFFICIENT_FROZEN_BALANCE", "Insufficient frozen balance")

        requester_wallet.frozen = money(Decimal(str(requester_wallet.frozen)) - value)
        _record_transaction(
            db,
            requester_wallet,
            TransactionType.SETTLE_OUT,
            value,
            related_task_id=related_task_id,
            settlement_key=related_task_id,
            description="Task reward settled out to helper",
        )

        helper_wallet.available = money(Decimal(str(helper_wallet.available)) + value)
        _record_transaction(
            db,
            helper_wallet,
            TransactionType.SETTLE_IN,
            value,
            related_task_id=related_task_id,
            description="Task reward settled in from requester",
        )
        return requester_wallet, helper_wallet
    except IntegrityError as exc:
        db.rollback()
        if _is_duplicate_task_settlement_integrity_error(exc):
            raise WalletError("DUPLICATE_TASK_SETTLEMENT", "Task reward has already been settled") from exc
        raise


def settle_split(
    db: Session,
    requester_id: str,
    helper_id: str,
    amount: str | Decimal,
    *,
    helper_ratio: str | Decimal,
    related_task_id: str,
) -> tuple[Wallet, Wallet]:
    try:
        value = money(amount)
        if isinstance(helper_ratio, float):
            raise WalletError("INVALID_SPLIT_RATIO", "Split ratio must not be a float")
        try:
            ratio = Decimal(str(helper_ratio))
        except (InvalidOperation, ValueError) as exc:
            raise WalletError("INVALID_SPLIT_RATIO", "Split ratio must be a valid decimal") from exc
        if ratio < Decimal("0") or ratio > Decimal("1"):
            raise WalletError("INVALID_SPLIT_RATIO", "Split ratio must be between 0 and 1")
        _ensure_positive(value)
        _ensure_no_task_settlement(db, related_task_id)

        helper_share = money(value * ratio)
        requester_share = money(value - helper_share)
        requester_wallet = get_wallet(db, requester_id, for_update=True)
        helper_wallet = get_or_create_wallet(db, helper_id, for_update=True)
        if money(requester_wallet.frozen) < value:
            raise WalletError("INSUFFICIENT_FROZEN_BALANCE", "Insufficient frozen balance")

        requester_wallet.frozen = money(Decimal(str(requester_wallet.frozen)) - value)
        requester_wallet.available = money(Decimal(str(requester_wallet.available)) + requester_share)
        _record_transaction(
            db,
            requester_wallet,
            TransactionType.SETTLE_SPLIT,
            requester_share,
            related_task_id=related_task_id,
            settlement_key=related_task_id,
            description=(
                f"Task reward split: frozen consumed {money_text(value)}, "
                f"requester refund {money_text(requester_share)}"
            ),
        )

        if helper_share > 0:
            helper_wallet.available = money(Decimal(str(helper_wallet.available)) + helper_share)
            _record_transaction(
                db,
                helper_wallet,
                TransactionType.SETTLE_SPLIT,
                helper_share,
                related_task_id=related_task_id,
                description=f"Task reward split: helper payout {money_text(helper_share)}",
            )
        return requester_wallet, helper_wallet
    except IntegrityError as exc:
        db.rollback()
        if _is_duplicate_task_settlement_integrity_error(exc):
            raise WalletError("DUPLICATE_TASK_SETTLEMENT", "Task reward has already been settled") from exc
        raise


def list_transactions(db: Session, user_id: str, *, page: int = 1, limit: int = 20) -> tuple[list[dict], int]:
    wallet = get_wallet(db, user_id)
    total = db.query(Transaction).filter(Transaction.wallet_id == wallet.id).count()
    rows = (
        db.query(Transaction)
        .filter(Transaction.wallet_id == wallet.id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return [transaction_to_dict(row) for row in rows], total
