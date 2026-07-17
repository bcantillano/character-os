"""LLM provider abstraction. Business modules depend only on this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.7) -> str:
        """Return model text for the given messages."""


def create_provider(name: str | None = None) -> LLMProvider:
    """Factory for configured providers. Default: stub (no API key required)."""
    import os

    from character_os.env import load_env

    load_env()
    provider_name = (name or os.getenv("CHARACTER_OS_LLM_PROVIDER") or "stub").lower()
    if provider_name == "openai":
        from character_os.llm.providers.openai import OpenAIProvider

        return OpenAIProvider()
    if provider_name == "stub":
        from character_os.llm.providers.stub import StubProvider

        return StubProvider()
    raise ValueError(f"Unknown LLM provider: {provider_name}")
