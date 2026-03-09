"""
Commands and Queries — the inputs to the Application layer.

Commands represent *intentions to change state*.
Queries represent *read requests*.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CreateDishCommand:
    seller_id: str
    name: str
    description: str
    price: float
    currency: str
    initial_portions: int


@dataclass(frozen=True)
class DeactivateDishCommand:
    dish_id: str


@dataclass(frozen=True)
class ChangeDishPriceCommand:
    dish_id: str
    new_price: float
    currency: str


@dataclass(frozen=True)
class DeductPortionsCommand:
    dish_id: str
    amount: int


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GetDishQuery:
    dish_id: str


@dataclass(frozen=True)
class ListSellerDishesQuery:
    seller_id: str
