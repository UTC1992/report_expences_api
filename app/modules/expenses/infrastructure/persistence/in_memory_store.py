from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.expenses.domain.entities import Expense, ExpenseListFilter, Invoice, InvoiceDetail
from app.modules.expenses.domain.normalization import normalize_money, normalize_text
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository


class InMemoryPersistence:
    """Shared mutable buckets for related repository adapters."""

    def __init__(self) -> None:
        self.expenses: dict[UUID, Expense] = {}
        self.invoices: dict[UUID, Invoice] = {}
        self.invoice_details: dict[UUID, list[InvoiceDetail]] = {}


class InMemoryExpenseRepository(ExpenseRepository):
    def __init__(self, store: InMemoryPersistence) -> None:
        self._store = store

    def save(self, expense: Expense) -> Expense:
        self._store.expenses[expense.id] = expense
        return expense

    def list_filtered(self, filter_: ExpenseListFilter) -> list[Expense]:
        rows = list(self._store.expenses.values())
        if filter_.date_from is not None:
            rows = [e for e in rows if e.expense_date >= filter_.date_from]
        if filter_.date_to is not None:
            rows = [e for e in rows if e.expense_date <= filter_.date_to]
        if filter_.category is not None:
            rows = [e for e in rows if e.category.lower() == filter_.category.strip().lower()]
        if filter_.min_amount is not None:
            rows = [e for e in rows if e.amount >= filter_.min_amount]
        if filter_.max_amount is not None:
            rows = [e for e in rows if e.amount <= filter_.max_amount]
        if filter_.provider_name is not None:
            needle = filter_.provider_name.strip().lower()
            rows = [e for e in rows if needle in e.provider_name.lower()]
        if filter_.search_text is not None:
            needle = filter_.search_text.strip().lower()
            rows = [
                e
                for e in rows
                if needle in e.description.lower()
                or (e.raw_text is not None and needle in e.raw_text.lower())
            ]
        return sorted(rows, key=lambda e: e.expense_date, reverse=True)

    def find_duplicate_expense(
        self,
        *,
        amount: Decimal,
        expense_date: date,
        provider_name: str,
        description: str,
    ) -> Expense | None:
        for expense in self._store.expenses.values():
            if expense.expense_date != expense_date:
                continue
            if normalize_money(expense.amount) != amount:
                continue
            if normalize_text(expense.provider_name) != provider_name:
                continue
            if normalize_text(expense.description) != description:
                continue
            return expense
        return None


class InMemoryInvoiceRepository(InvoiceRepository):
    def __init__(self, store: InMemoryPersistence) -> None:
        self._store = store

    def save(self, invoice: Invoice) -> Invoice:
        self._store.invoices[invoice.id] = invoice
        return invoice

    def get_by_id(self, invoice_id: UUID) -> Invoice | None:
        return self._store.invoices.get(invoice_id)

    def find_by_access_key(self, access_key: str) -> Invoice | None:
        key = access_key.strip()
        for inv in self._store.invoices.values():
            if inv.access_key and inv.access_key.strip() == key:
                return inv
        return None

    def find_by_external_id(self, external_id: str) -> Invoice | None:
        key = external_id.strip()
        for inv in self._store.invoices.values():
            if inv.external_id and inv.external_id.strip() == key:
                return inv
        return None

    def find_by_invoice_number_and_ruc(
        self,
        *,
        invoice_number: str,
        supplier_ruc: str,
    ) -> Invoice | None:
        num = invoice_number.strip()
        ruc = supplier_ruc.strip()
        for inv in self._store.invoices.values():
            if (
                inv.invoice_number
                and inv.supplier_ruc
                and inv.invoice_number.strip() == num
                and inv.supplier_ruc.strip() == ruc
            ):
                return inv
        return None

    def find_duplicate_invoice(
        self,
        *,
        issue_date: date,
        supplier_name: str,
        total: Decimal,
        invoice_number: str | None,
    ) -> Invoice | None:
        ns = normalize_text(supplier_name)
        nt = normalize_money(total)
        cand_num = invoice_number.strip().lower() if invoice_number else None
        for inv in self._store.invoices.values():
            if inv.issue_date != issue_date:
                continue
            if normalize_text(inv.supplier_name) != ns:
                continue
            if normalize_money(inv.total) != nt:
                continue
            inv_num = inv.invoice_number.strip().lower() if inv.invoice_number else None
            if inv_num != cand_num:
                continue
            return inv
        return None


class InMemoryInvoiceDetailRepository(InvoiceDetailRepository):
    def __init__(self, store: InMemoryPersistence) -> None:
        self._store = store

    def save_many(self, invoice_id: UUID, details: list[InvoiceDetail]) -> list[InvoiceDetail]:
        stored = list(details)
        self._store.invoice_details[invoice_id] = stored
        return stored
