import queue
import json
from typing import Generator
from mlos.communication.event_bus import GlobalEventBus, ExecutionEvent

class EventStreamService:
    @staticmethod
    def subscribe(run_id: str) -> Generator[str, None, None]:
        """
        Subscribe to the GlobalEventBus wildcard and stream events filtered by run_id in SSE format.
        """
        q = queue.Queue(maxsize=100)
        bus = GlobalEventBus()

        def listener(event: ExecutionEvent) -> None:
            if event.run_id == run_id:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    pass

        # Subscribe listener to all events
        bus.subscribe("*", listener)

        try:
            while True:
                try:
                    event = q.get(timeout=1.0)
                    data = {
                        "run_id": event.run_id,
                        "event_type": event.event_type,
                        "stage": event.stage,
                        "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp),
                        "payload": event.payload
                    }
                    
                    yield f"event: {event.event_type}\ndata: {json.dumps(data)}\n\n"
                    
                    if event.event_type in ["ExecutionCompleted", "ExecutionFailed"]:
                        break
                except queue.Empty:
                    # Send standard SSE heartbeat to check client connection
                    yield ": heartbeat\n\n"
        finally:
            # Guarantee unsubscribe cleanup on connection drops
            bus.unsubscribe("*", listener)
