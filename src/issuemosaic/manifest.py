"""Agent Builder manifest builder.

Gemini Agent Builder (and Google Cloud's Vertex AI Agent Engine) accept
a JSON manifest describing each agent: its system prompt, the tools it
exposes, and the model it should run on. This module assembles the
manifest from the live LLM + tool registry.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from .llm.base import LLM
from .mcp import MockMCPServer
from .mcp.client import make_mcp_client
from .tools import build_default_registry


def build_manifest(llm: LLM, mcp=None) -> Dict[str, Any]:
    """Return a manifest dict the Agent Builder UI can ingest."""
    if mcp is None:
        mcp = MockMCPServer()
    registry = build_default_registry(mcp)

    agents: List[Dict[str, Any]] = [
        {
            "name": "triage",
            "description": "Categorises incoming GitLab issues (label, priority, category, confidence).",
            "model": llm.name,
            "system_prompt": (
                "You are the Triage agent in the IssueMosaic multi-agent system. "
                "Given a GitLab issue title and body, categorise it and return strict JSON with "
                "label, priority, category, confidence."
            ),
            "tools": ["list_issues", "get_issue", "add_label"],
        },
        {
            "name": "resolution",
            "description": "Drafts a 5-step fix plan for a triaged issue.",
            "model": llm.name,
            "system_prompt": (
                "You are the Resolution agent. Given a triaged issue, draft a concrete resolution "
                "plan as strict JSON: steps, effort (S/M/L), risks, estimated_hours."
            ),
            "tools": ["get_issue", "post_comment"],
        },
        {
            "name": "reviewer",
            "description": "Validates a proposed resolution plan (APPROVE / REVISE).",
            "model": llm.name,
            "system_prompt": (
                "You are the Reviewer agent. Validate a proposed resolution plan and return "
                "strict JSON: decision (APPROVED/REVISE), feedback, concerns."
            ),
            "tools": ["get_issue", "post_comment"],
        },
    ]
    return {
        "schema_version": "1.0",
        "display_name": "IssueMosaic",
        "description": "Reactive multi-agent GitLab issue triage. Powered by Gemini + GitLab MCP.",
        "agents": agents,
        "tools": registry.specs(),
    }
