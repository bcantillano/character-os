"""OpenAI Whisper STT. Import openai only here — never from brain modules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from character_os.awareness.provider import STTProvider


class OpenAISTTProvider(STTProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when using the OpenAI STT provider. "
                "Copy .env.example to .env and set OPENAI_API_KEY, "
                "or use CHARACTER_OS_STT_PROVIDER=stub / --stt stub."
            )
        self.model = model or os.getenv("CHARACTER_OS_STT_MODEL", "whisper-1")
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

    def transcribe(self, audio_path: Path) -> str:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")
        client = self._get_client()
        with path.open("rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
            )
        text = getattr(result, "text", None) or str(result)
        return text.strip()
