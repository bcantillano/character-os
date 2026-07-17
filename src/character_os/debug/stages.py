"""Lifecycle stage tracing via event-bus wildcard subscription."""

from __future__ import annotations

import sys
from typing import TextIO

from character_os.events.bus import EventBus
from character_os.events.types import (
    Event,
    InputInterpretedEvent,
    IntentDecidedEvent,
    ResponseReadyEvent,
    SpeechSynthesizedEvent,
    StateChangedEvent,
    ThoughtsGeneratedEvent,
    TimeTickEvent,
    UserMessageEvent,
)

# Observe → Interpret → Reflect → Decide → Act → Remember
_STAGE_LABELS: dict[type[Event], str] = {
    UserMessageEvent: "Observe",
    InputInterpretedEvent: "Interpret",
    StateChangedEvent: "Reflect",
    IntentDecidedEvent: "Decide",
    ThoughtsGeneratedEvent: "Act/Thoughts",
    ResponseReadyEvent: "Act/Speak",
    SpeechSynthesizedEvent: "Act/Voice",
    TimeTickEvent: "Tick",
}


def _summarize(event: Event) -> str:
    if isinstance(event, UserMessageEvent):
        text = event.text.replace("\n", " ").strip()
        return f'text="{_clip(text, 60)}"'
    if isinstance(event, InputInterpretedEvent) and event.interpretation:
        i = event.interpretation
        return f"intent={i.intent} tone={i.emotional_tone}"
    if isinstance(event, StateChangedEvent):
        return f"trigger={event.trigger} {_clip(event.summary, 50)}"
    if isinstance(event, IntentDecidedEvent) and event.intent:
        return f"{event.intent.kind.value}: {_clip(event.intent.reasoning, 50)}"
    if isinstance(event, ThoughtsGeneratedEvent):
        return _clip(event.thoughts.replace("\n", " "), 60)
    if isinstance(event, ResponseReadyEvent):
        return _clip(event.text.replace("\n", " "), 60)
    if isinstance(event, SpeechSynthesizedEvent):
        return f"provider={event.provider} {_clip(event.audio_path, 50)}"
    if isinstance(event, TimeTickEvent):
        return f"tick={event.tick_index}"
    return ""


def _clip(text: str, n: int) -> str:
    text = text.strip()
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def format_stage_line(event: Event) -> str | None:
    label = _STAGE_LABELS.get(type(event))
    if label is None:
        return None
    detail = _summarize(event)
    return f"[stage:{label}] {detail}".rstrip() if detail else f"[stage:{label}]"


def attach_stage_logger(bus: EventBus, stream: TextIO | None = None) -> None:
    """Print compact lifecycle lines for each pipeline event."""
    out = stream or sys.stderr

    def _on_event(event: Event) -> None:
        line = format_stage_line(event)
        if line:
            print(line, file=out)

    bus.subscribe_all(_on_event)
