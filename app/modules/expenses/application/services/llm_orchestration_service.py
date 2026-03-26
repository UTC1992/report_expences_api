from __future__ import annotations

from app.core.exceptions import ValidationError
from app.modules.expenses.domain.llm_provider import LlmProvider, ParsedExpenseDraft


class LlmOrchestrationService:
    """Routes provider id to concrete LLM adapters (OpenAI first; extend for Gemini/Anthropic)."""

    def __init__(self, *, openai_provider: LlmProvider) -> None:
        self._openai = openai_provider

    async def parse_chat_expense(
        self,
        text: str,
        *,
        provider: str,
        api_key: str | None,
    ) -> ParsedExpenseDraft:
        pid = provider.strip().lower()
        if pid == "openai":
            return await self._openai.parse_expense_from_text(
                text,
                provider=provider,
                api_key=api_key,
            )
        raise ValidationError(f"Unsupported LLM provider: {provider}")
