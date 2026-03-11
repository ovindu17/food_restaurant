"""
Repository port for the Order aggregate.

This is a *domain* contract — it knows nothing about SQL, ORMs, or
any other infrastructure detail.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.orders.domain.entities import Order
from src.modules.orders.domain.value_objects import CustomerId, OrderId


class OrderRepository(ABC):

    @abstractmethod
    def add(self, order: Order) -> None:
        """Persist a brand-new order."""

    @abstractmethod
    def update(self, order: Order) -> None:
        """Persist changes to an existing order."""

    @abstractmethod
    def get_by_id(self, order_id: OrderId) -> Optional[Order]:
        """Return an order by its ID, or ``None``."""

    @abstractmethod
    def list_by_customer(self, customer_id: CustomerId) -> List[Order]:
        """Return all orders for a given customer."""

    @abstractmethod
    def count_active_by_customer(self, customer_id: CustomerId) -> int:
        """Return the number of active (non-terminal) orders for a customer."""
