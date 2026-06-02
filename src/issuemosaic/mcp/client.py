"""MCP client — talks to a GitLab MCP server.

When a real GitLab MCP server is available (over HTTP), `GitLabMCPClient`
uses httpx to invoke its RPC methods. Otherwise the orchestrator can
inject a `MockMCPServer` directly via the local-client path.
"""
from __future__ import annotations

from typing import Any, Dict, List, Protocol

from .server import MockMCPServer


class MCPClient(Protocol):
    """The minimum the orchestrator needs from an MCP client."""

    def list_issues(self) -> List[Dict[str, Any]]: ...
    def get_issue(self, iid: int) -> Dict[str, Any]: ...
    def post_comment(self, iid: int, body: str) -> Dict[str, Any]: ...
    def add_label(self, iid: int, label: str) -> Dict[str, Any]: ...


class GitLabMCPClient:
    """HTTP MCP client for a real GitLab MCP server.

    The server is expected to expose MCP-style JSON RPC at `endpoint`,
    e.g. https://mcp.example.com/mcp. The constructor takes the endpoint
    and a bearer token; methods translate the four high-level operations
    into `tools/call` requests.

    For the demo + tests, prefer the local `MockMCPServer` (no network).
    """

    def __init__(self, endpoint: str, token: str, timeout: float = 10.0) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._token = token
        self._timeout = timeout

    def _call(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        import httpx  # local import to keep the dependency optional

        url = f"{self._endpoint}/tools/call"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        body = {"name": tool, "arguments": arguments}
        with httpx.Client(timeout=self._timeout) as cli:
            r = cli.post(url, json=body, headers=headers)
            r.raise_for_status()
            return r.json()

    def list_issues(self) -> List[Dict[str, Any]]:
        result = self._call("list_issues", {"state": "opened"})
        return result.get("data", [])

    def get_issue(self, iid: int) -> Dict[str, Any]:
        result = self._call("get_issue", {"iid": iid})
        return result.get("data", {})

    def post_comment(self, iid: int, body: str) -> Dict[str, Any]:
        return self._call("post_comment", {"iid": iid, "body": body})

    def add_label(self, iid: int, label: str) -> Dict[str, Any]:
        return self._call("add_label", {"iid": iid, "label": label})


def make_mcp_client(
    endpoint: str = "",
    token: str = "",
    mock: MockMCPServer = None,
) -> MCPClient:
    """Factory: use the mock if no endpoint is configured, else HTTP."""
    if endpoint:
        return GitLabMCPClient(endpoint, token)
    if mock is not None:
        return mock
    return MockMCPServer()
