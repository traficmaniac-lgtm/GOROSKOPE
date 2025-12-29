"""OpenAI client wrapper for horoscope generation."""
from __future__ import annotations

from typing import Optional

from openai import OpenAI

from app.horoscope import build_prompt


class HoroscopeClient:
    """Wrapper around OpenAI Responses API."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, sign: str, period_key: str, system_prompt: str) -> str:
        prompt = build_prompt(sign, period_key)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: object) -> str:
        # The Responses API provides an output_text helper when available.
        text: Optional[str] = getattr(response, "output_text", None)
        if text:
            return text
        # Fallback for nested content
        output = getattr(response, "output", []) or []
        if output:
            content = output[0].get("content", [])
            if content:
                part = content[0]
                if isinstance(part, dict) and "text" in part:
                    return str(part["text"])
        raise RuntimeError("Не удалось получить текст ответа от модели")

