"""Gemini LLM backend.

Used when GOOGLE_API_KEY is set. Falls back to MockLLM at the
make_default_llm() level if the import fails or the key is missing.

The google-generativeai SDK is an optional dependency — installed via
`pip install issuemosaic[gemini]`. The mock backend is the default
so the demo + tests run without it.
"""
from __future__ import annotations

import os
from typing import List


class GeminiLLM:
    """Google Gemini via the google-generativeai SDK.

    Default model: gemini-1.5-flash (cheap, fast, good enough for
    structured JSON output. The hackathon partners hint that Gemini 3
    is preferred for Agent Builder, but flash is what we can ship
    without a GCP project.
    """

    def __init__(self, model: str = "gemini-1.5-flash") -> None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai not installed; run "
                "`pip install issuemosaic[gemini]`"
            ) from exc
        genai.configure(api_key=api_key)
        self._model_name = model
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        return f"gemini:{self._model_name}"

    def complete(
        self,
        system: str,
        messages: List[dict],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        # Flatten the messages into a single prompt — Gemini's SDK accepts
        # a single `contents` string in the simple form.
        parts: List[str] = [f"[SYSTEM]\n{system}"]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"[{role.upper()}]\n{content}")
        prompt = "\n\n".join(parts)

        # Newer google-generativeai uses generation_config=...
        try:
            resp = self._model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
        except TypeError:
            # Older SDK
            resp = self._model.generate_content(prompt)
        # text accessor
        return getattr(resp, "text", "") or ""
