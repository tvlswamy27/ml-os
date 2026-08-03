"""
EventStore module for event log sourcing and time-travel timeline replay.

Author: Antigravity
License: MIT
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from mlos.communication.event_bus import GlobalEventBus, ExecutionEvent


class EventStore:
    """
    Event-sourced log store for timeline reconstruction and auditing.
    """

    def __init__(self, project_path: str) -> None:
        self.project_path = Path(project_path)
        self.event_log_file = self.project_path / ".mlos" / "events.yaml"
        self._events: List[ExecutionEvent] = []
        self.load()
        # Subscribe to all events globally to capture them automatically
        GlobalEventBus().subscribe("*", self.append_event)

    def append_event(self, event: ExecutionEvent) -> None:
        """Append a new event and save to disk."""
        # Avoid duplicate events if the event is already captured
        if any(e.event_id == event.event_id for e in self._events):
            return

        self._events.append(event)
        self.save()

    def get_timeline(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[ExecutionEvent]:
        """Query history timeline, optionally filtering by date range."""
        timeline = list(self._events)
        if start_time:
            timeline = [e for e in timeline if e.timestamp >= start_time]
        if end_time:
            timeline = [e for e in timeline if e.timestamp <= end_time]
        return sorted(timeline, key=lambda e: e.timestamp)

    def replay(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[ExecutionEvent]:
        """Return the execution timeline for audit replay or visualization updates."""
        return self.get_timeline(start_time, end_time)

    def save(self) -> None:
        """Save captured events log to YAML."""
        self.event_log_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = [e.to_dict() for e in self._events]
        with open(self.event_log_file, "w") as f:
            yaml.safe_dump(serialized, f, sort_keys=False)

    def load(self) -> None:
        """Load persistent events log from disk."""
        if not self.event_log_file.exists():
            return
        try:
            with open(self.event_log_file, "r") as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, list):
                self._events = [ExecutionEvent.from_dict(d) for d in data]
        except Exception:
            pass

    def shutdown(self) -> None:
        """Unsubscribe from the global event bus."""
        GlobalEventBus().unsubscribe("*", self.append_event)
