"""OpenAI TTS. Import openai only here — never from brain modules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from character_os.core.types import TTSProfile
from character_os.voice.provider import TTSProvider


class OpenAITTSProvider(TTSProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the OpenAI TTS provider. "
                "Copy .env.example to .env and set OPENAI_API_KEY, "
                "or use CHARACTER_OS_TTS_PROVIDER=stub / --tts stub."
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

    def synthesize(self, text: str, profile: TTSProfile, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": profile.model,
            "voice": profile.voice,
            "input": text,
            "response_format": profile.response_format,
            "speed": profile.speed,
        }
        if profile.instructions and "gpt-4o-mini-tts" in profile.model:
            kwargs["instructions"] = profile.instructions

        with client.audio.speech.with_streaming_response.create(**kwargs) as response:
            response.stream_to_file(output_path)
        return output_path
