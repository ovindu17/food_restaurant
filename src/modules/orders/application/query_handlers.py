"""
Query Handlers — read-only operations that return DTOs.

These bypass the Unit of Work because they don't mutate state.
"""

from __future__ import annotations

from typing import List

from src.modules.orders.application.commands import GetOrderQuery, ListCustomerOrdersQuery
from src.modules.orders.application.dtos import OrderItemDTO, OrderResponseDTO
from src.modules.orders.domain.exceptions import OrderNotFoundError
from src.modules.orders.domain.repositories import OrderRepository
from src.modules.orders.domain.value_objects import CustomerId, OrderId


def _to_dto(order) -> OrderResponseDTO:
    return OrderResponseDTO(
        id=order.id,
        customer_id=order.customer_id.value,
        items=[
            OrderItemDTO(
                id=item.id,
                dish_id=item.dish_id,
                dish_name=item.dish_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                currency=item.currency,
                line_total=item.line_total,
            )
            for item in order.items
        ],
        status=order.status.value,
        total_amount=order.total.amount,
        currency=order.total.currency,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


class GetOrderHandler:
    def __init__(self, repository: OrderRepository) -> None:
        self._repo = repository

    def handle(self, query: GetOrderQuery) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(query.order_id))
        if order is None:
            raise OrderNotFoundError(query.order_id)
        return _to_dto(order)


class ListCustomerOrdersHandler:
    def __init__(self, repository: OrderRepository) -> None:
        self._repo = repository

    def handle(self, query: ListCustomerOrdersQuery) -> List[OrderResponseDTO]:
        orders = self._repo.list_by_customer(CustomerId(query.customer_id))
        return [_to_dto(o) for o in orders]
