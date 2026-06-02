"""LLM Protocol — the interface every LLM backend implements.

A minimal, no-frills protocol. The orchestrator and agents depend only on
this — they don't know whether they're talking to Gemini, Claude, or the
offline mock.
"""
from __future__ import annotations

from typing import List, Protocol


class LLM(Protocol):
    """A minimal protocol for LLM backends.

    Methods take a system prompt and a list of user/assistant messages,
    returning a single assistant text response. The orchestrator doesn't
    care which backend is plugged in.
    """

    def complete(
        self,
        system: str,
        messages: List[dict],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str: ...

    @property
    def name(self) -> str: ...


def make_default_llm(role: str = "generic") -> LLM:
    """Factory: prefer Gemini if GOOGLE_API_KEY is set, else MockLLM.

    Mirrors the convention used in the AgentMesh sister project so the
    CLI/UX is familiar to anyone who's used it before.
    """
    import os
    if os.environ.get("GOOGLE_API_KEY"):
        from issuemosaic.llm.gemini import GeminiLLM
        return GeminiLLM()
    from issuemosaic.llm.mock import MockLLM
    return MockLLM(role=role)
