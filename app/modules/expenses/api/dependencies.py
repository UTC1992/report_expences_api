from typing import Annotated

from fastapi import Depends

from app.core.container import (
    build_deduplication_service,
    build_expense_repository,
    build_expense_validation_service,
    build_invoice_detail_repository,
    build_invoice_repository,
    build_llm_provider,
)
from app.modules.expenses.application.services.deduplication_service import DeduplicationService
from app.modules.expenses.application.services.expense_validation_service import ExpenseValidationService
from app.modules.expenses.application.use_cases.import_expenses_batch import ImportExpensesBatchUseCase
from app.modules.expenses.application.use_cases.list_expenses import ListExpensesUseCase
from app.modules.expenses.application.use_cases.process_chat_expense import ProcessChatExpenseUseCase
from app.modules.expenses.domain.llm_provider import LlmProvider
from app.modules.expenses.domain.repositories import ExpenseRepository, InvoiceDetailRepository, InvoiceRepository


def get_expense_repository() -> ExpenseRepository:
    return build_expense_repository()


def get_invoice_repository() -> InvoiceRepository:
    return build_invoice_repository()


def get_invoice_detail_repository() -> InvoiceDetailRepository:
    return build_invoice_detail_repository()


def get_llm_provider() -> LlmProvider:
    return build_llm_provider()


def get_deduplication_service() -> DeduplicationService:
    return build_deduplication_service()


def get_expense_validation_service() -> ExpenseValidationService:
    return build_expense_validation_service()


def get_process_chat_expense_use_case(
    llm: Annotated[LlmProvider, Depends(get_llm_provider)],
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    dedup: Annotated[DeduplicationService, Depends(get_deduplication_service)],
    validation: Annotated[ExpenseValidationService, Depends(get_expense_validation_service)],
) -> ProcessChatExpenseUseCase:
    return ProcessChatExpenseUseCase(
        llm_provider=llm,
        expense_repository=expenses,
        deduplication_service=dedup,
        validation_service=validation,
    )


def get_import_batch_use_case(
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


def get_list_expenses_use_case(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repository)],
) -> ListExpensesUseCase:
    return ListExpensesUseCase(expenses)
