"""
HTTP endpoints for the Catalog module.

Endpoints are thin — they validate input via Pydantic, delegate to
Application-layer handlers, and return response schemas.  Exception
mapping is handled globally by ``catalog_exception_handler``.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status

from src.modules.catalog.application.command_handlers import (
    ChangeDishPriceHandler,
    CreateDishHandler,
    DeactivateDishHandler,
    DeductPortionsHandler,
)
from src.modules.catalog.application.commands import (
    ChangeDishPriceCommand,
    CreateDishCommand,
    DeactivateDishCommand,
    DeductPortionsCommand,
    GetDishQuery,
    ListSellerDishesQuery,
)
from src.modules.catalog.application.query_handlers import (
    GetDishHandler,
    ListSellerDishesHandler,
)
from src.modules.catalog.presentation.dependencies import (
    get_change_price_handler,
    get_create_dish_handler,
    get_deactivate_dish_handler,
    get_deduct_portions_handler,
    get_get_dish_handler,
    get_list_seller_dishes_handler,
)
from src.modules.catalog.presentation.schemas import (
    ChangePriceRequest,
    CreateDishRequest,
    DeductPortionsRequest,
    DishResponse,
)

router = APIRouter(prefix="/catalog/dishes", tags=["Catalog"])


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=DishResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dish",
)
def create_dish(
    body: CreateDishRequest,
    handler: CreateDishHandler = Depends(get_create_dish_handler),
) -> DishResponse:
    command = CreateDishCommand(
        seller_id=body.seller_id,
        name=body.name,
        description=body.description,
        price=body.price,
        currency=body.currency,
        initial_portions=body.initial_portions,
    )
    result = handler.handle(command)
    return DishResponse(**result.__dict__)


@router.patch(
    "/{dish_id}/deactivate",
    response_model=DishResponse,
    summary="Deactivate (soft-delete) a dish",
)
def deactivate_dish(
    dish_id: str,
    handler: DeactivateDishHandler = Depends(get_deactivate_dish_handler),
) -> DishResponse:
    result = handler.handle(DeactivateDishCommand(dish_id=dish_id))
    return DishResponse(**result.__dict__)


@router.patch(
    "/{dish_id}/price",
    response_model=DishResponse,
    summary="Change the price of a dish",
)
def change_price(
    dish_id: str,
    body: ChangePriceRequest,
    handler: ChangeDishPriceHandler = Depends(get_change_price_handler),
) -> DishResponse:
    command = ChangeDishPriceCommand(
        dish_id=dish_id,
        new_price=body.new_price,
        currency=body.currency,
    )
    result = handler.handle(command)
    return DishResponse(**result.__dict__)


@router.post(
    "/{dish_id}/deduct-portions",
    response_model=DishResponse,
    summary="Deduct portions from a dish (called by the Orders module)",
)
def deduct_portions(
    dish_id: str,
    body: DeductPortionsRequest,
    handler: DeductPortionsHandler = Depends(get_deduct_portions_handler),
) -> DishResponse:
    command = DeductPortionsCommand(dish_id=dish_id, amount=body.amount)
    result = handler.handle(command)
    return DishResponse(**result.__dict__)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
@router.get(
    "/{dish_id}",
    response_model=DishResponse,
    summary="Get a single dish by ID",
)
def get_dish(
    dish_id: str,
    handler: GetDishHandler = Depends(get_get_dish_handler),
) -> DishResponse:
    result = handler.handle(GetDishQuery(dish_id=dish_id))
    return DishResponse(**result.__dict__)


@router.get(
    "/seller/{seller_id}",
    response_model=List[DishResponse],
    summary="List all active dishes for a seller",
)
def list_seller_dishes(
    seller_id: str,
    handler: ListSellerDishesHandler = Depends(get_list_seller_dishes_handler),
) -> List[DishResponse]:
    results = handler.handle(ListSellerDishesQuery(seller_id=seller_id))
    return [DishResponse(**r.__dict__) for r in results]
