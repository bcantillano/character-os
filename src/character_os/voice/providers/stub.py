"""Stub TTS — writes a text sidecar so tests need no audio APIs."""

from __future__ import annotations

from pathlib import Path

from character_os.core.types import TTSProfile
from character_os.voice.provider import TTSProvider


class StubTTSProvider(TTSProvider):
    def synthesize(self, text: str, profile: TTSProfile, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Use .txt so playback helpers can skip non-audio stubs cleanly.
        stub_path = output_path.with_suffix(".txt")
        stub_path.write_text(
            f"[stub-tts voice={profile.voice} model={profile.model}]\n{text}\n",
            encoding="utf-8",
        )
        return stub_path
