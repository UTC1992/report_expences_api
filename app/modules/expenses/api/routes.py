from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.expenses.api.dependencies import (
    get_import_batch_use_case,
    get_list_expenses_use_case,
    get_process_chat_expense_use_case,
)
from app.modules.expenses.api.schemas import (
    ChatProcessExpenseRequest,
    ChatProcessExpenseResponse,
    ExpenseListResponse,
    ImportBatchRequest,
    ImportBatchResponse,
    expense_to_response,
)
from app.modules.expenses.application.use_cases.import_expenses_batch import (
    ExpenseImportItem,
    ImportBatchInput,
    ImportExpensesBatchUseCase,
    InvoiceDetailImportItem,
    InvoiceImportItem,
)
from app.modules.expenses.application.use_cases.list_expenses import ListExpensesUseCase
from app.modules.expenses.application.use_cases.process_chat_expense import ProcessChatExpenseUseCase
from app.modules.expenses.domain.entities import ExpenseListFilter

chat_router = APIRouter(tags=["chat"])


@chat_router.post("/process_expense", response_model=ChatProcessExpenseResponse)
async def process_expense_from_chat(
    body: ChatProcessExpenseRequest,
    use_case: Annotated[ProcessChatExpenseUseCase, Depends(get_process_chat_expense_use_case)],
) -> ChatProcessExpenseResponse:
    result = await use_case.execute(body.text)
    return ChatProcessExpenseResponse(
        saved=result.saved,
        duplicate=result.duplicate,
        expense_id=result.expense_id,
    )


expenses_router = APIRouter(tags=["expenses"])


@expenses_router.get("", response_model=ExpenseListResponse)
def list_expenses(
    use_case: Annotated[ListExpensesUseCase, Depends(get_list_expenses_use_case)],
    category: str | None = Query(default=None),
    provider_name: str | None = Query(default=None),
    search_text: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    min_amount: Decimal | None = Query(default=None),
    max_amount: Decimal | None = Query(default=None),
) -> ExpenseListResponse:
    filter_ = ExpenseListFilter(
        category=category,
        provider_name=provider_name,
        search_text=search_text,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
    )
    has_any = any(
        [
            category is not None,
            provider_name is not None,
            search_text is not None,
            date_from is not None,
            date_to is not None,
            min_amount is not None,
            max_amount is not None,
        ]
    )
    rows = use_case.execute(filter_ if has_any else None)
    return ExpenseListResponse(items=[expense_to_response(e) for e in rows], total=len(rows))


@expenses_router.post("/import", response_model=ImportBatchResponse)
def import_expenses_batch(
    body: ImportBatchRequest,
    use_case: Annotated[ImportExpensesBatchUseCase, Depends(get_import_batch_use_case)],
) -> ImportBatchResponse:
    batch = _map_import_request(body)
    result = use_case.execute(batch)
    return ImportBatchResponse(
        invoices_saved=result.invoices_saved,
        invoices_skipped_duplicate=result.invoices_skipped_duplicate,
        expenses_saved=result.expenses_saved,
        expenses_skipped_duplicate=result.expenses_skipped_duplicate,
    )


def _map_import_request(body: ImportBatchRequest) -> ImportBatchInput:
    invoices: list[InvoiceImportItem] = []
    for inv in body.invoices:
        details = [
            InvoiceDetailImportItem(
                item_name=d.item_name,
                quantity=d.quantity,
                unit_price=d.unit_price,
                discount=d.discount,
                line_subtotal=d.line_subtotal,
                tax=d.tax,
                total_line=d.total_line,
            )
            for d in inv.details
        ]
        expenses = [
            ExpenseImportItem(
                amount=e.amount,
                category=e.category,
                description=e.description,
                provider_name=e.provider_name,
                expense_date=e.expense_date,
                raw_text=e.raw_text,
            )
            for e in inv.expenses
        ]
        invoices.append(
            InvoiceImportItem(
                access_key=inv.access_key,
                external_id=inv.external_id,
                invoice_number=inv.invoice_number,
                supplier_name=inv.supplier_name,
                supplier_ruc=inv.supplier_ruc,
                issue_date=inv.issue_date,
                subtotal=inv.subtotal,
                tax=inv.tax,
                total=inv.total,
                details=details,
                expenses=expenses,
            )
        )
    return ImportBatchInput(invoices=invoices)
