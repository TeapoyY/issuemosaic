"""Tool registry — the curated set of MCP-backed tools the agents use.

Each tool has a name, a description (advertised to the LLM), a
JSON-schema-ish arg spec, and a callable that takes a dict of args and
returns a result. The default registry wraps the four high-level
operations the orchestrator needs from the GitLab MCP server.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ..mcp import MCPClient, MockMCPServer


@dataclass
class Tool:
    name: str
    description: str
    args: Dict[str, str]  # arg name -> short type description
    run: Callable[[Dict[str, Any]], Any]

    def spec(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": [{"name": k, "type": v} for k, v in self.args.items()],
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"tool {name!r} not registered")
        return self._tools[name]

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def specs(self) -> List[Dict[str, Any]]:
        return [t.spec() for t in self._tools.values()]


def build_default_registry(mcp: MCPClient) -> ToolRegistry:
    """Register the four GitLab MCP-backed tools the agents use."""
    reg = ToolRegistry()

    reg.register(Tool(
        name="list_issues",
        description="List open issues from the GitLab project.",
        args={"state": "string: 'opened' | 'closed' | 'all' (default 'opened')"},
        run=lambda a: mcp.list_issues(state=a.get("state", "opened")),
    ))
    reg.register(Tool(
        name="get_issue",
        description="Fetch a single issue by IID.",
        args={"iid": "int: issue IID"},
        run=lambda a: mcp.get_issue(int(a["iid"])),
    ))
    reg.register(Tool(
        name="post_comment",
        description="Post a comment on an issue (used to publish the resolution plan).",
        args={"iid": "int: issue IID", "body": "string: comment markdown"},
        run=lambda a: mcp.post_comment(int(a["iid"]), a["body"]),
    ))
    reg.register(Tool(
        name="add_label",
        description="Add a label to an issue (used to publish the triage verdict).",
        args={"iid": "int: issue IID", "label": "string: label name"},
        run=lambda a: mcp.add_label(int(a["iid"]), a["label"]),
    ))

    return reg
