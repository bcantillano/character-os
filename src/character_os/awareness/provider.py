"""STT provider abstraction. Awareness modules depend only on this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        """Return a transcript for the audio at ``audio_path``."""


def create_stt_provider(name: str | None = None) -> STTProvider:
    """Factory for STT providers. Default: stub (no API key / no mic)."""
    import os

    from character_os.env import load_env

    load_env()
    provider_name = (name or os.getenv("CHARACTER_OS_STT_PROVIDER") or "stub").lower()
    if provider_name == "openai":
        from character_os.awareness.providers.openai import OpenAISTTProvider

        return OpenAISTTProvider()
    if provider_name == "stub":
        from character_os.awareness.providers.stub import StubSTTProvider

        return StubSTTProvider()
    raise ValueError(f"Unknown STT provider: {provider_name}")
