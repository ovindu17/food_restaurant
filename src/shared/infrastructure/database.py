"""
Central database configuration shared by every module in the monolith.

In production the connection string is loaded from environment variables
via pydantic-settings.  The ``get_db`` generator is used as a FastAPI
dependency to supply a scoped SQLAlchemy session per request.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# ---------------------------------------------------------------------------
# Settings (loaded from environment / .env file)
# ---------------------------------------------------------------------------
class DatabaseSettings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost/homemade_food_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    model_config = {"env_prefix": "APP_"}


@lru_cache
def get_settings() -> DatabaseSettings:
    return DatabaseSettings()


# ---------------------------------------------------------------------------
# SQLAlchemy engine & session factory
# ---------------------------------------------------------------------------
_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    pool_size=_settings.db_pool_size,
    max_overflow=_settings.db_max_overflow,
    echo=_settings.db_echo,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Session:  # type: ignore[misc]
    """Yield a database session scoped to a single request."""
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
