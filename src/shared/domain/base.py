"""
Shared building blocks for all Domain layers across every module.

- Entity: Base class providing identity-based equality.
- AggregateRoot: Entity that can record and release Domain Events.
- DomainEvent: Marker base class for all domain events.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


# ---------------------------------------------------------------------------
# Domain Event base
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DomainEvent:
    """Immutable base class for every domain event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)
    occurred_on: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), kw_only=True
    )


# ---------------------------------------------------------------------------
# Entity base
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    """
    Provides identity-based equality so that two entities with the same *id*
    are considered equal regardless of their other attributes.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ---------------------------------------------------------------------------
# Aggregate Root base
# ---------------------------------------------------------------------------
@dataclass
class AggregateRoot(Entity):
    """
    An Entity that also acts as a consistency / transactional boundary.
    It can *record* domain events which the Application layer will
    *collect* after persisting the aggregate.
    """

    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def collect_events(self) -> List[DomainEvent]:
        """Return and clear all pending events."""
        events = list(self._events)
        self._events.clear()
        return events
