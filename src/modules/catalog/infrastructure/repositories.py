"""
Concrete repository backed by PostgreSQL via SQLAlchemy.

Key design decisions:
  - ``add`` and ``update`` are separate methods (no silent upsert).
  - ``_to_domain`` uses ``Dish.reconstitute`` so that business-rule
    validation and domain events are NOT re-triggered on read.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.catalog.domain.entities import Dish
from src.modules.catalog.domain.repositories import DishRepository
from src.modules.catalog.domain.value_objects import DishId, SellerId
from src.modules.catalog.infrastructure.models import DishModel


class PostgresDishRepository(DishRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, dish: Dish) -> None:
        db_model = self._to_model(dish)
        self._session.add(db_model)
        self._session.flush()  # assign DB-level defaults, detect conflicts

    def update(self, dish: Dish) -> None:
        db_model = (
            self._session.query(DishModel)
            .filter(DishModel.id == dish.id)
            .first()
        )
        if db_model is None:
            raise RuntimeError(f"Cannot update non-existent dish {dish.id}")

        db_model.seller_id = dish.seller_id.value
        db_model.name = dish.name
        db_model.description = dish.description
        db_model.price_amount = dish.price.amount
        db_model.price_currency = dish.price.currency
        db_model.available_portions = dish.portions.value
        db_model.is_active = dish.is_active
        db_model.created_at = dish.created_at
        self._session.flush()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_by_id(self, dish_id: DishId) -> Optional[Dish]:
        row = (
            self._session.query(DishModel)
            .filter(DishModel.id == dish_id.value)
            .first()
        )
        return self._to_domain(row) if row else None

    def list_active_by_seller(self, seller_id: SellerId) -> List[Dish]:
        rows = (
            self._session.query(DishModel)
            .filter(
                DishModel.seller_id == seller_id.value,
                DishModel.is_active.is_(True),
            )
            .order_by(DishModel.created_at.desc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def count_active_by_seller(self, seller_id: SellerId) -> int:
        return (
            self._session.query(DishModel)
            .filter(
                DishModel.seller_id == seller_id.value,
                DishModel.is_active.is_(True),
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_model(dish: Dish) -> DishModel:
        return DishModel(
            id=dish.id,
            seller_id=dish.seller_id.value,
            name=dish.name,
            description=dish.description,
            price_amount=dish.price.amount,
            price_currency=dish.price.currency,
            available_portions=dish.portions.value,
            is_active=dish.is_active,
            created_at=dish.created_at,
        )

    @staticmethod
    def _to_domain(model: DishModel) -> Dish:
        return Dish.reconstitute(
            dish_id=model.id,
            seller_id=model.seller_id,
            name=model.name,
            description=model.description,
            price_amount=Decimal(str(model.price_amount)),
            price_currency=model.price_currency,
            available_portions=model.available_portions,
            is_active=model.is_active,
            created_at=model.created_at,
        )
