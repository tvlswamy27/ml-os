"""
ExecutionEventBus event-driven communicator module.

Author: Antigravity
License: MIT
"""

from collections.abc import Callable
from datetime import datetime


class ExecutionEvent:
    """
    Standard event published during planning and execution dispatching.
    """

    def __init__(self, event_type: str, payload: dict):
        self.event_type = event_type
        self.timestamp = datetime.utcnow()
        self.payload = payload


class ExecutionEventBus:
    """
    Decoupled publish-subscribe communications hub.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[ExecutionEvent], None]]] = {}

    def subscribe(
        self, event_type: str, callback: Callable[[ExecutionEvent], None]
    ) -> None:
        """
        Register subscriber callable for a specific event type.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: ExecutionEvent) -> None:
        """
        Broadcasts event payload to all registered type subscribers.
        """
        callbacks = self._subscribers.get(event.event_type, [])
        for cb in callbacks:
            try:
                cb(event)
            except Exception:
                # Failure of observer callback should not interrupt execution loops
                pass
