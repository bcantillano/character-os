"""OpenAI provider. Import openai only here — never from brain modules."""

from __future__ import annotations

import os

from character_os.llm.provider import LLMMessage, LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the OpenAI provider. "
                "Set it in .env or use CHARACTER_OS_LLM_PROVIDER=stub."
            )

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.7) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package not installed. Install with: pip install 'character-os[openai]'"
            ) from exc

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        content = response.choices[0].message.content
        return (content or "").strip()
