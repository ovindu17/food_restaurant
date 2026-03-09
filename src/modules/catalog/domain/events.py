"""
Domain Events emitted by the Catalog aggregate.

Other modules (Orders, Notifications, etc.) subscribe to these events
through the shared EventBus — they never import Catalog internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.shared.domain.base import DomainEvent


@dataclass(frozen=True)
class DishCreatedEvent(DomainEvent):
    dish_id: str
    seller_id: str
    name: str
    price: Decimal
    available_portions: int


@dataclass(frozen=True)
class DishPriceChangedEvent(DomainEvent):
    dish_id: str
    old_price: Decimal
    new_price: Decimal


@dataclass(frozen=True)
class DishDeactivatedEvent(DomainEvent):
    dish_id: str
    seller_id: str


@dataclass(frozen=True)
class PortionsDeductedEvent(DomainEvent):
    dish_id: str
    deducted: int
    remaining: int


@dataclass(frozen=True)
class PortionsExhaustedEvent(DomainEvent):
    """Emitted when a dish runs out of portions — useful for notifications."""
    dish_id: str
    seller_id: str
