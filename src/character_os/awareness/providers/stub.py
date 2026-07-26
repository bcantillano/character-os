"""Stub STT — reads .txt as transcript or returns a fixed phrase for audio files."""

from __future__ import annotations

from pathlib import Path

from character_os.awareness.provider import STTProvider

_DEFAULT_TRANSCRIPT = "Hello from stub speech recognition."


class StubSTTProvider(STTProvider):
    def __init__(self, default_transcript: str = _DEFAULT_TRANSCRIPT) -> None:
        self.default_transcript = default_transcript

    def transcribe(self, audio_path: Path) -> str:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
        return self.default_transcript
