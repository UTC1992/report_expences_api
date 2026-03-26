"""Composition root: bind infrastructure implementations to domain ports."""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.application.services.llm_orchestration_service import LlmOrchestrationService
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository
from app.modules.expenses.infrastructure.llm.openai_llm_provider import OpenAiLlmProvider
from app.modules.expenses.infrastructure.persistence.in_memory_store import (
    InMemoryExpenseRepository,
    InMemoryInvoiceDetailRepository,
    InMemoryInvoiceRepository,
    InMemoryPersistence,
)
from app.modules.expenses.infrastructure.persistence.postgres.postgres_repositories import (
    PostgresExpenseRepository,
    PostgresInvoiceDetailRepository,
    PostgresInvoiceRepository,
)
from sqlalchemy.ext.asyncio import AsyncSession


@lru_cache
def get_memory_persistence() -> InMemoryPersistence:
    return InMemoryPersistence()


def build_in_memory_expense_repository() -> ExpenseRepository:
    return InMemoryExpenseRepository(get_memory_persistence())


def build_in_memory_invoice_repository() -> InvoiceRepository:
    return InMemoryInvoiceRepository(get_memory_persistence())


def build_in_memory_invoice_detail_repository() -> InvoiceDetailRepository:
    return InMemoryInvoiceDetailRepository(get_memory_persistence())


def build_postgres_expense_repository(session: AsyncSession) -> ExpenseRepository:
    return PostgresExpenseRepository(session)


def build_postgres_invoice_repository(session: AsyncSession) -> InvoiceRepository:
    return PostgresInvoiceRepository(session)


def build_postgres_invoice_detail_repository(session: AsyncSession) -> InvoiceDetailRepository:
    return PostgresInvoiceDetailRepository(session)


def build_llm_orchestration_service(settings: Settings | None = None) -> LlmOrchestrationService:
    settings = settings or get_settings()
    openai = OpenAiLlmProvider(
        default_model=settings.resolve_openai_model(),
        fallback_api_key=settings.openai_api_key.strip() or None,
    )
    return LlmOrchestrationService(openai_provider=openai)


def build_deduplication_service(
    expense_repository: ExpenseRepository,
    invoice_repository: InvoiceRepository,
) -> DeduplicationService:
    return DeduplicationService(
        expense_repository=expense_repository,
        invoice_repository=invoice_repository,
    )


def build_expense_validation_service() -> ExpenseValidationService:
    return ExpenseValidationService()
