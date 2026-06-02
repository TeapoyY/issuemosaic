"""Tools the agents can invoke.

Tools are thin wrappers over the MCP client. Each tool is named and
schema-decorated, ready to be advertised in a Gemini Agent Builder
manifest or a LangChain tool list.
"""
from .registry import Tool, ToolRegistry, build_default_registry

__all__ = ["Tool", "ToolRegistry", "build_default_registry"]
