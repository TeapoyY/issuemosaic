"""Agents — Triage, Resolution, Reviewer.

Each agent is a thin wrapper around an LLM backend that:
  1. Holds a `system_prompt` describing its role.
  2. Exposes a single `run(issue_payload) -> dict` method.
  3. Records every call into the blackboard for observability.

The agents never know whether they're talking to a real LLM or the
offline mock — the Protocol boundary in `llm.base` keeps them honest.
"""
from .triage import TriageAgent
from .resolution import ResolutionAgent
from .reviewer import ReviewerAgent

__all__ = ["TriageAgent", "ResolutionAgent", "ReviewerAgent"]
