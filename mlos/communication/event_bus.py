"""
GlobalEventBus module for ML-OS.

Author: Antigravity
License: MIT
"""

import threading
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Callable, Dict, List
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionEvent:
    """Standard execution lifecycle event DTO."""

    event_id: UUID
    event_type: str
    timestamp: datetime
    source: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionEvent":
        return cls(
            event_id=UUID(data["event_id"]),
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            payload=data.get("payload", {}),
        )


class GlobalEventBus:
    """
    Decoupled thread-safe event-driven communications hub (Singleton).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(GlobalEventBus, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_subscribers"):
            self._subscribers: Dict[str, List[Callable[[ExecutionEvent], None]]] = {}
            self._lock = threading.Lock()

    def subscribe(
        self, event_type: str, callback: Callable[[ExecutionEvent], None]
    ) -> None:
        """Subscribe a callback to a specific event type (or '*' for wildcard matching)."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def unsubscribe(
        self, event_type: str, callback: Callable[[ExecutionEvent], None]
    ) -> None:
        """Unsubscribe a callback from an event type."""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass

    def publish(
        self, event_type: str, source: str, payload: Dict[str, Any]
    ) -> ExecutionEvent:
        """Publish a new event to all matching subscribers."""
        event = ExecutionEvent(
            event_id=uuid4(),
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            payload=payload,
        )

        # Collect subscribers under a lock, then call them outside of the lock
        # to avoid deadlocks.
        subscribers_to_call = []
        with self._lock:
            subscribers_to_call.extend(self._subscribers.get(event_type, []))
            subscribers_to_call.extend(self._subscribers.get("*", []))

        for cb in subscribers_to_call:
            try:
                cb(event)
            except Exception:
                # Observers must not interrupt core process execution flow
                pass

        return event

    def clear(self) -> None:
        """Clear all subscribers."""
        with self._lock:
            self._subscribers.clear()
