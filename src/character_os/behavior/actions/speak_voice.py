"""Speak-voice action — synthesizes audio after ResponseReadyEvent (Phase 1b)."""

from __future__ import annotations

import threading
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
        self._synth_generation = 0
        self._synth_lock = threading.Lock()
        self._synth_worker: threading.Thread | None = None

    def wire(self) -> None:
        self.bus.subscribe(ResponseReadyEvent, self._on_response_ready)

    def stop(self) -> None:
        """Stop background playback and cancel remaining chunk synthesis."""
        with self._synth_lock:
            self._synth_generation += 1
            self._synth_worker = None
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
        # New speech interrupts any still-playing prior clip / queue / synth.
        self.stop()

        ext = self.profile.response_format if self.profile.response_format else "mp3"
        profile = self._profile_for_speak()

        if self.play:
            chunks = split_speak_chunks(speak_text)
            if not chunks:
                return
            first_path = self.tts.synthesize(
                chunks[0],
                profile,
                self.output_dir / f"{event.event_id}.0.{ext}",
            )
            self.last_audio_path = first_path
            self.bus.publish(
                SpeechSynthesizedEvent(
                    character_id=self.character_id,
                    session_id=self.session_id,
                    text=text,
                    audio_path=str(first_path),
                    provider=type(self.tts).__name__,
                )
            )
            enqueue_audio(first_path)

            remaining = list(enumerate(chunks[1:], start=1))
            if remaining:
                with self._synth_lock:
                    gen = self._synth_generation
                    worker = threading.Thread(
                        target=self._synthesize_remaining,
                        args=(gen, event.event_id, ext, profile, remaining),
                        name="character-os-tts-chunks",
                        daemon=True,
                    )
                    self._synth_worker = worker
                    worker.start()
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

    def _synthesize_remaining(
        self,
        gen: int,
        event_id: str,
        ext: str,
        profile: TTSProfile,
        remaining: list[tuple[int, str]],
    ) -> None:
        for index, chunk in remaining:
            with self._synth_lock:
                if gen != self._synth_generation:
                    return
            path = self.tts.synthesize(
                chunk,
                profile,
                self.output_dir / f"{event_id}.{index}.{ext}",
            )
            with self._synth_lock:
                if gen != self._synth_generation:
                    return
            enqueue_audio(path)
        with self._synth_lock:
            if gen == self._synth_generation and self._synth_worker is threading.current_thread():
                self._synth_worker = None
