"""
Domain-specific exceptions for the Catalog bounded context.

These exceptions carry semantic meaning and are mapped to appropriate
HTTP status codes in the Presentation layer.
"""

from __future__ import annotations


class CatalogDomainError(Exception):
    """Base for all Catalog domain errors."""


class InvalidPriceError(CatalogDomainError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Invalid price: {detail}")


class InsufficientPortionsError(CatalogDomainError):
    def __init__(self, requested: int, available: int) -> None:
        self.requested = requested
        self.available = available
        super().__init__(
            f"Cannot deduct {requested} portions. Only {available} available."
        )


class DishNotFoundError(CatalogDomainError):
    def __init__(self, dish_id: str) -> None:
        self.dish_id = dish_id
        super().__init__(f"Dish with ID '{dish_id}' was not found.")


class DishAlreadyDeactivatedError(CatalogDomainError):
    def __init__(self, dish_id: str) -> None:
        super().__init__(f"Dish '{dish_id}' is already deactivated.")


class SellerDishLimitExceededError(CatalogDomainError):
    """Raised when a seller tries to exceed the maximum number of active dishes."""

    def __init__(self, seller_id: str, limit: int) -> None:
        super().__init__(
            f"Seller '{seller_id}' has reached the maximum of {limit} active dishes."
        )
