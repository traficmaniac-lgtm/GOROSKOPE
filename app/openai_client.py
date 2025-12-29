"""Simple OpenAI client for minimal chatbot flows."""
from __future__ import annotations

from openai import OpenAI


class OpenAIClient:
    """Wrapper around the OpenAI Responses API."""

    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def ask(self, prompt: str, max_output_tokens: int = 150) -> str:
        response = self.client.responses.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_output_tokens=max_output_tokens,
        )
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: object) -> str:
        try:
            message = response.output[0]
            if hasattr(message, "content") and message.content:
                text_block = message.content[0]
                if hasattr(text_block, "text") and text_block.text:
                    return text_block.text
        except Exception:  # noqa: BLE001
            pass
        return "Не удалось разобрать ответ от OpenAI."

    def test_greeting(self) -> str:
        return self.ask("Скажи одно короткое приветствие одним предложением.", max_output_tokens=60)
