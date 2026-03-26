from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.expenses.domain.entities import Expense


class ChatProcessExpenseRequest(BaseModel):
    text: str = Field(min_length=1)


class ChatProcessExpenseResponse(BaseModel):
    saved: bool
    duplicate: bool
    expense_id: str | None = None


class InvoiceDetailImportBody(BaseModel):
    item_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal = Decimal("0")
    line_subtotal: Decimal
    tax: Decimal = Decimal("0")
    total_line: Decimal


class ExpenseImportBody(BaseModel):
    amount: Decimal
    category: str
    description: str
    provider_name: str
    expense_date: date
    raw_text: str | None = None


class InvoiceImportBody(BaseModel):
    access_key: str | None = None
    external_id: str | None = None
    invoice_number: str | None = None
    supplier_name: str
    supplier_ruc: str | None = None
    issue_date: date
    subtotal: Decimal
    tax: Decimal = Decimal("0")
    total: Decimal
    details: list[InvoiceDetailImportBody] = Field(default_factory=list)
    expenses: list[ExpenseImportBody] = Field(default_factory=list)


class ImportBatchRequest(BaseModel):
    invoices: list[InvoiceImportBody]


class ImportBatchResponse(BaseModel):
    invoices_saved: int
    invoices_skipped_duplicate: int
    expenses_saved: int
    expenses_skipped_duplicate: int


class ExpenseResponse(BaseModel):
    id: UUID
    amount: Decimal
    category: str
    description: str
    provider_name: str
    expense_date: date
    raw_text: str | None
    linked_invoice_id: UUID | None
    created_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int


def expense_to_response(entity: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=entity.id,
        amount=entity.amount,
        category=entity.category,
        description=entity.description,
        provider_name=entity.provider_name,
        expense_date=entity.expense_date,
        raw_text=entity.raw_text,
        linked_invoice_id=entity.linked_invoice_id,
        created_at=entity.created_at,
    )
