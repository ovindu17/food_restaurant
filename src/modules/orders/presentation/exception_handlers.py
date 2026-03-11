"""
Maps domain exceptions to appropriate HTTP responses.

Keeps the router clean — no try/except blocks in endpoint functions.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from src.modules.orders.domain.exceptions import (
    DishUnavailableError,
    EmptyOrderError,
    InvalidOrderTransitionError,
    OrderAlreadyCancelledError,
    OrderDomainError,
    OrderNotFoundError,
    TooManyActiveOrdersError,
)

_STATUS_MAP: dict[type[OrderDomainError], int] = {
    OrderNotFoundError: 404,
    EmptyOrderError: 400,
    InvalidOrderTransitionError: 409,
    OrderAlreadyCancelledError: 409,
    TooManyActiveOrdersError: 422,
    DishUnavailableError: 404,
}


async def order_exception_handler(
    _request: Request,
    exc: OrderDomainError,
) -> JSONResponse:
    status = _STATUS_MAP.get(type(exc), 400)
    return JSONResponse(
        status_code=status,
        content={"detail": str(exc)},
    )
