"""
Order — the Aggregate Root for the Orders bounded context.
OrderItem — an Entity within the Order aggregate.

All mutations go through public methods that enforce invariants and
record domain events.  No external code should mutate fields directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from src.shared.domain.base import AggregateRoot, Entity
from src.modules.orders.domain.exceptions import (
    EmptyOrderError,
    InvalidOrderTransitionError,
    OrderAlreadyCancelledError,
)
from src.modules.orders.domain.events import (
    OrderCancelledEvent,
    OrderConfirmedEvent,
    OrderItemData,
    OrderPickedUpEvent,
    OrderPlacedEvent,
    OrderReadyEvent,
)
from src.modules.orders.domain.value_objects import (
    CustomerId,
    OrderId,
    OrderStatus,
    OrderTotal,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# OrderItem (child entity)
# ---------------------------------------------------------------------------
@dataclass
class OrderItem(Entity):
    """A line item in an order — snapshot of dish at time of ordering."""

    dish_id: str = ""
    dish_name: str = ""
    quantity: int = 0
    unit_price: Decimal = Decimal("0")
    currency: str = "USD"

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))

    @classmethod
    def create(
        cls,
        dish_id: str,
        dish_name: str,
        quantity: int,
        unit_price: Decimal,
        currency: str = "USD",
    ) -> OrderItem:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if unit_price <= 0:
            raise ValueError("Unit price must be positive.")
        return cls(
            id=str(uuid.uuid4()),
            dish_id=dish_id,
            dish_name=dish_name,
            quantity=quantity,
            unit_price=Decimal(str(unit_price)).quantize(Decimal("0.01")),
            currency=currency,
        )


# ---------------------------------------------------------------------------
# Order (Aggregate Root)
# ---------------------------------------------------------------------------
@dataclass
class Order(AggregateRoot):
    """
    Aggregate Root representing a customer's order.

    Use the ``create`` class method to build new instances — it enforces
    all creation-time invariants and records an ``OrderPlacedEvent``.

    Use the ``reconstitute`` class method when loading from persistence
    so that validation and events are **not** re-triggered.
    """

    customer_id: CustomerId = field(default_factory=lambda: CustomerId("unset"))
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PLACED
    total: OrderTotal = field(default_factory=lambda: OrderTotal(amount=0))
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Factory: new order
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        customer_id: CustomerId,
        items: List[OrderItem],
        notes: str = "",
    ) -> Order:
        """
        Named constructor enforcing creation invariants.
        Records an ``OrderPlacedEvent``.
        """
        if not items:
            raise EmptyOrderError()

        # Calculate total from items (all items should share the same currency)
        currency = items[0].currency
        total_amount = sum(item.line_total for item in items)
        total = OrderTotal(amount=total_amount, currency=currency)

        now = datetime.now(timezone.utc)
        order = cls(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            items=items,
            status=OrderStatus.PLACED,
            total=total,
            notes=notes.strip() if notes else "",
            created_at=now,
            updated_at=now,
        )

        order.record_event(
            OrderPlacedEvent(
                order_id=order.id,
                customer_id=customer_id.value,
                items=tuple(
                    OrderItemData(
                        dish_id=item.dish_id,
                        dish_name=item.dish_name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                    )
                    for item in items
                ),
                total_amount=total.amount,
                currency=total.currency,
            )
        )
        return order

    # ------------------------------------------------------------------
    # Factory: reconstitute from persistence (NO validation, NO events)
    # ------------------------------------------------------------------
    @classmethod
    def reconstitute(
        cls,
        *,
        order_id: str,
        customer_id: str,
        items: List[OrderItem],
        status: str,
        total_amount: Decimal,
        total_currency: str,
        notes: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> Order:
        """Rebuild an Order from stored data without triggering business rules."""
        order = cls.__new__(cls)
        order.id = order_id
        order.customer_id = CustomerId(customer_id)
        order.items = items
        order.status = OrderStatus(status)
        order.total = OrderTotal(amount=total_amount, currency=total_currency)
        order.notes = notes
        order.created_at = created_at
        order.updated_at = updated_at
        order._events = []
        return order

    # ------------------------------------------------------------------
    # Commands (state transitions)
    # ------------------------------------------------------------------
    def _transition_to(self, target: OrderStatus) -> None:
        """Enforce the state machine."""
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if target not in allowed:
            raise InvalidOrderTransitionError(self.status.value, target.value)
        self.status = target
        self.updated_at = datetime.now(timezone.utc)

    def confirm(self) -> None:
        """Seller confirms the order."""
        self._transition_to(OrderStatus.CONFIRMED)
        self.record_event(
            OrderConfirmedEvent(
                order_id=self.id,
                customer_id=self.customer_id.value,
            )
        )

    def start_preparing(self) -> None:
        """Seller starts preparing the order."""
        self._transition_to(OrderStatus.PREPARING)

    def mark_ready(self) -> None:
        """Seller marks the order as ready for pickup."""
        self._transition_to(OrderStatus.READY)
        self.record_event(
            OrderReadyEvent(
                order_id=self.id,
                customer_id=self.customer_id.value,
            )
        )

    def pick_up(self) -> None:
        """Customer picks up the order."""
        self._transition_to(OrderStatus.PICKED_UP)
        self.record_event(
            OrderPickedUpEvent(
                order_id=self.id,
                customer_id=self.customer_id.value,
            )
        )

    def cancel(self, reason: str = "") -> None:
        """Cancel the order — only allowed from PLACED or CONFIRMED."""
        if self.status == OrderStatus.CANCELLED:
            raise OrderAlreadyCancelledError(self.id)
        self._transition_to(OrderStatus.CANCELLED)
        self.record_event(
            OrderCancelledEvent(
                order_id=self.id,
                customer_id=self.customer_id.value,
                items=tuple(
                    OrderItemData(
                        dish_id=item.dish_id,
                        dish_name=item.dish_name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                    )
                    for item in self.items
                ),
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    @property
    def is_active(self) -> bool:
        """An order is active if it hasn't reached a terminal state."""
        return self.status not in (OrderStatus.PICKED_UP, OrderStatus.CANCELLED)
