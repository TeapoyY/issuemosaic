"""Mock MCP server tests."""
from __future__ import annotations

import pytest

from issuemosaic.mcp import MockMCPServer


def test_default_fixture_has_four_issues():
    s = MockMCPServer()
    assert len(s.list_issues()) == 4


def test_get_issue_returns_full_record():
    s = MockMCPServer()
    issue = s.get_issue(101)
    assert issue["iid"] == 101
    assert "title" in issue
    assert "body" in issue


def test_get_unknown_issue_raises():
    s = MockMCPServer()
    with pytest.raises(KeyError):
        s.get_issue(999)


def test_post_comment_appends_to_issue():
    s = MockMCPServer()
    s.post_comment(101, "Hello from test")
    issue = s.get_issue(101)
    assert len(issue["comments"]) == 1
    assert issue["comments"][0]["body"] == "Hello from test"
    assert issue["comments"][0]["author"] == "issuemosaic-bot"


def test_add_label_idempotent():
    s = MockMCPServer()
    s.add_label(101, "bug")
    s.add_label(101, "bug")  # duplicate should be no-op
    issue = s.get_issue(101)
    assert issue["labels"] == ["bug"]


def test_add_label_unknown_issue_raises():
    s = MockMCPServer()
    with pytest.raises(KeyError):
        s.add_label(999, "bug")
