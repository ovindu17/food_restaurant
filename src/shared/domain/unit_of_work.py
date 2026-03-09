"""
Abstract Unit of Work — a domain-level port (interface).

Application-layer handlers depend on this abstraction.  The concrete
implementation (e.g. ``SqlAlchemyUnitOfWork``) lives in the
Infrastructure layer and is injected at runtime by the Presentation
layer's dependency-injection wiring.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.shared.domain.base import AggregateRoot


class UnitOfWork(ABC):
    """Abstract unit of work — each module extends this to expose its repos."""

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def register_aggregate(self, aggregate: AggregateRoot) -> None:
        """Track an aggregate so its events get published after commit."""

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
