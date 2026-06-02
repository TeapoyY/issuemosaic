"""Blackboard + event bus tests."""
from __future__ import annotations

from issuemosaic.blackboard import Blackboard, EventBus, Event


def test_eventbus_publishes_to_subscribers():
    bus = EventBus()
    received = []
    bus.subscribe(lambda e: received.append(e))
    bus.publish(Event(type="hello", payload={"x": 1}))
    bus.publish(Event(type="world", payload={"y": 2}))
    assert len(received) == 2
    assert received[0].type == "hello"
    assert received[1].payload == {"y": 2}


def test_eventbus_handles_subscriber_exception():
    bus = EventBus()

    def bad(_e):
        raise RuntimeError("boom")

    received = []
    bus.subscribe(bad)
    bus.subscribe(lambda e: received.append(e))
    # bad subscriber raising should not block the next one
    bus.publish(Event(type="hi", payload={}))
    assert len(received) == 1


def test_blackboard_emit_appends_event():
    bb = Blackboard()
    bb.emit("issue_arrived", {"iid": 1})
    bb.emit("triaged", {"label": "bug"})
    assert len(bb.events) == 2
    assert bb.events[0]["type"] == "issue_arrived"
    assert bb.events[1]["type"] == "triaged"


def test_blackboard_set_and_get():
    bb = Blackboard()
    bb.set("foo", "bar")
    assert bb.get("foo") == "bar"
    assert bb.get("missing", "default") == "default"


def test_blackboard_publishes_to_bus():
    bus = EventBus()
    received = []
    bus.subscribe(lambda e: received.append(e))
    bb = Blackboard(bus=bus)
    bb.emit("done", {"x": 1})
    assert len(received) == 1
    assert received[0].type == "done"


def test_blackboard_snapshot_is_independent():
    bb = Blackboard()
    bb.set("a", 1)
    snap = bb.snapshot()
    bb.set("a", 2)
    assert snap["state"]["a"] == 1
    assert bb.get("a") == 2
