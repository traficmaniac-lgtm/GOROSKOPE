"""Simple OpenAI client for minimal chatbot flows."""
from __future__ import annotations

from typing import Any

from openai import OpenAI

MIN_OUTPUT_TOKENS = 128


def get_text(response: Any) -> str:
    """Extract text from OpenAI Responses API response."""
    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text)

    # Fallback: collect from output items
    try:
        parts: list[str] = []
        for item in getattr(response, "output", []) or []:
            content = getattr(item, "content", None) or []
            for block in content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(str(text))
        if parts:
            return "\n".join(parts)
    except Exception:  # noqa: BLE001
        pass

    return "Не удалось разобрать ответ от OpenAI."


class OpenAIClient:
    """Wrapper around the OpenAI Responses API."""

    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def ask(self, prompt: str, max_output_tokens: int = 256) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=max(max_output_tokens, MIN_OUTPUT_TOKENS),
        )
        return get_text(response)

    def test_greeting(self) -> str:
        return self.ask("Say OK", max_output_tokens=MIN_OUTPUT_TOKENS)
