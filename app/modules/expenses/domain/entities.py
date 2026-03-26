from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Expense:
    id: UUID
    amount: Decimal
    category: str
    description: str
    provider_name: str
    expense_date: date
    raw_text: str | None
    linked_invoice_id: UUID | None
    created_at: datetime


@dataclass(slots=True)
class Invoice:
    id: UUID
    access_key: str | None
    external_id: str | None
    invoice_number: str | None
    supplier_name: str
    supplier_ruc: str | None
    issue_date: date
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime


@dataclass(slots=True)
class InvoiceDetail:
    id: UUID
    invoice_id: UUID
    item_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    line_subtotal: Decimal
    tax: Decimal
    total_line: Decimal


@dataclass(slots=True)
class ExpenseListFilter:
    date_from: date | None = None
    date_to: date | None = None
    category: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    provider_name: str | None = None
    search_text: str | None = None
