"""
Abstract event bus that the Application layer depends on.
The concrete implementation lives in the Infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Type

from src.shared.domain.base import DomainEvent


class EventBus(ABC):
    """Port through which the application publishes domain events."""

    @abstractmethod
    def publish(self, events: List[DomainEvent]) -> None:
        """Publish a batch of domain events to all registered handlers."""

    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """Register a handler for a specific event type."""
