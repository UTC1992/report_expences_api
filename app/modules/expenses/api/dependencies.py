from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.container import (
    build_deduplication_service,
    build_expense_validation_service,
    build_in_memory_expense_repository,
    build_in_memory_invoice_detail_repository,
    build_in_memory_invoice_repository,
    build_llm_orchestration_service,
    build_postgres_expense_repository,
    build_postgres_invoice_detail_repository,
    build_postgres_invoice_repository,
)
from app.core.database import get_session_factory
from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.application.services.llm_orchestration_service import LlmOrchestrationService
from app.modules.expenses.application.use_cases.import_expenses_batch import ImportExpensesBatchUseCase
from app.modules.expenses.application.use_cases.list_expenses import ListExpensesUseCase
from app.modules.expenses.application.use_cases.process_chat_expense import ProcessChatExpenseUseCase
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession | None, None]:
    if settings.persistence_provider != "postgres":
        yield None
        return
    if not settings.resolve_async_database_url():
        raise RuntimeError("PostgreSQL is selected but database connection settings are incomplete.")
    factory = get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_expense_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> ExpenseRepository:
    if settings.persistence_provider == "memory":
        return build_in_memory_expense_repository()
    if session is None:
        raise RuntimeError("Database session is required for PostgreSQL persistence.")
    return build_postgres_expense_repository(session)


async def get_invoice_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> InvoiceRepository:
    if settings.persistence_provider == "memory":
        return build_in_memory_invoice_repository()
    if session is None:
        raise RuntimeError("Database session is required for PostgreSQL persistence.")
    return build_postgres_invoice_repository(session)


async def get_invoice_detail_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> InvoiceDetailRepository:
    if settings.persistence_provider == "memory":
        return build_in_memory_invoice_detail_repository()
    if session is None:
        raise RuntimeError("Database session is required for PostgreSQL persistence.")
    return build_postgres_invoice_detail_repository(session)


def get_llm_orchestration_service() -> LlmOrchestrationService:
    return build_llm_orchestration_service()


async def get_deduplication_service(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    invoices: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
) -> DeduplicationService:
    return build_deduplication_service(expense_repository=expenses, invoice_repository=invoices)


def get_expense_validation_service() -> ExpenseValidationService:
    return build_expense_validation_service()


async def get_process_chat_expense_use_case(
    llm: Annotated[LlmOrchestrationService, Depends(get_llm_orchestration_service)],
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    dedup: Annotated[DeduplicationService, Depends(get_deduplication_service)],
    validation: Annotated[ExpenseValidationService, Depends(get_expense_validation_service)],
) -> ProcessChatExpenseUseCase:
    return ProcessChatExpenseUseCase(
        llm_orchestration=llm,
        expense_repository=expenses,
        deduplication_service=dedup,
        validation_service=validation,
    )


async def get_import_batch_use_case(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    invoices: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
    details: Annotated[InvoiceDetailRepository, Depends(get_invoice_detail_repository)],
    dedup: Annotated[DeduplicationService, Depends(get_deduplication_service)],
    validation: Annotated[ExpenseValidationService, Depends(get_expense_validation_service)],
) -> ImportExpensesBatchUseCase:
    return ImportExpensesBatchUseCase(
        expense_repository=expenses,
        invoice_repository=invoices,
        invoice_detail_repository=details,
        deduplication_service=dedup,
        validation_service=validation,
    )


async def get_list_expenses_use_case(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
) -> ListExpensesUseCase:
    return ListExpensesUseCase(expenses)
