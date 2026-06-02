"""Back-compat module: re-exports from the blackboard package."""
from .blackboard import Blackboard, EventBus, Event

__all__ = ["Blackboard", "EventBus", "Event"]
