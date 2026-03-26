from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.domain.entities import Expense, Invoice, InvoiceDetail
from app.modules.expenses.domain.repositories import (
    ExpenseRepository,
    InvoiceDetailRepository,
    InvoiceRepository,
)


@dataclass(frozen=True, slots=True)
class ImportBatchInput:
    invoices: list[InvoiceImportItem]


@dataclass(frozen=True, slots=True)
class InvoiceImportItem:
    access_key: str | None
    external_id: str | None
    invoice_number: str | None
    supplier_name: str
    supplier_ruc: str | None
    issue_date: date
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    details: list[InvoiceDetailImportItem]
    expenses: list[ExpenseImportItem]


@dataclass(frozen=True, slots=True)
class InvoiceDetailImportItem:
    item_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    line_subtotal: Decimal
    tax: Decimal
    total_line: Decimal


@dataclass(frozen=True, slots=True)
class ExpenseImportItem:
    amount: Decimal
    category: str
    description: str
    provider_name: str
    expense_date: date
    raw_text: str | None


@dataclass(frozen=True, slots=True)
class ImportBatchResult:
    invoices_saved: int
    invoices_skipped_duplicate: int
    expenses_saved: int
    expenses_skipped_duplicate: int


class ImportExpensesBatchUseCase:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        invoice_repository: InvoiceRepository,
        invoice_detail_repository: InvoiceDetailRepository,
        deduplication_service: DeduplicationService,
        validation_service: ExpenseValidationService,
    ) -> None:
        self._expenses = expense_repository
        self._invoices = invoice_repository
        self._details = invoice_detail_repository
        self._dedup = deduplication_service
        self._validation = validation_service

    async def execute(self, batch: ImportBatchInput) -> ImportBatchResult:
        invoices_saved = 0
        invoices_skipped = 0
        expenses_saved = 0
        expenses_skipped = 0

        for item in batch.invoices:
            invoice = Invoice(
                id=uuid4(),
                access_key=item.access_key.strip() if item.access_key else None,
                external_id=item.external_id.strip() if item.external_id else None,
                invoice_number=item.invoice_number.strip() if item.invoice_number else None,
                supplier_name=item.supplier_name.strip(),
                supplier_ruc=item.supplier_ruc.strip() if item.supplier_ruc else None,
                issue_date=item.issue_date,
                subtotal=self._validation.require_positive_amount(item.subtotal),
                tax=item.tax.quantize(Decimal("0.01")),
                total=self._validation.require_positive_amount(item.total),
                created_at=datetime.now(UTC),
            )
            self._validation.validate_invoice(invoice)

            detail_entities = [
                InvoiceDetail(
                    id=uuid4(),
                    invoice_id=invoice.id,
                    item_name=d.item_name.strip(),
                    quantity=d.quantity,
                    unit_price=d.unit_price.quantize(Decimal("0.01")),
                    discount=d.discount.quantize(Decimal("0.01")),
                    line_subtotal=d.line_subtotal.quantize(Decimal("0.01")),
                    tax=d.tax.quantize(Decimal("0.01")),
                    total_line=d.total_line.quantize(Decimal("0.01")),
                )
                for d in item.details
            ]
            self._validation.validate_invoice_details(detail_entities)

            if await self._dedup.is_duplicate_invoice(invoice):
                invoices_skipped += 1
                continue

            saved_invoice = await self._invoices.save(invoice)
            await self._details.save_many(saved_invoice.id, detail_entities)

            for expense_item in item.expenses:
                self._validation.validate_expense_fields(
                    amount=expense_item.amount,
                    category=expense_item.category,
                    description=expense_item.description,
                    provider_name=expense_item.provider_name,
                    expense_date=expense_item.expense_date,
                )
                expense = Expense(
                    id=uuid4(),
                    amount=self._validation.require_positive_amount(expense_item.amount),
                    category=expense_item.category.strip(),
                    description=expense_item.description.strip(),
                    provider_name=expense_item.provider_name.strip(),
                    expense_date=expense_item.expense_date,
                    raw_text=expense_item.raw_text,
                    linked_invoice_id=saved_invoice.id,
                    created_at=datetime.now(UTC),
                )
                if await self._dedup.is_duplicate_expense(expense):
                    expenses_skipped += 1
                    continue
                await self._expenses.save(expense)
                expenses_saved += 1

            invoices_saved += 1

        return ImportBatchResult(
            invoices_saved=invoices_saved,
            invoices_skipped_duplicate=invoices_skipped,
            expenses_saved=expenses_saved,
            expenses_skipped_duplicate=expenses_skipped,
        )
