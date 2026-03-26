from __future__ import annotations

from app.modules.expenses.domain.entities import Expense, Invoice
from app.modules.expenses.domain.normalization import normalize_money, normalize_text
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceRepository


class DeduplicationService:
    """Shared duplicate detection for chat processing and batch import."""

    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        invoice_repository: InvoiceRepository,
    ) -> None:
        self._expenses = expense_repository
        self._invoices = invoice_repository

    async def is_duplicate_invoice(self, candidate: Invoice) -> bool:
        if candidate.access_key:
            existing = await self._invoices.find_by_access_key(candidate.access_key.strip())
            if existing is not None:
                return True
        if candidate.external_id:
            existing = await self._invoices.find_by_external_id(candidate.external_id.strip())
            if existing is not None:
                return True
        if candidate.invoice_number and candidate.supplier_ruc:
            existing = await self._invoices.find_by_invoice_number_and_ruc(
                invoice_number=candidate.invoice_number.strip(),
                supplier_ruc=candidate.supplier_ruc.strip(),
            )
            if existing is not None:
                return True
        composite = await self._invoices.find_duplicate_invoice(
            issue_date=candidate.issue_date,
            supplier_name=candidate.supplier_name,
            total=normalize_money(candidate.total),
            invoice_number=candidate.invoice_number.strip() if candidate.invoice_number else None,
        )
        return composite is not None

    async def is_duplicate_expense(self, candidate: Expense) -> bool:
        existing = await self._expenses.find_duplicate_expense(
            amount=normalize_money(candidate.amount),
            expense_date=candidate.expense_date,
            provider_name=normalize_text(candidate.provider_name),
            description=normalize_text(candidate.description),
        )
        return existing is not None
