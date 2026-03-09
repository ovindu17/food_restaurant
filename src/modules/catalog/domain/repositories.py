"""
Repository port for the Dish aggregate.

This is a *domain* contract — it knows nothing about SQL, ORMs, or
any other infrastructure detail.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.catalog.domain.entities import Dish
from src.modules.catalog.domain.value_objects import DishId, SellerId


class DishRepository(ABC):

    @abstractmethod
    def add(self, dish: Dish) -> None:
        """Persist a brand-new dish."""

    @abstractmethod
    def update(self, dish: Dish) -> None:
        """Persist changes to an existing dish."""

    @abstractmethod
    def get_by_id(self, dish_id: DishId) -> Optional[Dish]:
        """Return a dish by its ID, or ``None``."""

    @abstractmethod
    def list_active_by_seller(self, seller_id: SellerId) -> List[Dish]:
        """Return all active dishes for a given seller."""

    @abstractmethod
    def count_active_by_seller(self, seller_id: SellerId) -> int:
        """Return the number of active dishes a seller currently has."""
