from __future__ import annotations

from decimal import Decimal


class ImportNormalizationService:
    """Shared string/decimal normalization for batch import payloads."""

    @staticmethod
    def strip_optional(value: str | None) -> str | None:
        if value is None:
            return None
        s = value.strip()
        return s or None

    @staticmethod
    def money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))
