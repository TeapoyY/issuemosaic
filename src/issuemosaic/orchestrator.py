"""Orchestrator — drives the reactive triage pipeline.

Sequence:
  issue_arrived -> triage -> resolution -> reviewer -> (post_comment + add_label) -> completed

The orchestrator publishes events to the blackboard on every step. If
the reviewer rejects the plan, the orchestrator runs up to `max_revisions`
revision cycles before giving up.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .blackboard import Blackboard
from .llm.base import LLM, make_default_llm
from .mcp import MCPClient
from .tools import build_default_registry, ToolRegistry


def _format_plan_comment(issue_iid: int, triage: Dict[str, Any], plan: Dict[str, Any]) -> str:
    lines = [
        f"### IssueMosaic — auto-triaged plan for #{issue_iid}",
        "",
        f"**Triage:** `{triage.get('label', '?')}` (priority {triage.get('priority', '?')}, "
        f"confidence {triage.get('confidence', 0):.2f})",
        "",
        "**Proposed plan:**",
    ]
    for i, step in enumerate(plan.get("steps", []), 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append(
        f"_Effort: {plan.get('effort', '?')} (~{plan.get('estimated_hours', '?')} h)_"
    )
    if plan.get("risks"):
        lines.append("\n**Risks:**")
        for r in plan["risks"]:
            lines.append(f"- {r}")
    return "\n".join(lines)


def triage_issue(
    issue: Dict[str, Any],
    mcp: MCPClient,
    llm: Optional[LLM] = None,
    bus=None,
    max_revisions: int = 2,
) -> Blackboard:
    """Run a single issue through the full pipeline. Returns the blackboard."""
    # Local imports to avoid a circular dep with the agents package
    from .agents.triage import TriageAgent
    from .agents.resolution import ResolutionAgent
    from .agents.reviewer import ReviewerAgent

    if llm is None:
        llm = make_default_llm(role="orchestrator")

    board = Blackboard(bus=bus)
    board.set("issue", issue)
    board.emit("issue_arrived", {"iid": issue.get("iid")})

    triage = TriageAgent(llm)
    resolver = ResolutionAgent(llm)
    reviewer = ReviewerAgent(llm)
    registry: ToolRegistry = build_default_registry(mcp)

    # Triage
    triage_result = triage.run(issue)
    board.set("triage", triage_result)
    board.emit("triaged", {"label": triage_result.get("label"), "priority": triage_result.get("priority")})
    try:
        registry.get("add_label").run({"iid": issue["iid"], "label": triage_result.get("label", "needs-triage")})
    except Exception as exc:
        board.emit("tool_error", {"tool": "add_label", "error": str(exc)})

    # Resolution + Review (with revisions)
    plan: Dict[str, Any] = {}
    verdict: Dict[str, Any] = {}
    revisions = 0
    while True:
        plan = resolver.run(issue, triage_result)
        board.set("plan", plan)
        board.emit("plan_ready", {"steps": plan.get("steps", []), "effort": plan.get("effort")})
        verdict = reviewer.run(issue, triage_result, plan)
        board.set("verdict", verdict)
        board.emit("reviewed", {"decision": verdict.get("decision")})
        if verdict.get("decision") == "APPROVED":
            break
        revisions += 1
        if revisions > max_revisions:
            board.emit("failed", {"reason": "max_revisions exceeded", "concerns": verdict.get("concerns", [])})
            return board
        # Loop again with the same triage; the resolver will see a fresh
        # LLM call and produce a refined plan.

    # Publish
    comment = _format_plan_comment(issue["iid"], triage_result, plan)
    try:
        registry.get("post_comment").run({"iid": issue["iid"], "body": comment})
        board.emit("commented", {"iid": issue["iid"]})
    except Exception as exc:
        board.emit("tool_error", {"tool": "post_comment", "error": str(exc)})

    # Add the effort label too
    effort = plan.get("effort", "S")
    try:
        registry.get("add_label").run({"iid": issue["iid"], "label": f"effort::{effort.lower()}"})
    except Exception:
        pass

    board.emit("completed", {"iid": issue["iid"], "plan_steps": len(plan.get("steps", []))})
    return board


def triage_all(
    mcp: MCPClient,
    llm: Optional[LLM] = None,
    bus=None,
) -> Dict[str, Any]:
    """Triage every open issue in the MCP server. Returns a summary."""
    issues = mcp.list_issues()
    sessions = []
    for issue in issues:
        board = triage_issue(issue, mcp, llm=llm, bus=bus)
        sessions.append(board.snapshot())
    return {
        "issue_count": len(issues),
        "sessions": sessions,
    }
