"""Speak-voice action — synthesizes audio after ResponseReadyEvent (Phase 1b)."""

from __future__ import annotations

from pathlib import Path

from character_os.core.types import TTSProfile
from character_os.events.types import ResponseReadyEvent, SpeechSynthesizedEvent
from character_os.voice.playback import play_audio
from character_os.voice.provider import TTSProvider


class SpeakVoiceAction:
    """Subscribes to ResponseReadyEvent; does not replace text speak."""

    def __init__(
        self,
        bus,
        tts: TTSProvider,
        profile: TTSProfile,
        output_dir: Path,
        *,
        character_id: str,
        session_id: str,
        play: bool = False,
    ) -> None:
        self.bus = bus
        self.tts = tts
        self.profile = profile
        self.output_dir = output_dir
        self.character_id = character_id
        self.session_id = session_id
        self.play = play
        self.last_audio_path: Path | None = None

    def wire(self) -> None:
        self.bus.subscribe(ResponseReadyEvent, self._on_response_ready)

    def _on_response_ready(self, event: ResponseReadyEvent) -> None:
        text = (event.text or "").strip()
        if not text:
            return

        ext = self.profile.response_format if self.profile.response_format else "mp3"
        # Stub writes .txt; keep requested stem for openai.
        output_path = self.output_dir / f"{event.event_id}.{ext}"
        path = self.tts.synthesize(text, self.profile, output_path)
        self.last_audio_path = path

        self.bus.publish(
            SpeechSynthesizedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                text=text,
                audio_path=str(path),
                provider=type(self.tts).__name__,
            )
        )
        if self.play:
            play_audio(path)
