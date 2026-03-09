"""
Unit of Work pattern.

Coordinates committing the database transaction and publishing domain
events atomically (from the application's perspective).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.shared.domain.base import AggregateRoot
from src.shared.domain.event_bus import EventBus


class UnitOfWork(ABC):
    """Abstract unit of work — each module extends this to expose its repos."""

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    Base SQLAlchemy implementation.

    After a successful commit it collects and publishes domain events
    from every aggregate that was passed through ``register_aggregate``.
    """

    def __init__(self, session: Session, event_bus: EventBus) -> None:
        self._session = session
        self._event_bus = event_bus
        self._aggregates: list[AggregateRoot] = []

    @property
    def session(self) -> Session:
        return self._session

    def register_aggregate(self, aggregate: AggregateRoot) -> None:
        """Track an aggregate so its events get published after commit."""
        if aggregate not in self._aggregates:
            self._aggregates.append(aggregate)

    def commit(self) -> None:
        self._session.commit()
        self._publish_events()

    def rollback(self) -> None:
        self._session.rollback()

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()

    # ------------------------------------------------------------------
    def _publish_events(self) -> None:
        for aggregate in self._aggregates:
            events = aggregate.collect_events()
            if events:
                self._event_bus.publish(events)
        self._aggregates.clear()
