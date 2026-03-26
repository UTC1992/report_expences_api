from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.expenses.domain.entities import Expense, ExpenseListFilter, Invoice, InvoiceDetail


class ExpenseRepository(Protocol):
    def save(self, expense: Expense) -> Expense: ...

    def list_filtered(self, filter_: ExpenseListFilter) -> list[Expense]: ...

    def find_duplicate_expense(
        self,
        *,
        amount: Decimal,
        expense_date: date,
        provider_name: str,
        description: str,
    ) -> Expense | None: ...


class InvoiceRepository(Protocol):
    def save(self, invoice: Invoice) -> Invoice: ...

    def get_by_id(self, invoice_id: UUID) -> Invoice | None: ...

    def find_by_access_key(self, access_key: str) -> Invoice | None: ...

    def find_by_external_id(self, external_id: str) -> Invoice | None: ...

    def find_by_invoice_number_and_ruc(
        self,
        *,
        invoice_number: str,
        supplier_ruc: str,
    ) -> Invoice | None: ...

    def find_duplicate_invoice(
        self,
        *,
        issue_date: date,
        supplier_name: str,
        total: Decimal,
        invoice_number: str | None,
    ) -> Invoice | None: ...


class InvoiceDetailRepository(Protocol):
    def save_many(self, invoice_id: UUID, details: list[InvoiceDetail]) -> list[InvoiceDetail]: ...
