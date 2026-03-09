"""
Catalog Module — Public Facade.

Other modules in the monolith (e.g. Orders, Notifications) interact
with the Catalog ONLY through this facade.  They must never import
from ``catalog.domain``, ``catalog.infrastructure``, or
``catalog.presentation`` directly.

This keeps modules loosely coupled — if the Catalog's internals change,
the facade's contract stays stable.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.catalog.application.commands import (
    DeductPortionsCommand,
    GetDishQuery,
)
from src.modules.catalog.application.command_handlers import DeductPortionsHandler
from src.modules.catalog.application.dtos import DishResponseDTO
from src.modules.catalog.application.query_handlers import GetDishHandler
from src.modules.catalog.infrastructure.repositories import PostgresDishRepository
from src.shared.domain.event_bus import EventBus
from src.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class CatalogFacade:
    """
    Inter-module API for the Catalog bounded context.

    Example usage from the Orders module:

        catalog = CatalogFacade(session=db, event_bus=bus)
        catalog.deduct_portions(dish_id="...", amount=2)
    """

    def __init__(self, session: Session, event_bus: EventBus) -> None:
        self._repo = PostgresDishRepository(session)
        self._uow = SqlAlchemyUnitOfWork(session=session, event_bus=event_bus)

    def get_dish(self, dish_id: str) -> Optional[DishResponseDTO]:
        """Return dish details or ``None``."""
        handler = GetDishHandler(repository=self._repo)
        return handler.handle(GetDishQuery(dish_id=dish_id))

    def deduct_portions(self, dish_id: str, amount: int) -> DishResponseDTO:
        """Deduct portions — called by the Orders module during checkout."""
        handler = DeductPortionsHandler(repository=self._repo, uow=self._uow)
        return handler.handle(DeductPortionsCommand(dish_id=dish_id, amount=amount))
