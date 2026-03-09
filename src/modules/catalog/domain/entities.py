"""
Dish — the Aggregate Root for the Catalog bounded context.

All mutations go through public methods that enforce invariants and
record domain events. No external code should mutate fields directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.shared.domain.base import AggregateRoot
from src.modules.catalog.domain.exceptions import (
    DishAlreadyDeactivatedError,
    InsufficientPortionsError,
    InvalidPriceError,
)
from src.modules.catalog.domain.events import (
    DishCreatedEvent,
    DishDeactivatedEvent,
    DishPriceChangedEvent,
    PortionsDeductedEvent,
    PortionsExhaustedEvent,
)
from src.modules.catalog.domain.value_objects import DishId, Money, Portions, SellerId


@dataclass
class Dish(AggregateRoot):
    """
    Aggregate Root representing a dish listed by a seller.

    Use the ``create`` class method to build new instances — it enforces
    all creation-time invariants and records a ``DishCreatedEvent``.

    Use the ``reconstitute`` class method when loading from persistence
    so that validation and events are **not** re-triggered.
    """

    seller_id: SellerId = field(default_factory=lambda: SellerId("unset"))
    name: str = ""
    description: str = ""
    price: Money = field(default_factory=lambda: Money(amount=1))
    portions: Portions = field(default_factory=lambda: Portions(value=0))
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------
    # Factory: new dish
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        seller_id: SellerId,
        name: str,
        description: str,
        price: Money,
        portions: Portions,
    ) -> Dish:
        """
        Named constructor enforcing creation invariants.
        Records a ``DishCreatedEvent``.
        """
        if not name or not name.strip():
            raise ValueError("Dish name cannot be empty.")
        if len(name) > 100:
            raise ValueError("Dish name must be 100 characters or fewer.")

        dish = cls(
            id=str(uuid.uuid4()),
            seller_id=seller_id,
            name=name.strip(),
            description=description.strip() if description else "",
            price=price,
            portions=portions,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        dish.record_event(
            DishCreatedEvent(
                dish_id=dish.id,
                seller_id=seller_id.value,
                name=dish.name,
                price=price.amount,
                available_portions=portions.value,
            )
        )
        return dish

    # ------------------------------------------------------------------
    # Factory: reconstitute from persistence (NO validation, NO events)
    # ------------------------------------------------------------------
    @classmethod
    def reconstitute(
        cls,
        *,
        dish_id: str,
        seller_id: str,
        name: str,
        description: str,
        price_amount: "Decimal",  # noqa: F821
        price_currency: str,
        available_portions: int,
        is_active: bool,
        created_at: datetime,
    ) -> Dish:
        """
        Rebuild a Dish from stored data without triggering business rules
        or emitting events.
        """
        dish = cls.__new__(cls)
        dish.id = dish_id
        dish.seller_id = SellerId(seller_id)
        dish.name = name
        dish.description = description
        # Use object.__setattr__ dance inside frozen VO? No — Money is frozen
        # but we build a *new* one here which is fine.
        dish.price = Money(amount=price_amount, currency=price_currency)
        dish.portions = Portions(value=available_portions)
        dish.is_active = is_active
        dish.created_at = created_at
        dish._events = []
        return dish

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    def change_price(self, new_price: Money) -> None:
        old = self.price
        self.price = new_price
        self.record_event(
            DishPriceChangedEvent(
                dish_id=self.id,
                old_price=old.amount,
                new_price=new_price.amount,
            )
        )

    def deduct_portions(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Deduction amount must be positive.")
        if self.portions.value < amount:
            raise InsufficientPortionsError(
                requested=amount,
                available=self.portions.value,
            )

        self.portions = self.portions.deduct(amount)

        self.record_event(
            PortionsDeductedEvent(
                dish_id=self.id,
                deducted=amount,
                remaining=self.portions.value,
            )
        )

        if self.portions.is_exhausted():
            self.record_event(
                PortionsExhaustedEvent(
                    dish_id=self.id,
                    seller_id=self.seller_id.value,
                )
            )

    def deactivate(self) -> None:
        if not self.is_active:
            raise DishAlreadyDeactivatedError(self.id)
        self.is_active = False
        self.record_event(
            DishDeactivatedEvent(
                dish_id=self.id,
                seller_id=self.seller_id.value,
            )
        )
