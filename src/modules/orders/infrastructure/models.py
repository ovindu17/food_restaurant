"""
SQLAlchemy ORM models for the ``orders_*`` tables.

This is a pure infrastructure concern — the domain knows nothing about it.
Tables are prefixed with ``orders_`` to make module ownership explicit
and avoid naming collisions in the shared database.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.shared.infrastructure.database import Base


class OrderModel(Base):
    __tablename__ = "orders_orders"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), index=True, nullable=False)
    status = Column(String(20), nullable=False, default="PLACED")
    total_amount = Column(Numeric(10, 2), nullable=False)
    total_currency = Column(String(3), nullable=False, default="USD")
    notes = Column(Text, nullable=True, default="")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    items = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class OrderItemModel(Base):
    __tablename__ = "orders_order_items"

    id = Column(String(36), primary_key=True)
    order_id = Column(
        String(36),
        ForeignKey("orders_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dish_id = Column(String(36), nullable=False)
    dish_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    order = relationship("OrderModel", back_populates="items")
