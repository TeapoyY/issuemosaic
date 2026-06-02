"""Resolution agent — drafts a 5-step fix plan for a triaged issue.

Reads a triage verdict + original issue and emits a structured plan:
  - steps: ordered list of action strings
  - effort: S | M | L
  - risks: list of risk strings
  - estimated_hours: int

The mock backend returns a deterministic generic plan; Gemini can
produce context-specific steps when given the issue body.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from ..llm.base import LLM


SYSTEM_PROMPT = """\
You are the Resolution agent in the IssueMosaic multi-agent system.

Given a triaged GitLab issue (with label + priority), draft a concrete
resolution plan. Return strict JSON:
  - steps: ordered list of strings (each a single action).
  - effort: one of "S" (<= 4h), "M" (~ 1 day), "L" (> 1 day).
  - risks: list of risk strings.
  - estimated_hours: integer.

Output ONLY the JSON object, wrapped in a ```json ... ``` fence.
"""


def _extract_json(text: str) -> Dict[str, Any]:
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        candidate = m.group(1)
    else:
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if not m:
            return _fallback(text)
        candidate = m.group(1)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return _fallback(text)


def _fallback(text: str) -> Dict[str, Any]:
    return {
        "steps": [
            "Reproduce against the latest main.",
            "Add a regression test.",
            "Implement the fix.",
            "Run the full test suite.",
            "Open a merge request.",
        ],
        "effort": "S",
        "risks": ["Unknown — LLM did not return valid JSON"],
        "estimated_hours": 4,
        "_raw": text,
    }


class ResolutionAgent:
    """Drafts a fix plan for a triaged issue."""

    def __init__(self, llm: LLM) -> None:
        self._llm = llm
        self.name = "resolution"

    def run(self, issue: Dict[str, Any], triage: Dict[str, Any]) -> Dict[str, Any]:
        user_msg = (
            f"Issue title: {issue.get('title', '')}\n"
            f"Issue body:\n{issue.get('body', '')}\n\n"
            f"Triage verdict: {triage}\n"
        )
        raw = self._llm.complete(SYSTEM_PROMPT, [{"role": "user", "content": user_msg}])
        plan = _extract_json(raw)
        plan.setdefault("steps", [])
        plan.setdefault("effort", "S")
        plan.setdefault("risks", [])
        plan.setdefault("estimated_hours", 4)
        plan["agent"] = self.name
        plan["_raw"] = raw
        return plan
