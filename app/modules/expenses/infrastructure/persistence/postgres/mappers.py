from __future__ import annotations

from app.modules.expenses.domain.entities import Expense, Invoice, InvoiceDetail
from app.modules.expenses.infrastructure.persistence.postgres.orm_models import (
    ExpenseORM,
    InvoiceDetailORM,
    InvoiceORM,
)


def invoice_to_domain(row: InvoiceORM) -> Invoice:
    return Invoice(
        id=row.id,
        access_key=row.access_key,
        external_id=row.external_id,
        invoice_number=row.invoice_number,
        supplier_name=row.supplier_name,
        supplier_ruc=row.supplier_ruc,
        issue_date=row.issue_date,
        subtotal=row.subtotal,
        tax=row.tax,
        total=row.total,
        created_at=row.created_at,
    )


def invoice_from_domain(entity: Invoice) -> InvoiceORM:
    return InvoiceORM(
        id=entity.id,
        access_key=entity.access_key,
        external_id=entity.external_id,
        invoice_number=entity.invoice_number,
        supplier_name=entity.supplier_name,
        supplier_ruc=entity.supplier_ruc,
        issue_date=entity.issue_date,
        subtotal=entity.subtotal,
        tax=entity.tax,
        total=entity.total,
        created_at=entity.created_at,
    )


def expense_to_domain(row: ExpenseORM) -> Expense:
    return Expense(
        id=row.id,
        amount=row.amount,
        category=row.category,
        description=row.description,
        provider_name=row.provider_name,
        expense_date=row.expense_date,
        raw_text=row.raw_text,
        linked_invoice_id=row.linked_invoice_id,
        created_at=row.created_at,
    )


def expense_from_domain(entity: Expense) -> ExpenseORM:
    return ExpenseORM(
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


def detail_to_domain(row: InvoiceDetailORM) -> InvoiceDetail:
    return InvoiceDetail(
        id=row.id,
        invoice_id=row.invoice_id,
        item_name=row.item_name,
        quantity=row.quantity,
        unit_price=row.unit_price,
        discount=row.discount,
        line_subtotal=row.line_subtotal,
        tax=row.tax,
        total_line=row.total_line,
    )


def detail_from_domain(entity: InvoiceDetail) -> InvoiceDetailORM:
    return InvoiceDetailORM(
        id=entity.id,
        invoice_id=entity.invoice_id,
        item_name=entity.item_name,
        quantity=entity.quantity,
        unit_price=entity.unit_price,
        discount=entity.discount,
        line_subtotal=entity.line_subtotal,
        tax=entity.tax,
        total_line=entity.total_line,
    )
