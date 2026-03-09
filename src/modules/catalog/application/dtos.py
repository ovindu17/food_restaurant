"""
Response DTOs returned by the Application layer.

These are plain data containers that decouple the domain model from
whatever the caller (HTTP controller, CLI, test) needs to see.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class DishResponseDTO:
    id: str
    seller_id: str
    name: str
    description: str
    price: Decimal
    currency: str
    available_portions: int
    is_active: bool
    created_at: datetime
