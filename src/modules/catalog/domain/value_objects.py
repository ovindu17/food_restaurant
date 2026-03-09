"""
Value Objects for the Catalog bounded context.

Value Objects are immutable, compared by value (not identity), and
encapsulate validation rules that would otherwise leak into services.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Typed identifiers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DishId:
    """Strongly-typed identifier for a Dish aggregate."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("DishId cannot be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SellerId:
    """Strongly-typed identifier for a Seller (owned by another module)."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("SellerId cannot be empty.")

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Money:
    """
    Represents a monetary amount with two-decimal precision.

    Using ``Decimal`` avoids the floating-point pitfalls of ``float``.
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        # Convert from int/float/str if needed, then validate
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"Invalid monetary amount: {self.amount}") from exc

        if self.amount <= 0:
            raise ValueError(f"Money amount must be positive. Got: {self.amount}")

        # Normalize to 2 decimal places
        quantized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code. Got: {self.currency}")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies.")
        return Money(amount=self.amount + other.amount, currency=self.currency)


# ---------------------------------------------------------------------------
# Portions
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Portions:
    """
    Non-negative integer representing available servings.
    Encapsulates the deduction rule.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int):
            raise TypeError(f"Portions must be an integer. Got: {type(self.value).__name__}")
        if self.value < 0:
            object.__setattr__(self, "value", 0)

    def deduct(self, amount: int) -> Portions:
        if amount <= 0:
            raise ValueError("Deduction amount must be positive.")
        if amount > self.value:
            raise ValueError(
                f"Cannot deduct {amount} portions. Only {self.value} available."
            )
        return Portions(value=self.value - amount)

    def is_exhausted(self) -> bool:
        return self.value == 0

    def __str__(self) -> str:
        return str(self.value)
