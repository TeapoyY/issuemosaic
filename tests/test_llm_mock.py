"""Mock LLM tests — verify each agent role's canned response is parseable."""
from __future__ import annotations

import json

from issuemosaic.llm.mock import MockLLM


def test_mock_triage_extracts_critical_bug():
    llm = MockLLM(role="triage")
    sys = "You are the Triage agent. Categorise issues."
    out = llm.complete(sys, [{"role": "user", "content": "App crashed with traceback and panic"}])
    assert "bug::critical" in out
    assert "P1" in out


def test_mock_triage_classifies_feature_request():
    llm = MockLLM(role="triage")
    sys = "You are the Triage agent. Categorise issues."
    out = llm.complete(sys, [{"role": "user", "content": "Could you add support for XLSX?"}])
    assert "feature-request" in out
    assert "P3" in out


def test_mock_resolution_returns_json_with_steps_and_effort():
    llm = MockLLM(role="resolution")
    sys = "You are the Resolution agent. Draft a plan."
    out = llm.complete(sys, [{"role": "user", "content": "Fix the bug"}])
    # The canned response is JSON in a code fence
    assert '"steps"' in out
    assert '"effort"' in out
    assert '"S"' in out


def test_mock_reviewer_approves_when_plan_has_steps_and_test():
    llm = MockLLM(role="reviewer")
    sys = "You are the Reviewer agent. Validate the plan."
    user_msg = "Plan: {'steps': ['1. add test', '2. fix'], 'effort': 'S'}"
    out = llm.complete(sys, [{"role": "user", "content": user_msg}])
    assert '"decision": "APPROVED"' in out


def test_mock_reviewer_revises_when_no_effort():
    llm = MockLLM(role="reviewer")
    sys = "You are the Reviewer agent. Validate the plan."
    out = llm.complete(sys, [{"role": "user", "content": "Plan: do the thing"}])
    assert '"decision": "REVISE"' in out


def test_mock_reviewer_approves_when_plan_has_steps_and_test():
    llm = MockLLM(role="reviewer")
    sys = "You are the Reviewer agent. Validate the plan."
    user_msg = "Plan: {'steps': ['1. add test', '2. fix'], 'effort': 'S'}"
    out = llm.complete(sys, [{"role": "user", "content": user_msg}])
    assert "APPROVED" in out


def test_mock_records_calls_for_observability():
    llm = MockLLM(role="triage")
    llm.complete("sys", [{"role": "user", "content": "hello"}])
    llm.complete("sys", [{"role": "user", "content": "world"}])
    assert len(llm.calls) == 2
    assert llm.calls[0]["user_first_120"] == "hello"
