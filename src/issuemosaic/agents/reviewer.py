"""Reviewer agent — validates a resolution plan.

Reads the resolution plan and the original triage verdict and either
APPROVES the plan or sends it back for revision. Output is structured:
  - decision: "APPROVED" | "REVISE"
  - feedback: short text explanation
  - concerns: list of strings (empty when approved)
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from ..llm.base import LLM


SYSTEM_PROMPT = """\
You are the Reviewer agent in the IssueMosaic multi-agent system.

Validate the proposed resolution plan. Return strict JSON:
  - decision: "APPROVED" or "REVISE".
  - feedback: short explanation.
  - concerns: list of strings (empty when approved).

A good plan has: a reproduce step, a regression-test step, a clear fix,
verification (tests / CI), and an effort estimate.

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
        "decision": "REVISE",
        "feedback": "LLM did not return valid JSON — please regenerate.",
        "concerns": ["Invalid plan output"],
        "_raw": text,
    }


class ReviewerAgent:
    """Validates a resolution plan."""

    def __init__(self, llm: LLM) -> None:
        self._llm = llm
        self.name = "reviewer"

    def run(
        self,
        issue: Dict[str, Any],
        triage: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_msg = (
            f"Issue title: {issue.get('title', '')}\n"
            f"Triage verdict: {triage}\n"
            f"Proposed plan: {plan}\n"
        )
        raw = self._llm.complete(SYSTEM_PROMPT, [{"role": "user", "content": user_msg}])
        verdict = _extract_json(raw)
        verdict.setdefault("decision", "REVISE")
        verdict.setdefault("feedback", "")
        verdict.setdefault("concerns", [])
        verdict["agent"] = self.name
        verdict["_raw"] = raw
        return verdict
