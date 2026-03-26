"""Composition root: bind infrastructure implementations to domain ports."""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.domain.llm_provider import LlmProvider
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository
from app.modules.expenses.infrastructure.llm.openai_llm_provider import OpenAiLlmProvider
from app.modules.expenses.infrastructure.persistence.in_memory_store import (
    InMemoryExpenseRepository,
    InMemoryInvoiceDetailRepository,
    InMemoryInvoiceRepository,
    InMemoryPersistence,
)


@lru_cache
def get_memory_persistence() -> InMemoryPersistence:
    return InMemoryPersistence()


def build_expense_repository(settings: Settings | None = None) -> ExpenseRepository:
    settings = settings or get_settings()
    if settings.persistence_provider != "memory":
        raise ValueError(f"Unsupported persistence provider: {settings.persistence_provider}")
    return InMemoryExpenseRepository(get_memory_persistence())


def build_invoice_repository(settings: Settings | None = None) -> InvoiceRepository:
    settings = settings or get_settings()
    if settings.persistence_provider != "memory":
        raise ValueError(f"Unsupported persistence provider: {settings.persistence_provider}")
    return InMemoryInvoiceRepository(get_memory_persistence())


def build_invoice_detail_repository(settings: Settings | None = None) -> InvoiceDetailRepository:
    settings = settings or get_settings()
    if settings.persistence_provider != "memory":
        raise ValueError(f"Unsupported persistence provider: {settings.persistence_provider}")
    return InMemoryInvoiceDetailRepository(get_memory_persistence())


def build_llm_provider(settings: Settings | None = None) -> LlmProvider:
    settings = settings or get_settings()
    if settings.llm_provider in {"openai_stub", "openai"}:
        return OpenAiLlmProvider()
    raise ValueError(f"Unsupported llm provider: {settings.llm_provider}")


def build_deduplication_service(settings: Settings | None = None) -> DeduplicationService:
    settings = settings or get_settings()
    return DeduplicationService(
        expense_repository=build_expense_repository(settings),
        invoice_repository=build_invoice_repository(settings),
    )


def build_expense_validation_service() -> ExpenseValidationService:
    return ExpenseValidationService()
