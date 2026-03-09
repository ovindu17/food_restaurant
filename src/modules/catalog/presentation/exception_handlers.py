"""
Maps domain exceptions to appropriate HTTP responses.

Keeps the router clean — no try/except blocks in endpoint functions.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from src.modules.catalog.domain.exceptions import (
    CatalogDomainError,
    DishAlreadyDeactivatedError,
    DishNotFoundError,
    InsufficientPortionsError,
    InvalidPriceError,
    SellerDishLimitExceededError,
)

_STATUS_MAP: dict[type[CatalogDomainError], int] = {
    DishNotFoundError: 404,
    InvalidPriceError: 400,
    InsufficientPortionsError: 409,
    DishAlreadyDeactivatedError: 409,
    SellerDishLimitExceededError: 422,
}


async def catalog_exception_handler(
    _request: Request,
    exc: CatalogDomainError,
) -> JSONResponse:
    status = _STATUS_MAP.get(type(exc), 400)
    return JSONResponse(
        status_code=status,
        content={"detail": str(exc)},
    )
