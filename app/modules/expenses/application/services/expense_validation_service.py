from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core.exceptions import ValidationError
from app.modules.expenses.domain.entities import Expense, Invoice, InvoiceDetail


class ExpenseValidationService:
    """Normalization and validation rules shared across entry points."""

    @staticmethod
    def require_positive_amount(amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValidationError("amount must be greater than zero")
        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def require_non_empty(value: str, field_name: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValidationError(f"{field_name} is required")
        return stripped

    def validate_expense_fields(
        self,
        *,
        amount: Decimal,
        category: str,
        description: str,
        provider_name: str,
        expense_date: date,
    ) -> None:
        self.require_positive_amount(amount)
        self.require_non_empty(category, "category")
        self.require_non_empty(description, "description")
        self.require_non_empty(provider_name, "provider_name")

    def validate_invoice(self, invoice: Invoice) -> None:
        self.require_non_empty(invoice.supplier_name, "supplier_name")
        if invoice.total <= 0:
            raise ValidationError("invoice total must be greater than zero")

    def validate_invoice_details(self, details: list[InvoiceDetail]) -> None:
        for line in details:
            if line.quantity <= 0:
                raise ValidationError("invoice detail quantity must be greater than zero")
