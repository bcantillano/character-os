"""Event type definitions for Character OS.

All inputs enter as events. Future phases add types without changing the bus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from character_os.core.types import Intent, Interpretation


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Event:
    """Base event. All events carry identity and timing metadata."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=_utcnow)
    character_id: str = ""
    session_id: str = ""


@dataclass(frozen=True)
class UserMessageEvent(Event):
    text: str = ""


@dataclass(frozen=True)
class TimeTickEvent(Event):
    tick_index: int = 0
    interval_seconds: float = 30.0


@dataclass(frozen=True)
class InputInterpretedEvent(Event):
    interpretation: Interpretation | None = None


@dataclass(frozen=True)
class StateChangedEvent(Event):
    trigger: str = ""  # "user_message" | "time_tick"
    summary: str = ""
    state_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntentDecidedEvent(Event):
    intent: Intent | None = None


@dataclass(frozen=True)
class BehaviorRequestedEvent(Event):
    intent: Intent | None = None


@dataclass(frozen=True)
class ThoughtsGeneratedEvent(Event):
    thoughts: str = ""
    intent: Intent | None = None


@dataclass(frozen=True)
class ResponseReadyEvent(Event):
    text: str = ""
    thoughts: str = ""


@dataclass(frozen=True)
class SpeechSynthesizedEvent(Event):
    """Phase 1b: TTS finished for a spoken response."""

    text: str = ""
    audio_path: str = ""
    provider: str = ""


# Reserved for future phases (defined so the bus can accept them later).
@dataclass(frozen=True)
class VisionDetectedEvent(Event):
    description: str = ""


@dataclass(frozen=True)
class SensorReadingEvent(Event):
    sensor: str = ""
    value: Any = None


@dataclass(frozen=True)
class SpeechRecognizedEvent(Event):
    """Phase 3: STT produced a transcript (Observe for speech)."""

    text: str = ""
    audio_path: str = ""
    provider: str = ""


@dataclass(frozen=True)
class MotionCompletedEvent(Event):
    motion_id: str = ""
