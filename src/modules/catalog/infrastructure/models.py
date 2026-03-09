"""
SQLAlchemy ORM model for the ``catalog_dishes`` table.

This is a pure infrastructure concern — the domain knows nothing about it.
The table is prefixed with ``catalog_`` to make module ownership explicit
and avoid naming collisions in the shared database.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String

from src.shared.infrastructure.database import Base


class DishModel(Base):
    __tablename__ = "catalog_dishes"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True, default="")
    price_amount = Column(Numeric(10, 2), nullable=False)
    price_currency = Column(String(3), nullable=False, default="USD")
    available_portions = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
