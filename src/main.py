"""
Application entry point.

Registers module routers, exception handlers, and middleware.
In production, use Alembic for migrations instead of ``create_all``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.modules.catalog.domain.exceptions import CatalogDomainError
from src.modules.catalog.presentation.exception_handlers import (
    catalog_exception_handler,
)
from src.modules.catalog.presentation.router import router as catalog_router
from src.modules.orders.domain.exceptions import OrderDomainError
from src.modules.orders.presentation.exception_handlers import (
    order_exception_handler,
)
from src.modules.orders.presentation.router import router as orders_router
from src.shared.infrastructure.database import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (replace with Alembic in production)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified.")
    yield
    # Shutdown logic (if any) goes here


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Homemade Food E-Commerce API",
    description="Modular Monolith · Clean Architecture · DDD",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Register modules
# ---------------------------------------------------------------------------
# 1. Catalog
app.include_router(catalog_router, prefix="/api/v1")
app.add_exception_handler(CatalogDomainError, catalog_exception_handler)  # type: ignore[arg-type]

# 2. Orders
app.include_router(orders_router, prefix="/api/v1")
app.add_exception_handler(OrderDomainError, order_exception_handler)  # type: ignore[arg-type]

# 3. Future modules (Users, Notifications) go here …


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Infrastructure"])
def health_check():
    return {"status": "healthy"}
