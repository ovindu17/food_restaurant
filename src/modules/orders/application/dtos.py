"""
Response DTOs returned by the Application layer.

These are plain data containers that decouple the domain model from
whatever the caller (HTTP controller, CLI, test) needs to see.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List


@dataclass(frozen=True)
class OrderItemDTO:
    id: str
    dish_id: str
    dish_name: str
    quantity: int
    unit_price: Decimal
    currency: str
    line_total: Decimal


@dataclass(frozen=True)
class OrderResponseDTO:
    id: str
    customer_id: str
    items: List[OrderItemDTO]
    status: str
    total_amount: Decimal
    currency: str
    notes: str
    created_at: datetime
    updated_at: datetime
