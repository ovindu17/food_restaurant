"""
Value Objects for the Orders bounded context.

Value Objects are immutable, compared by value (not identity), and
encapsulate validation rules.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Typed identifiers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OrderId:
    """Strongly-typed identifier for an Order aggregate."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("OrderId cannot be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CustomerId:
    """Strongly-typed identifier for a Customer (owned by another module)."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("CustomerId cannot be empty.")

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Order Status
# ---------------------------------------------------------------------------
class OrderStatus(enum.Enum):
    """
    State machine for an order's lifecycle.

    PLACED → CONFIRMED → PREPARING → READY → PICKED_UP
    PLACED → CANCELLED
    CONFIRMED → CANCELLED
    """

    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"


# Valid transitions: current_status → set of allowed next statuses
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PLACED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.PICKED_UP},
    OrderStatus.PICKED_UP: set(),
    OrderStatus.CANCELLED: set(),
}


# ---------------------------------------------------------------------------
# Order Total
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OrderTotal:
    """
    Calculated monetary total for an order.

    Uses ``Decimal`` to avoid floating-point pitfalls.
    """

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except Exception as exc:
                raise ValueError(f"Invalid order total: {self.amount}") from exc

        quantized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

        if self.amount < 0:
            raise ValueError(f"Order total cannot be negative. Got: {self.amount}")

        if not self.currency or len(self.currency) != 3:
            raise ValueError(f"Currency must be a 3-letter ISO code. Got: {self.currency}")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
