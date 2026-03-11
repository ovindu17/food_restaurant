"""
Domain Events emitted by the Order aggregate.

Other modules (Catalog, Notifications, etc.) subscribe to these events
through the shared EventBus — they never import Orders internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

from src.shared.domain.base import DomainEvent


@dataclass(frozen=True)
class OrderItemData:
    """Lightweight data carrier embedded in order events."""

    dish_id: str
    dish_name: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class OrderPlacedEvent(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    items: tuple[OrderItemData, ...] = ()
    total_amount: Decimal = Decimal("0")
    currency: str = "USD"


@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    order_id: str = ""
    customer_id: str = ""


@dataclass(frozen=True)
class OrderCancelledEvent(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
    items: tuple[OrderItemData, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class OrderReadyEvent(DomainEvent):
    order_id: str = ""
    customer_id: str = ""


@dataclass(frozen=True)
class OrderPickedUpEvent(DomainEvent):
    order_id: str = ""
    customer_id: str = ""
