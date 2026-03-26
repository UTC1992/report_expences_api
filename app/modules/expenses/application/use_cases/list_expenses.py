from app.modules.expenses.domain.entities import Expense, ExpenseListFilter
from app.modules.expenses.domain.repositories import ExpenseRepository


class ListExpensesUseCase:
    def __init__(self, expense_repository: ExpenseRepository) -> None:
        self._expenses = expense_repository

    def execute(self, filter_: ExpenseListFilter | None = None) -> list[Expense]:
        return self._expenses.list_filtered(filter_ or ExpenseListFilter())
