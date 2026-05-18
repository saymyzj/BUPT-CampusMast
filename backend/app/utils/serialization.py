from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


def to_iso8601(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def decimal_to_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def decimal_to_money(value: Decimal | float | int | None) -> str:
    numeric = Decimal(str(value or 0))
    return f"{numeric:.2f}"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)
