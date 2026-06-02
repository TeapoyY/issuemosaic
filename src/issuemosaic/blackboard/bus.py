"""Reactive event bus + blackboard.

The blackboard is a thread-safe in-memory dict the orchestrator shares
with all agents. Subscribers register on the event bus; the orchestrator
publishes events as a triage session progresses (issue_arrived,
triaged, plan_ready, reviewed, completed, failed).
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Event:
    """An event flowing through the bus."""

    type: str
    payload: Dict[str, Any]
    ts: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "payload": self.payload, "ts": self.ts, "id": self.id}


Subscriber = Callable[[Event], None]


class EventBus:
    """Tiny pub/sub bus. Not high-throughput — for the demo dashboard."""

    def __init__(self) -> None:
        self._subs: List[Subscriber] = []
        self._lock = threading.Lock()

    def subscribe(self, fn: Subscriber) -> None:
        with self._lock:
            self._subs.append(fn)

    def unsubscribe(self, fn: Subscriber) -> None:
        with self._lock:
            if fn in self._subs:
                self._subs.remove(fn)

    def publish(self, event: Event) -> None:
        with self._lock:
            subs = list(self._subs)
        for fn in subs:
            try:
                fn(event)
            except Exception:
                # Don't let a bad subscriber kill the pipeline
                pass


class Blackboard:
    """Shared state for one triage session.

    - `state`: arbitrary dict for the current pipeline.
    - `events`: chronological log of all events.
    - `bus`: optional EventBus for live updates.
    """

    def __init__(self, session_id: Optional[str] = None, bus: Optional[EventBus] = None) -> None:
        self.session_id = session_id or str(uuid.uuid4())[:12]
        self.state: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.bus = bus
        self._lock = threading.Lock()

    def emit(self, event_type: str, payload: Dict[str, Any]) -> Event:
        event = Event(type=event_type, payload=payload)
        with self._lock:
            self.events.append(event.to_dict())
        if self.bus is not None:
            self.bus.publish(event)
        return event

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.state.get(key, default)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "state": dict(self.state),
                "events": list(self.events),
            }
