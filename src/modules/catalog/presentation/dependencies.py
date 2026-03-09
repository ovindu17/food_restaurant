"""
FastAPI dependency injection wiring for the Catalog module.

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
from src.modules.catalog.application.command_handlers import (
    ChangeDishPriceHandler,
    CreateDishHandler,
    DeactivateDishHandler,
    DeductPortionsHandler,
)
from src.modules.catalog.application.query_handlers import (
    GetDishHandler,
    ListSellerDishesHandler,
)
from src.modules.catalog.infrastructure.repositories import PostgresDishRepository


# ---------------------------------------------------------------------------
# Singletons (module-level)
# ---------------------------------------------------------------------------
_event_bus = InMemoryEventBus()


def get_event_bus() -> EventBus:
    return _event_bus


# ---------------------------------------------------------------------------
# Per-request dependencies
# ---------------------------------------------------------------------------
def get_dish_repository(
    db: Session = Depends(get_db),
) -> PostgresDishRepository:
    return PostgresDishRepository(session=db)


def get_unit_of_work(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session=db, event_bus=event_bus)


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------
def get_create_dish_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> CreateDishHandler:
    return CreateDishHandler(repository=repo, uow=uow)


def get_deactivate_dish_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> DeactivateDishHandler:
    return DeactivateDishHandler(repository=repo, uow=uow)


def get_change_price_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> ChangeDishPriceHandler:
    return ChangeDishPriceHandler(repository=repo, uow=uow)


def get_deduct_portions_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
    uow: SqlAlchemyUnitOfWork = Depends(get_unit_of_work),
) -> DeductPortionsHandler:
    return DeductPortionsHandler(repository=repo, uow=uow)


# ---------------------------------------------------------------------------
# Query Handlers
# ---------------------------------------------------------------------------
def get_get_dish_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
) -> GetDishHandler:
    return GetDishHandler(repository=repo)


def get_list_seller_dishes_handler(
    repo: PostgresDishRepository = Depends(get_dish_repository),
) -> ListSellerDishesHandler:
    return ListSellerDishesHandler(repository=repo)
