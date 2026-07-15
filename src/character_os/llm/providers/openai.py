"""OpenAI provider. Import openai only here — never from brain modules."""

from __future__ import annotations

import os
from typing import Any

from character_os.llm.provider import LLMMessage, LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the OpenAI provider. "
                "Copy .env.example to .env and set OPENAI_API_KEY, "
                "or use CHARACTER_OS_LLM_PROVIDER=stub."
            )
        self._client: Any = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ImportError(
                    "openai package not installed. "
                    "Install with: pip install 'character-os[openai]'"
                ) from exc
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.7) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        content = response.choices[0].message.content
        return (content or "").strip()
