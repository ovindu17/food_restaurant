"""
FastAPI dependency injection wiring for the Orders module.

Each dependency function constructs exactly one object and declares its
own upstream dependencies — FastAPI resolves the graph automatically.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from src.shared.domain.event_bus import EventBus
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.event_bus import InMemoryEventBus
from src.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from src.modules.catalog import CatalogFacade
from src.modules.orders.application.command_handlers import (
    CancelOrderHandler,
    ConfirmOrderHandler,
    MarkReadyHandler,
    PickUpOrderHandler,
    PlaceOrderHandler,
    StartPreparingHandler,
)
from src.modules.orders.application.query_handlers import (
    GetOrderHandler,
    ListCustomerOrdersHandler,
)
from src.modules.orders.infrastructure.repositories import PostgresOrderRepository


# ---------------------------------------------------------------------------
# Singletons (module-level)
# ---------------------------------------------------------------------------
_event_bus = InMemoryEventBus()


def get_event_bus() -> EventBus:
    return _event_bus


# ---------------------------------------------------------------------------
# Per-request dependencies
# ---------------------------------------------------------------------------
def get_order_repository(
    db: Session = Depends(get_db),
) -> PostgresOrderRepository:
    return PostgresOrderRepository(session=db)


def get_unit_of_work(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session=db, event_bus=event_bus)


def get_catalog_facade(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> CatalogFacade:
    return CatalogFacade(session=db, event_bus=event_bus)


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------
def get_place_order_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
    catalog: CatalogFacade = Depends(get_catalog_facade),
) -> PlaceOrderHandler:
    return PlaceOrderHandler(repository=repo, uow=uow, catalog=catalog)


def get_confirm_order_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> ConfirmOrderHandler:
    return ConfirmOrderHandler(repository=repo, uow=uow)


def get_cancel_order_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CancelOrderHandler:
    return CancelOrderHandler(repository=repo, uow=uow)


def get_start_preparing_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> StartPreparingHandler:
    return StartPreparingHandler(repository=repo, uow=uow)


def get_mark_ready_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> MarkReadyHandler:
    return MarkReadyHandler(repository=repo, uow=uow)


def get_pick_up_order_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> PickUpOrderHandler:
    return PickUpOrderHandler(repository=repo, uow=uow)


# ---------------------------------------------------------------------------
# Query Handlers
# ---------------------------------------------------------------------------
def get_get_order_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
) -> GetOrderHandler:
    return GetOrderHandler(repository=repo)


def get_list_customer_orders_handler(
    repo: PostgresOrderRepository = Depends(get_order_repository),
) -> ListCustomerOrdersHandler:
    return ListCustomerOrdersHandler(repository=repo)
