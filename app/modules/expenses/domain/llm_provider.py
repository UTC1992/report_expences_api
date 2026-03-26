from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ParsedExpenseDraft:
    """Structured output from an LLM before domain validation and persistence."""

    amount: Decimal
    category: str
    description: str
    provider_name: str
    expense_date: date


class LlmProvider(Protocol):
    """Port for chat-based expense extraction (OpenAI first; swap implementation in infra)."""

    async def parse_expense_from_text(self, text: str) -> ParsedExpenseDraft:
        """Parse free-text into a draft expense. Implementations may call external APIs."""
        ...
