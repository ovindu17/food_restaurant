"""
Simple synchronous in-process event bus.

For a production system you could swap this for an async implementation
backed by RabbitMQ, Kafka, or a transactional outbox pattern — without
touching the domain or application layers.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Dict, List, Type

from src.shared.domain.base import DomainEvent
from src.shared.domain.event_bus import EventBus

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Dispatches domain events to registered handlers in the same process."""

    def __init__(self) -> None:
        self._handlers: Dict[
            Type[DomainEvent], List[Callable[[DomainEvent], None]]
        ] = defaultdict(list)

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None],
    ) -> None:
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed %s to %s", handler.__name__, event_type.__name__)

    def publish(self, events: List[DomainEvent]) -> None:
        for event in events:
            handlers = self._handlers.get(type(event), [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception:
                    logger.exception(
                        "Handler %s failed for event %s",
                        handler.__name__,
                        type(event).__name__,
                    )
