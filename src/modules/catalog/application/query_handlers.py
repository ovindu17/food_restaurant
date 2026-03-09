"""
Query Handlers — read-only operations that return DTOs.

These bypass the Unit of Work because they don't mutate state.
"""

from __future__ import annotations

from typing import List

from src.modules.catalog.application.commands import GetDishQuery, ListSellerDishesQuery
from src.modules.catalog.application.dtos import DishResponseDTO
from src.modules.catalog.domain.exceptions import DishNotFoundError
from src.modules.catalog.domain.repositories import DishRepository
from src.modules.catalog.domain.value_objects import DishId, SellerId


def _to_dto(dish) -> DishResponseDTO:
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


class GetDishHandler:
    def __init__(self, repository: DishRepository) -> None:
        self._repo = repository

    def handle(self, query: GetDishQuery) -> DishResponseDTO:
        dish = self._repo.get_by_id(DishId(query.dish_id))
        if dish is None:
            raise DishNotFoundError(query.dish_id)
        return _to_dto(dish)


class ListSellerDishesHandler:
    def __init__(self, repository: DishRepository) -> None:
        self._repo = repository

    def handle(self, query: ListSellerDishesQuery) -> List[DishResponseDTO]:
        dishes = self._repo.list_active_by_seller(SellerId(query.seller_id))
        return [_to_dto(d) for d in dishes]
