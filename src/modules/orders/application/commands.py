"""
Commands and Queries — the inputs to the Application layer.

Commands represent *intentions to change state*.
Queries represent *read requests*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Nested DTO for order items in commands
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OrderItemInput:
    """One dish + quantity requested by the customer."""

    dish_id: str
    quantity: int


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PlaceOrderCommand:
    customer_id: str
    items: List[OrderItemInput]
    notes: str = ""


@dataclass(frozen=True)
class ConfirmOrderCommand:
    order_id: str


@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: str
    reason: str = ""


@dataclass(frozen=True)
class StartPreparingCommand:
    order_id: str


@dataclass(frozen=True)
class MarkReadyCommand:
    order_id: str


@dataclass(frozen=True)
class PickUpOrderCommand:
    order_id: str


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GetOrderQuery:
    order_id: str


@dataclass(frozen=True)
class ListCustomerOrdersQuery:
    customer_id: str
