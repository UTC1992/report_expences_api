from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

from app.modules.expenses.domain.llm_provider import LlmProvider, ParsedExpenseDraft


class OpenAiLlmProvider(LlmProvider):
    """
    OpenAI-backed parser (structure ready; replace body with real API calls).

    Deterministic mock derived from input text so tests stay stable without API keys.
    """

    async def parse_expense_from_text(self, text: str) -> ParsedExpenseDraft:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        amount = Decimal("10.00") + (int(digest[:4], 16) % 500) / 100
        day_index = int(digest[4:8], 16) % 28 + 1
        expense_date = date(2025, 1, min(day_index, 28))
        return ParsedExpenseDraft(
            amount=amount.quantize(Decimal("0.01")),
            category="general",
            description=text.strip()[:200] or "Parsed expense",
            provider_name="unknown_provider",
            expense_date=expense_date,
        )
