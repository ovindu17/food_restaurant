"""
Command Handlers — orchestrate the domain to fulfil write operations.

Each handler:
  1. Receives a Command DTO.
  2. Loads / creates domain aggregates.
  3. Invokes domain behaviour.
  4. Persists via the repository.
  5. Returns a response DTO.

The Unit of Work commits the transaction and publishes domain events.
"""

from __future__ import annotations

from src.modules.catalog.application.commands import (
    ChangeDishPriceCommand,
    CreateDishCommand,
    DeactivateDishCommand,
    DeductPortionsCommand,
)
from src.modules.catalog.application.dtos import DishResponseDTO
from src.modules.catalog.domain.entities import Dish
from src.modules.catalog.domain.exceptions import (
    DishNotFoundError,
    SellerDishLimitExceededError,
)
from src.modules.catalog.domain.repositories import DishRepository
from src.modules.catalog.domain.value_objects import DishId, Money, Portions, SellerId
from src.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

MAX_ACTIVE_DISHES_PER_SELLER = 50


def _to_dto(dish: Dish) -> DishResponseDTO:
    return DishResponseDTO(
        id=dish.id,
        seller_id=dish.seller_id.value,
        name=dish.name,
        description=dish.description,
        price=dish.price.amount,
        currency=dish.price.currency,
        available_portions=dish.portions.value,
        is_active=dish.is_active,
        created_at=dish.created_at,
    )


# ---------------------------------------------------------------------------
# Create Dish
# ---------------------------------------------------------------------------
class CreateDishHandler:
    def __init__(self, repository: DishRepository, uow: SqlAlchemyUnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: CreateDishCommand) -> DishResponseDTO:
        seller_id = SellerId(command.seller_id)

        # Enforce aggregate-level invariant: max active dishes per seller
        active_count = self._repo.count_active_by_seller(seller_id)
        if active_count >= MAX_ACTIVE_DISHES_PER_SELLER:
            raise SellerDishLimitExceededError(
                command.seller_id, MAX_ACTIVE_DISHES_PER_SELLER
            )

        dish = Dish.create(
            seller_id=seller_id,
            name=command.name,
            description=command.description,
            price=Money(amount=command.price, currency=command.currency),
            portions=Portions(value=command.initial_portions),
        )

        self._repo.add(dish)
        self._uow.register_aggregate(dish)
        self._uow.commit()

        return _to_dto(dish)


# ---------------------------------------------------------------------------
# Deactivate Dish
# ---------------------------------------------------------------------------
class DeactivateDishHandler:
    def __init__(self, repository: DishRepository, uow: SqlAlchemyUnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: DeactivateDishCommand) -> DishResponseDTO:
        dish = self._repo.get_by_id(DishId(command.dish_id))
        if dish is None:
            raise DishNotFoundError(command.dish_id)

        dish.deactivate()

        self._repo.update(dish)
        self._uow.register_aggregate(dish)
        self._uow.commit()

        return _to_dto(dish)


# ---------------------------------------------------------------------------
# Change Price
# ---------------------------------------------------------------------------
class ChangeDishPriceHandler:
    def __init__(self, repository: DishRepository, uow: SqlAlchemyUnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: ChangeDishPriceCommand) -> DishResponseDTO:
        dish = self._repo.get_by_id(DishId(command.dish_id))
        if dish is None:
            raise DishNotFoundError(command.dish_id)

        dish.change_price(Money(amount=command.new_price, currency=command.currency))

        self._repo.update(dish)
        self._uow.register_aggregate(dish)
        self._uow.commit()

        return _to_dto(dish)


# ---------------------------------------------------------------------------
# Deduct Portions
# ---------------------------------------------------------------------------
class DeductPortionsHandler:
    def __init__(self, repository: DishRepository, uow: SqlAlchemyUnitOfWork) -> None:
        self._repo = repository
        self._uow = uow

    def handle(self, command: DeductPortionsCommand) -> DishResponseDTO:
        dish = self._repo.get_by_id(DishId(command.dish_id))
        if dish is None:
            raise DishNotFoundError(command.dish_id)

        dish.deduct_portions(command.amount)

        self._repo.update(dish)
        self._uow.register_aggregate(dish)
        self._uow.commit()

        return _to_dto(dish)
