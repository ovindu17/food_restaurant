"""
Orders Module — Public Facade.

Other modules in the monolith interact with Orders ONLY through this
facade.  They must never import from ``orders.domain``,
``orders.infrastructure``, or ``orders.presentation`` directly.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.orders.application.commands import GetOrderQuery, ListCustomerOrdersQuery
from src.modules.orders.application.dtos import OrderResponseDTO
from src.modules.orders.application.query_handlers import (
    GetOrderHandler,
    ListCustomerOrdersHandler,
)
from src.modules.orders.infrastructure.repositories import PostgresOrderRepository


class OrdersFacade:
    """
    Inter-module API for the Orders bounded context.

    Example usage from another module:

        orders = OrdersFacade(session=db)
        order = orders.get_order(order_id="...")
    """

    def __init__(self, session: Session) -> None:
        self._repo = PostgresOrderRepository(session)

    def get_order(self, order_id: str) -> Optional[OrderResponseDTO]:
        """Return order details or ``None``."""
        handler = GetOrderHandler(repository=self._repo)
        return handler.handle(GetOrderQuery(order_id=order_id))

    def list_customer_orders(self, customer_id: str) -> List[OrderResponseDTO]:
        """Return all orders for a customer."""
        handler = ListCustomerOrdersHandler(repository=self._repo)
        return handler.handle(ListCustomerOrdersQuery(customer_id=customer_id))
