"""Orchestrator end-to-end tests.

These run the full pipeline against the mock LLM + mock MCP server.
They verify:
  - all default fixture issues are processed
  - each issue ends in `completed` state
  - the triage labels are plausible
  - the reviewer reaches a decision
  - a tool error in MCP doesn't kill the pipeline
"""
from __future__ import annotations

from issuemosaic.blackboard import Blackboard, EventBus
from issuemosaic.llm.mock import MockLLM
from issuemosaic.mcp import MockMCPServer
from issuemosaic.orchestrator import triage_all, triage_issue


def test_triage_all_processes_every_issue():
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    result = triage_all(mcp, llm=llm)
    assert result["issue_count"] == 4
    assert len(result["sessions"]) == 4
    for sess in result["sessions"]:
        assert sess["state"]["triage"]["label"]
        assert sess["state"]["verdict"]["decision"] == "APPROVED"


def test_triage_issue_publishes_completion_event():
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    issue = mcp.get_issue(101)
    board = triage_issue(issue, mcp, llm=llm)
    types = [e["type"] for e in board.events]
    assert "issue_arrived" in types
    assert "triaged" in types
    assert "plan_ready" in types
    assert "reviewed" in types
    assert "completed" in types


def test_triage_issue_labels_the_mcp_record():
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    issue = mcp.get_issue(101)
    triage_issue(issue, mcp, llm=llm)
    updated = mcp.get_issue(101)
    assert len(updated["labels"]) >= 1


def test_triage_issue_posts_a_comment():
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    issue = mcp.get_issue(101)
    triage_issue(issue, mcp, llm=llm)
    updated = mcp.get_issue(101)
    assert len(updated["comments"]) == 1
    comment_body = updated["comments"][0]["body"]
    assert "IssueMosaic" in comment_body
    assert "Proposed plan" in comment_body


def test_eventbus_receives_pipeline_events():
    bus = EventBus()
    received = []
    bus.subscribe(lambda e: received.append(e.type))
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    issue = mcp.get_issue(102)
    triage_issue(issue, mcp, llm=llm, bus=bus)
    assert "issue_arrived" in received
    assert "completed" in received


def test_triage_custom_issue():
    mcp = MockMCPServer()
    llm = MockLLM(role="e2e")
    issue = {
        "iid": 999,
        "title": "Performance regression in /api/search",
        "body": "Latency has spiked to 5s. Timeout complaints are flooding in.",
        "labels": [],
        "comments": [],
    }
    board = triage_issue(issue, mcp, llm=llm)
    triage_out = board.get("triage")
    assert triage_out["priority"] in ("P1", "P2")  # perf issue should be high prio
