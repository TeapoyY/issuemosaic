"""Mock LLM — deterministic, offline, no API key required.

Returns canned but plausible outputs based on simple pattern matching.
Used by the demo and by the test suite; the real Gemini backend is
loaded by `make_default_llm` when `GOOGLE_API_KEY` is set.
"""
from __future__ import annotations

import re
from typing import List


class MockLLM:
    """A deterministic mock LLM.

    Recognises a handful of agent-specific system prompts and returns
    pre-baked responses. The shape of the response always matches what
    the real Gemini backend would emit, so the rest of the system can't
    tell the difference.
    """

    def __init__(self, role: str = "generic") -> None:
        self._role = role
        self._calls: List[dict] = []  # for trace/observability

    @property
    def name(self) -> str:
        return f"mock:{self._role}"

    @property
    def calls(self) -> List[dict]:
        """The history of LLM calls — used by the dashboard."""
        return list(self._calls)

    def complete(
        self,
        system: str,
        messages: List[dict],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        self._calls.append(
            {
                "system_first_60": system[:60],
                "user_first_120": last_user[:120],
                "max_tokens": max_tokens,
            }
        )
        sys_low = system.lower()
        # IMPORTANT: check more-specific roles BEFORE less-specific ones,
        # since the reviewer's system prompt contains the substring
        # "resolution plan" which would otherwise match the resolver check.
        if "triage" in sys_low and "categorise" in sys_low:
            return self._mock_triage(last_user)
        if "reviewer" in sys_low and "validate" in sys_low:
            return self._mock_review(last_user)
        if "resolution" in sys_low and "plan" in sys_low:
            return self._mock_resolution(last_user)
        # Generic: echo + acknowledge
        return f"[{self._role}] ack: {last_user[:80]}"

    # ---- canned agent responses ---------------------------------------

    @staticmethod
    def _mock_triage(user_msg: str) -> str:
        # Sniff category from the issue body.
        body = user_msg.lower()
        if any(kw in body for kw in ["crash", "exception", "panic", "traceback", "fatal"]):
            label, prio = "bug::critical", "P1"
        elif any(kw in body for kw in ["feature", "would be nice", "could you add", "support for"]):
            label, prio = "feature-request", "P3"
        elif any(kw in body for kw in ["docs", "typo", "readme", "documentation"]):
            label, prio = "docs", "P4"
        elif any(kw in body for kw in ["performance", "slow", "latency", "timeout"]):
            label, prio = "perf", "P2"
        else:
            label, prio = "needs-triage", "P3"
        return (
            "```json\n"
            "{\n"
            f'  "label": "{label}",\n'
            f'  "priority": "{prio}",\n'
            '  "category": "engineering",\n'
            '  "confidence": 0.82\n'
            "}\n"
            "```"
        )

    @staticmethod
    def _mock_resolution(user_msg: str) -> str:
        return (
            "```json\n"
            "{\n"
            '  "steps": [\n'
            '    "Reproduce against the latest main.",\n'
            '    "Add a regression test capturing the failing behaviour.",\n'
            '    "Implement the fix in the smallest reasonable diff.",\n'
            '    "Verify the full test suite passes.",\n'
            '    "Open a merge request and link it in a comment."\n'
            "  ],\n"
            '  "effort": "S",\n'
            '  "risks": [],\n'
            '  "estimated_hours": 4\n'
            "}\n"
            "```"
        )

    @staticmethod
    def _mock_review(user_msg: str) -> str:
        # The user_msg is the serialised plan dict (str(dict) uses single
        # quotes). Approve if it looks well-formed: has an effort label
        # (S/M/L) and a steps array, with at least one test-related step.
        low = str(user_msg).lower()
        has_effort_label = "'s'" in low or "'m'" in low or "'l'" in low or "s/m/l" in low
        has_steps_array = "'steps'" in low or '"steps"' in low
        has_test_in_plan = "test" in low
        if has_effort_label and has_steps_array and has_test_in_plan:
            return (
                "```json\n"
                "{\n"
                '  "decision": "APPROVED",\n'
                '  "feedback": "Plan is reasonable, safe to execute.",\n'
                '  "concerns": []\n'
                "}\n"
                "```"
            )
        return (
            "```json\n"
            "{\n"
            '  "decision": "REVISE",\n'
            '  "feedback": "Please include a regression-test step and an effort estimate.",\n'
            '  "concerns": ["Missing effort label or regression test"]\n'
            "}\n"
            "```"
        )
