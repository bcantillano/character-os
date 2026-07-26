"""Normalize speech Observe into the shared text interpret path."""

from __future__ import annotations

from character_os.events.bus import EventBus
from character_os.events.types import SpeechRecognizedEvent, UserMessageEvent


class SpeechInputBridge:
    """SpeechRecognizedEvent → UserMessageEvent (same Interpret→Remember pipeline)."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def wire(self) -> None:
        self.bus.subscribe(SpeechRecognizedEvent, self.on_speech_recognized)

    def on_speech_recognized(self, event: SpeechRecognizedEvent) -> None:
        text = (event.text or "").strip()
        if not text:
            return
        self.bus.publish(
            UserMessageEvent(
                character_id=event.character_id,
                session_id=event.session_id,
                text=text,
            )
        )
