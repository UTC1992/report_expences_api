from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from openai import AsyncOpenAI

from app.core.exceptions import ValidationError
from app.modules.expenses.domain.llm_provider import LlmProvider, ParsedExpenseDraft

_SYSTEM_PROMPT = """You extract structured expense data from free-form user text.
Respond with a single JSON object only, no markdown, with exactly these keys:
- amount: string representing a decimal number (e.g. "12.50")
- category: short string
- description: short string in the user's language
- provider_name: merchant or vendor name if inferable, else "unknown"
- expense_date: ISO date string YYYY-MM-DD (infer from context; use a sensible default if missing)
"""


class OpenAiLlmProvider(LlmProvider):
    """OpenAI Chat Completions with JSON mode. Keys are never logged."""

    def __init__(self, *, default_model: str, fallback_api_key: str | None) -> None:
        self._default_model = default_model
        self._fallback_api_key = fallback_api_key

    async def parse_expense_from_text(
        self,
        text: str,
        *,
        provider: str,
        api_key: str | None,
    ) -> ParsedExpenseDraft:
        if provider.strip().lower() != "openai":
            raise ValidationError(f"Unsupported LLM provider: {provider}")
        key = (api_key or "").strip() or (self._fallback_api_key or "").strip()
        if not key:
            raise ValidationError(
                "OpenAI API key is required: pass api_key in the request or set OPENAI_API_KEY in the server environment."
            )
        client = AsyncOpenAI(api_key=key)
        try:
            response = await client.chat.completions.create(
                model=self._default_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text.strip()},
                ],
            )
        except Exception as exc:
            raise ValidationError("OpenAI request failed") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("OpenAI returned invalid JSON") from exc

        try:
            amount = Decimal(str(data.get("amount")))
            category = str(data["category"])
            description = str(data["description"])
            provider_name = str(data["provider_name"])
            expense_date = date.fromisoformat(str(data["expense_date"]))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise ValidationError("OpenAI JSON missing required fields or invalid types") from exc

        return ParsedExpenseDraft(
            amount=amount.quantize(Decimal("0.01")),
            category=category,
            description=description,
            provider_name=provider_name,
            expense_date=expense_date,
        )
