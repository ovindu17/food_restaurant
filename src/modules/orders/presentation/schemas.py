"""
Pydantic schemas for HTTP request validation and response serialization.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------
class OrderItemRequest(BaseModel):
    dish_id: str = Field(..., min_length=1, examples=["dish-001"])
    quantity: int = Field(..., gt=0, examples=[2])


class PlaceOrderRequest(BaseModel):
    customer_id: str = Field(..., min_length=1, examples=["customer-001"])
    items: List[OrderItemRequest] = Field(..., min_length=1)
    notes: str = Field(default="", max_length=500)


class CancelOrderRequest(BaseModel):
    reason: str = Field(default="", max_length=500)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class OrderItemResponse(BaseModel):
    id: str
    dish_id: str
    dish_name: str
    quantity: int
    unit_price: Decimal
    currency: str
    line_total: Decimal


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    items: List[OrderItemResponse]
    status: str
    total_amount: Decimal
    currency: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
