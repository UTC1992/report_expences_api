from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.expenses.infrastructure.persistence.postgres.base import Base


class InvoiceORM(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    invoice_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(512), nullable=False)
    supplier_ruc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    details: Mapped[list["InvoiceDetailORM"]] = relationship(
        "InvoiceDetailORM",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    expenses: Mapped[list["ExpenseORM"]] = relationship(
        "ExpenseORM",
        back_populates="linked_invoice",
        foreign_keys="ExpenseORM.linked_invoice_id",
    )


class InvoiceDetailORM(Base):
    __tablename__ = "invoice_details"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(512), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    total_line: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    invoice: Mapped["InvoiceORM"] = relationship(back_populates="details")


class ExpenseORM(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(512), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    linked_invoice: Mapped["InvoiceORM | None"] = relationship(
        "InvoiceORM",
        back_populates="expenses",
        foreign_keys=[linked_invoice_id],
    )
