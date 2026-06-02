"""Tool registry tests."""
from __future__ import annotations

from issuemosaic.mcp import MockMCPServer
from issuemosaic.tools import build_default_registry


def test_registry_has_four_gitlab_tools():
    mcp = MockMCPServer()
    reg = build_default_registry(mcp)
    names = {t.name for t in reg.all()}
    assert names == {"list_issues", "get_issue", "post_comment", "add_label"}


def test_registry_specs_are_well_formed():
    mcp = MockMCPServer()
    reg = build_default_registry(mcp)
    for spec in reg.specs():
        assert "name" in spec
        assert "description" in spec
        assert "arguments" in spec
        assert isinstance(spec["arguments"], list)


def test_get_issue_tool_runs():
    mcp = MockMCPServer()
    reg = build_default_registry(mcp)
    out = reg.get("get_issue").run({"iid": 101})
    assert out["iid"] == 101


def test_add_label_tool_runs():
    mcp = MockMCPServer()
    reg = build_default_registry(mcp)
    reg.get("add_label").run({"iid": 101, "label": "bug::critical"})
    issue = mcp.get_issue(101)
    assert "bug::critical" in issue["labels"]


def test_unknown_tool_raises():
    mcp = MockMCPServer()
    reg = build_default_registry(mcp)
    import pytest
    with pytest.raises(KeyError):
        reg.get("nonexistent")
