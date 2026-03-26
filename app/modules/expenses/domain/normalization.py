from __future__ import annotations

from decimal import Decimal


def normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def normalize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))
