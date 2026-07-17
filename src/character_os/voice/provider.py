"""TTS provider abstraction. Behavior modules depend only on this interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from character_os.core.types import TTSProfile


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, profile: TTSProfile, output_path: Path) -> Path:
        """Write spoken audio for ``text`` to ``output_path`` and return that path."""


def create_tts_provider(name: str | None = None) -> TTSProvider:
    """Factory for TTS providers. Default: stub (no API key / no audio hardware)."""
    import os

    from character_os.env import load_env

    load_env()
    provider_name = (name or os.getenv("CHARACTER_OS_TTS_PROVIDER") or "stub").lower()
    if provider_name == "openai":
        from character_os.voice.providers.openai import OpenAITTSProvider

        return OpenAITTSProvider()
    if provider_name == "stub":
        from character_os.voice.providers.stub import StubTTSProvider

        return StubTTSProvider()
    raise ValueError(f"Unknown TTS provider: {provider_name}")
