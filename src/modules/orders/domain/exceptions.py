"""
Domain-specific exceptions for the Orders bounded context.

These exceptions carry semantic meaning and are mapped to appropriate
HTTP status codes in the Presentation layer.
"""

from __future__ import annotations


class OrderDomainError(Exception):
    """Base for all Orders domain errors."""


class OrderNotFoundError(OrderDomainError):
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Order with ID '{order_id}' was not found.")


class EmptyOrderError(OrderDomainError):
    def __init__(self) -> None:
        super().__init__("An order must have at least one item.")


class InvalidOrderTransitionError(OrderDomainError):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from '{current}' to '{target}'."
        )


class OrderAlreadyCancelledError(OrderDomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order '{order_id}' is already cancelled.")


class TooManyActiveOrdersError(OrderDomainError):
    """Raised when a customer exceeds the maximum number of active orders."""

    def __init__(self, customer_id: str, limit: int) -> None:
        super().__init__(
            f"Customer '{customer_id}' has reached the maximum of {limit} active orders."
        )


class DishUnavailableError(OrderDomainError):
    """Raised when a dish referenced in the order is not available."""

    def __init__(self, dish_id: str, reason: str = "") -> None:
        self.dish_id = dish_id
        detail = f"Dish '{dish_id}' is unavailable"
        if reason:
            detail += f": {reason}"
        super().__init__(detail)
