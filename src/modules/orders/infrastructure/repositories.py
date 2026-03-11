"""
Concrete repository backed by PostgreSQL via SQLAlchemy.

Key design decisions:
  - ``add`` and ``update`` are separate methods (no silent upsert).
  - ``_to_domain`` uses ``Order.reconstitute`` so that business-rule
    validation and domain events are NOT re-triggered on read.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.orders.domain.entities import Order, OrderItem
from src.modules.orders.domain.repositories import OrderRepository
from src.modules.orders.domain.value_objects import CustomerId, OrderId, OrderStatus
from src.modules.orders.infrastructure.models import OrderItemModel, OrderModel


class PostgresOrderRepository(OrderRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, order: Order) -> None:
        db_model = self._to_model(order)
        self._session.add(db_model)
        self._session.flush()

    def update(self, order: Order) -> None:
        db_model = (
            self._session.query(OrderModel)
            .filter(OrderModel.id == order.id)
            .first()
        )
        if db_model is None:
            raise RuntimeError(f"Cannot update non-existent order {order.id}")

        db_model.customer_id = order.customer_id.value
        db_model.status = order.status.value
        db_model.total_amount = order.total.amount
        db_model.total_currency = order.total.currency
        db_model.notes = order.notes
        db_model.created_at = order.created_at
        db_model.updated_at = order.updated_at

        # Sync items: remove existing, add current
        db_model.items.clear()
        for item in order.items:
            db_model.items.append(
                OrderItemModel(
                    id=item.id,
                    order_id=order.id,
                    dish_id=item.dish_id,
                    dish_name=item.dish_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    currency=item.currency,
                )
            )
        self._session.flush()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_by_id(self, order_id: OrderId) -> Optional[Order]:
        row = (
            self._session.query(OrderModel)
            .filter(OrderModel.id == order_id.value)
            .first()
        )
        return self._to_domain(row) if row else None

    def list_by_customer(self, customer_id: CustomerId) -> List[Order]:
        rows = (
            self._session.query(OrderModel)
            .filter(OrderModel.customer_id == customer_id.value)
            .order_by(OrderModel.created_at.desc())
            .all()
        )
        return [self._to_domain(r) for r in rows]

    def count_active_by_customer(self, customer_id: CustomerId) -> int:
        terminal_statuses = (
            OrderStatus.PICKED_UP.value,
            OrderStatus.CANCELLED.value,
        )
        return (
            self._session.query(OrderModel)
            .filter(
                OrderModel.customer_id == customer_id.value,
                OrderModel.status.notin_(terminal_statuses),
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_model(order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            customer_id=order.customer_id.value,
            status=order.status.value,
            total_amount=order.total.amount,
            total_currency=order.total.currency,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[
                OrderItemModel(
                    id=item.id,
                    order_id=order.id,
                    dish_id=item.dish_id,
                    dish_name=item.dish_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    currency=item.currency,
                )
                for item in order.items
            ],
        )

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        items = [
            OrderItem(
                id=item_model.id,
                dish_id=item_model.dish_id,
                dish_name=item_model.dish_name,
                quantity=item_model.quantity,
                unit_price=Decimal(str(item_model.unit_price)),
                currency=item_model.currency,
            )
            for item_model in model.items
        ]
        return Order.reconstitute(
            order_id=model.id,
            customer_id=model.customer_id,
            items=items,
            status=model.status,
            total_amount=Decimal(str(model.total_amount)),
            total_currency=model.total_currency,
            notes=model.notes or "",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
