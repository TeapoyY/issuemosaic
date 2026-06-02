"""Triage agent — categorises an incoming GitLab issue.

Given an issue title + body, returns a structured JSON object with:
  - label: short kebab-case label (e.g. "bug::critical", "feature-request")
  - priority: P1 (critical) … P4 (low)
  - category: engineering | docs | product | question
  - confidence: 0..1

The agent uses a small system prompt that any LLM (Gemini or mock) can
parse. The mock backend pattern-matches against keyword lists; the real
Gemini backend uses its own judgement.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from ..llm.base import LLM


SYSTEM_PROMPT = """\
You are the Triage agent in the IssueMosaic multi-agent system.

Your job: given a GitLab issue title and body, categorise it and return
strict JSON with the following keys:
  - label: short kebab-case label (e.g. "bug::critical", "feature-request",
    "docs", "perf", "needs-triage").
  - priority: one of "P1" (critical), "P2" (high), "P3" (medium), "P4" (low).
  - category: one of "engineering", "docs", "product", "question".
  - confidence: float 0.0 - 1.0 reflecting how certain you are.

Output ONLY the JSON object, wrapped in a ```json ... ``` fence.
"""


def _extract_json(text: str) -> Dict[str, Any]:
    """Pull the first JSON object out of an LLM response (handles fences)."""
    # Try fence first
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        candidate = m.group(1)
    else:
        # Fallback: any {...} block
        m = re.search(r"(\{.*\})", text, re.DOTALL)
        if not m:
            return {
                "label": "needs-triage",
                "priority": "P3",
                "category": "question",
                "confidence": 0.1,
                "_raw": text,
            }
        candidate = m.group(1)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {
            "label": "needs-triage",
            "priority": "P3",
            "category": "question",
            "confidence": 0.2,
            "_raw": text,
        }


class TriageAgent:
    """Categorises incoming issues."""

    def __init__(self, llm: LLM) -> None:
        self._llm = llm
        self.name = "triage"

    def run(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        user_msg = (
            f"Title: {issue.get('title', '')}\n\n"
            f"Body:\n{issue.get('body', '')}\n"
        )
        raw = self._llm.complete(SYSTEM_PROMPT, [{"role": "user", "content": user_msg}])
        parsed = _extract_json(raw)
        # Sanity defaults
        parsed.setdefault("label", "needs-triage")
        parsed.setdefault("priority", "P3")
        parsed.setdefault("category", "question")
        parsed.setdefault("confidence", 0.5)
        parsed["agent"] = self.name
        parsed["_raw"] = raw
        return parsed
