"""MCP (Model Context Protocol) client + mock server.

The project speaks MCP to talk to GitLab. The real client uses the
official Python MCP SDK (HTTP transport). The mock server is an in-memory
fake so the demo + tests run without a GitLab instance.
"""
from .server import MockMCPServer
from .client import GitLabMCPClient, MCPClient

__all__ = ["MockMCPServer", "GitLabMCPClient", "MCPClient"]
