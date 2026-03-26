from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.domain.entities import Expense
from app.modules.expenses.domain.llm_provider import LlmProvider
from app.modules.expenses.domain.repositories import ExpenseRepository


@dataclass(frozen=True, slots=True)
class ProcessChatExpenseResult:
    saved: bool
    duplicate: bool
    expense_id: str | None


class ProcessChatExpenseUseCase:
    def __init__(
        self,
        *,
        llm_provider: LlmProvider,
        expense_repository: ExpenseRepository,
        deduplication_service: DeduplicationService,
        validation_service: ExpenseValidationService,
    ) -> None:
        self._llm = llm_provider
        self._expenses = expense_repository
        self._dedup = deduplication_service
        self._validation = validation_service

    async def execute(self, text: str) -> ProcessChatExpenseResult:
        self._validation.require_non_empty(text, "text")
        stripped = text.strip()

        draft = await self._llm.parse_expense_from_text(stripped)
        self._validation.validate_expense_fields(
            amount=draft.amount,
            category=draft.category,
            description=draft.description,
            provider_name=draft.provider_name,
            expense_date=draft.expense_date,
        )

        expense = Expense(
            id=uuid4(),
            amount=self._validation.require_positive_amount(draft.amount),
            category=draft.category.strip(),
            description=draft.description.strip(),
            provider_name=draft.provider_name.strip(),
            expense_date=draft.expense_date,
            raw_text=stripped,
            linked_invoice_id=None,
            created_at=datetime.now(UTC),
        )

        if self._dedup.is_duplicate_expense(expense):
            return ProcessChatExpenseResult(saved=False, duplicate=True, expense_id=None)

        saved = self._expenses.save(expense)
        return ProcessChatExpenseResult(saved=True, duplicate=False, expense_id=str(saved.id))
