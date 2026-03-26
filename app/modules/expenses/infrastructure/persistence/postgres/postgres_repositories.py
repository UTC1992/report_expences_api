from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.expenses.domain.entities import Expense, ExpenseListFilter, Invoice, InvoiceDetail
from app.modules.expenses.domain.normalization import normalize_money, normalize_text
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository
from app.modules.expenses.infrastructure.persistence.postgres.mappers import (
    detail_from_domain,
    expense_from_domain,
    expense_to_domain,
    invoice_from_domain,
    invoice_to_domain,
)
from app.modules.expenses.infrastructure.persistence.postgres.orm_models import ExpenseORM, InvoiceORM


class PostgresExpenseRepository(ExpenseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, expense: Expense) -> Expense:
        row = expense_from_domain(expense)
        self._session.add(row)
        await self._session.flush()
        return expense_to_domain(row)

    async def list_filtered(self, filter_: ExpenseListFilter) -> list[Expense]:
        stmt = select(ExpenseORM)
        if filter_.date_from is not None:
            stmt = stmt.where(ExpenseORM.expense_date >= filter_.date_from)
        if filter_.date_to is not None:
            stmt = stmt.where(ExpenseORM.expense_date <= filter_.date_to)
        if filter_.category is not None:
            cat = filter_.category.strip().lower()
            stmt = stmt.where(func.lower(ExpenseORM.category) == cat)
        if filter_.min_amount is not None:
            stmt = stmt.where(ExpenseORM.amount >= filter_.min_amount)
        if filter_.max_amount is not None:
            stmt = stmt.where(ExpenseORM.amount <= filter_.max_amount)
        if filter_.provider_name is not None:
            needle = f"%{filter_.provider_name.strip().lower()}%"
            stmt = stmt.where(func.lower(ExpenseORM.provider_name).like(needle))
        if filter_.search_text is not None:
            needle = f"%{filter_.search_text.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ExpenseORM.description).like(needle),
                    func.lower(func.coalesce(ExpenseORM.raw_text, "")).like(needle),
                )
            )
        stmt = stmt.order_by(ExpenseORM.expense_date.desc())
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [expense_to_domain(r) for r in rows]

    async def find_duplicate_expense(
        self,
        *,
        amount: Decimal,
        expense_date: date,
        provider_name: str,
        description: str,
    ) -> Expense | None:
        stmt = select(ExpenseORM).where(
            ExpenseORM.expense_date == expense_date,
            ExpenseORM.amount == amount,
        )
        result = await self._session.execute(stmt)
        for row in result.scalars():
            if normalize_text(row.provider_name) == provider_name and normalize_text(
                row.description
            ) == description:
                return expense_to_domain(row)
        return None


class PostgresInvoiceRepository(InvoiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, invoice: Invoice) -> Invoice:
        row = invoice_from_domain(invoice)
        self._session.add(row)
        await self._session.flush()
        return invoice_to_domain(row)

    async def get_by_id(self, invoice_id: UUID) -> Invoice | None:
        row = await self._session.get(InvoiceORM, invoice_id)
        return invoice_to_domain(row) if row else None

    async def find_by_access_key(self, access_key: str) -> Invoice | None:
        key = access_key.strip()
        stmt = select(InvoiceORM).where(InvoiceORM.access_key == key).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return invoice_to_domain(row) if row else None

    async def find_by_external_id(self, external_id: str) -> Invoice | None:
        key = external_id.strip()
        stmt = select(InvoiceORM).where(InvoiceORM.external_id == key).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return invoice_to_domain(row) if row else None

    async def find_by_invoice_number_and_ruc(
        self,
        *,
        invoice_number: str,
        supplier_ruc: str,
    ) -> Invoice | None:
        num = invoice_number.strip()
        ruc = supplier_ruc.strip()
        stmt = (
            select(InvoiceORM)
            .where(
                InvoiceORM.invoice_number == num,
                InvoiceORM.supplier_ruc == ruc,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return invoice_to_domain(row) if row else None

    async def find_duplicate_invoice(
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
        stmt = select(InvoiceORM).where(
            InvoiceORM.issue_date == issue_date,
            InvoiceORM.total == nt,
        )
        result = await self._session.execute(stmt)
        for row in result.scalars():
            if normalize_text(row.supplier_name) != ns:
                continue
            inv_num = row.invoice_number.strip().lower() if row.invoice_number else None
            if inv_num == cand_num:
                return invoice_to_domain(row)
        return None


class PostgresInvoiceDetailRepository(InvoiceDetailRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_many(self, invoice_id: UUID, details: list[InvoiceDetail]) -> list[InvoiceDetail]:
        for d in details:
            self._session.add(detail_from_domain(d))
        await self._session.flush()
        return list(details)
