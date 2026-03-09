"""
Pydantic schemas for HTTP request validation and response serialization.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------
class CreateDishRequest(BaseModel):
    seller_id: str = Field(..., min_length=1, examples=["seller-001"])
    name: str = Field(..., min_length=2, max_length=100, examples=["Lasagna"])
    description: str = Field(default="", max_length=500)
    price: float = Field(..., gt=0, examples=[12.99])
    currency: str = Field(default="USD", min_length=3, max_length=3)
    initial_portions: int = Field(..., ge=0, examples=[10])


class ChangePriceRequest(BaseModel):
    new_price: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class DeductPortionsRequest(BaseModel):
    amount: int = Field(..., gt=0)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class DishResponse(BaseModel):
    id: str
    seller_id: str
    name: str
    description: str
    price: Decimal
    currency: str
    available_portions: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
