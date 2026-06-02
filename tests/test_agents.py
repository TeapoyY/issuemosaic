"""Agent tests — verify each agent produces a valid structured response."""
from __future__ import annotations

from issuemosaic.agents.triage import TriageAgent, _extract_json
from issuemosaic.agents.resolution import ResolutionAgent
from issuemosaic.agents.reviewer import ReviewerAgent
from issuemosaic.llm.mock import MockLLM


def test_extract_json_handles_fenced():
    text = 'Here you go:\n```json\n{"a": 1, "b": 2}\n```\nEnjoy!'
    out = _extract_json(text)
    assert out == {"a": 1, "b": 2}


def test_extract_json_handles_bare():
    text = 'Sure: {"a": 1, "b": 2}'
    out = _extract_json(text)
    assert out == {"a": 1, "b": 2}


def test_extract_json_fallback_on_garbage():
    out = _extract_json("no json here at all")
    assert out["label"] == "needs-triage"
    assert out["priority"] == "P3"


def test_triage_agent_returns_required_keys():
    llm = MockLLM(role="triage")
    agent = TriageAgent(llm)
    issue = {"iid": 1, "title": "Crash on startup", "body": "Got a traceback and exception"}
    out = agent.run(issue)
    assert "label" in out
    assert "priority" in out
    assert "category" in out
    assert "confidence" in out
    assert out["agent"] == "triage"


def test_resolution_agent_returns_plan():
    llm = MockLLM(role="resolution")
    agent = ResolutionAgent(llm)
    issue = {"iid": 1, "title": "Bug", "body": "crash"}
    triage = {"label": "bug::critical", "priority": "P1", "category": "engineering", "confidence": 0.9}
    out = agent.run(issue, triage)
    assert "steps" in out
    assert "effort" in out
    assert "estimated_hours" in out
    assert out["effort"] in ("S", "M", "L")
    assert len(out["steps"]) >= 3


def test_reviewer_agent_returns_decision():
    llm = MockLLM(role="reviewer")
    agent = ReviewerAgent(llm)
    issue = {"iid": 1, "title": "Bug", "body": "crash"}
    triage = {"label": "bug", "priority": "P1"}
    plan = {"steps": ["1. Add test", "2. Fix"], "effort": "S", "estimated_hours": 4}
    out = agent.run(issue, triage, plan)
    assert out["decision"] in ("APPROVED", "REVISE")
    assert "feedback" in out
    assert "concerns" in out
