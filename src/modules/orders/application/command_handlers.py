"""
Command Handlers — orchestrate the domain to fulfil write operations.

Each handler:
  1. Receives a Command DTO.
  2. Loads / creates domain aggregates.
  3. Invokes domain behaviour.
  4. Persists via the repository.
  5. Returns a response DTO.

The Unit of Work commits the transaction and publishes domain events.

Cross-module communication happens through the CatalogFacade — the
Orders module never imports Catalog internals.
"""

from __future__ import annotations

from decimal import Decimal

from src.modules.catalog import CatalogFacade
from src.modules.orders.application.commands import (
    CancelOrderCommand,
    ConfirmOrderCommand,
    MarkReadyCommand,
    PickUpOrderCommand,
    PlaceOrderCommand,
    StartPreparingCommand,
)
from src.modules.orders.application.dtos import OrderItemDTO, OrderResponseDTO
from src.modules.orders.domain.entities import Order, OrderItem
from src.modules.orders.domain.exceptions import (
    DishUnavailableError,
    OrderNotFoundError,
    TooManyActiveOrdersError,
)
from src.modules.orders.domain.repositories import OrderRepository
from src.modules.orders.domain.value_objects import CustomerId, OrderId
from src.shared.domain.unit_of_work import UnitOfWork

MAX_ACTIVE_ORDERS_PER_CUSTOMER = 5


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------
def _to_dto(order: Order) -> OrderResponseDTO:
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


# ---------------------------------------------------------------------------
# Place Order
# ---------------------------------------------------------------------------
class PlaceOrderHandler:
    def __init__(
        self,
        repository: OrderRepository,
        uow: UnitOfWork,
        catalog: CatalogFacade,
    ) -> None:
        self._repo = repository
        self._uow = uow
        self._catalog = catalog

    def handle(self, command: PlaceOrderCommand) -> OrderResponseDTO:
        customer_id = CustomerId(command.customer_id)

        # Enforce max active orders per customer
        active_count = self._repo.count_active_by_customer(customer_id)
        if active_count >= MAX_ACTIVE_ORDERS_PER_CUSTOMER:
            raise TooManyActiveOrdersError(
                command.customer_id, MAX_ACTIVE_ORDERS_PER_CUSTOMER
            )

        # Validate each dish via the Catalog facade and snapshot the price
        order_items: list[OrderItem] = []
        for item_input in command.items:
            dish = self._catalog.get_dish(item_input.dish_id)
            if dish is None or not dish.is_active:
                raise DishUnavailableError(item_input.dish_id, "not found or inactive")

            order_items.append(
                OrderItem.create(
                    dish_id=dish.id,
                    dish_name=dish.name,
                    quantity=item_input.quantity,
                    unit_price=dish.price,
                    currency=dish.currency,
                )
            )

        # Deduct portions for every item via the Catalog facade
        for item_input, order_item in zip(command.items, order_items):
            self._catalog.deduct_portions(
                dish_id=order_item.dish_id,
                amount=item_input.quantity,
            )

        # Create the Order aggregate
        order = Order.create(
            customer_id=customer_id,
            items=order_items,
            notes=command.notes,
        )

        self._repo.add(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)


# ---------------------------------------------------------------------------
# Confirm Order
# ---------------------------------------------------------------------------
class ConfirmOrderHandler:
    def __init__(self, repository: OrderRepository, uow: UnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: ConfirmOrderCommand) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(command.order_id))
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.confirm()

        self._repo.update(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)


# ---------------------------------------------------------------------------
# Cancel Order
# ---------------------------------------------------------------------------
class CancelOrderHandler:
    def __init__(self, repository: OrderRepository, uow: UnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: CancelOrderCommand) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(command.order_id))
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.cancel(reason=command.reason)

        self._repo.update(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)


# ---------------------------------------------------------------------------
# Start Preparing
# ---------------------------------------------------------------------------
class StartPreparingHandler:
    def __init__(self, repository: OrderRepository, uow: UnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: StartPreparingCommand) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(command.order_id))
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.start_preparing()

        self._repo.update(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)


# ---------------------------------------------------------------------------
# Mark Ready
# ---------------------------------------------------------------------------
class MarkReadyHandler:
    def __init__(self, repository: OrderRepository, uow: UnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: MarkReadyCommand) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(command.order_id))
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.mark_ready()

        self._repo.update(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)


# ---------------------------------------------------------------------------
# Pick Up Order
# ---------------------------------------------------------------------------
class PickUpOrderHandler:
    def __init__(self, repository: OrderRepository, uow: UnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: PickUpOrderCommand) -> OrderResponseDTO:
        order = self._repo.get_by_id(OrderId(command.order_id))
        if order is None:
            raise OrderNotFoundError(command.order_id)

        order.pick_up()

        self._repo.update(order)
        self._uow.register_aggregate(order)
        self._uow.commit()

        return _to_dto(order)
