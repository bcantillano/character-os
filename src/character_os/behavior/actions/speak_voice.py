"""Speak-voice action — synthesizes audio after ResponseReadyEvent (Phase 1b)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from character_os.core.types import EmotionalDrives, TTSProfile
from character_os.events.types import ResponseReadyEvent, SpeechSynthesizedEvent
from character_os.voice.emotion_overlay import emotion_delivery_overlay
from character_os.voice.playback import enqueue_audio, stop_audio
from character_os.voice.provider import TTSProvider
from character_os.voice.speech_text import normalize_for_speech, split_speak_chunks


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
        get_drives: Callable[[], EmotionalDrives] | None = None,
    ) -> None:
        self.bus = bus
        self.tts = tts
        self.profile = profile
        self.output_dir = output_dir
        self.character_id = character_id
        self.session_id = session_id
        self.play = play
        self.get_drives = get_drives
        self.last_audio_path: Path | None = None

    def wire(self) -> None:
        self.bus.subscribe(ResponseReadyEvent, self._on_response_ready)

    def stop(self) -> None:
        """Stop background playback (session close / interrupt)."""
        stop_audio()

    def _profile_for_speak(self) -> TTSProfile:
        if not self.profile.emotion_overlay or self.get_drives is None:
            return self.profile
        overlay = emotion_delivery_overlay(self.get_drives())
        if not overlay:
            return self.profile
        base = (self.profile.instructions or "").rstrip()
        merged = f"{base}\n\n{overlay}" if base else overlay
        return replace(self.profile, instructions=merged)

    def _speak_text(self, text: str) -> str:
        speak_text = (
            normalize_for_speech(text) if self.profile.normalize_speech else text
        )
        if not speak_text.strip():
            return text
        return speak_text

    def _on_response_ready(self, event: ResponseReadyEvent) -> None:
        text = (event.text or "").strip()
        if not text:
            return

        speak_text = self._speak_text(text)
        # New speech interrupts any still-playing prior clip / queue.
        stop_audio()

        ext = self.profile.response_format if self.profile.response_format else "mp3"
        profile = self._profile_for_speak()

        if self.play:
            chunks = split_speak_chunks(speak_text)
            if not chunks:
                return
            first_path: Path | None = None
            for index, chunk in enumerate(chunks):
                output_path = self.output_dir / f"{event.event_id}.{index}.{ext}"
                path = self.tts.synthesize(chunk, profile, output_path)
                if first_path is None:
                    first_path = path
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
                enqueue_audio(path)
            return

        output_path = self.output_dir / f"{event.event_id}.{ext}"
        path = self.tts.synthesize(speak_text, profile, output_path)
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
