"""Stage debug logger tests."""

from io import StringIO

from character_os.core.types import Intent, IntentKind, Interpretation
from character_os.debug.stages import attach_stage_logger, format_stage_line
from character_os.events.bus import EventBus
from character_os.events.types import (
    InputInterpretedEvent,
    IntentDecidedEvent,
    ResponseReadyEvent,
    UserMessageEvent,
)


def test_format_stage_line_labels():
    assert format_stage_line(UserMessageEvent(text="hello there")).startswith("[stage:Observe]")
    interp = Interpretation(intent="greet", emotional_tone="warm", raw_message="hi")
    line = format_stage_line(InputInterpretedEvent(interpretation=interp))
    assert line is not None and "Interpret" in line and "greet" in line
    intent = Intent(kind=IntentKind.SPEAK, reasoning="reply warmly")
    assert "Decide" in (format_stage_line(IntentDecidedEvent(intent=intent)) or "")
    assert "Act/Speak" in (format_stage_line(ResponseReadyEvent(text="Ahoy")) or "")


def test_attach_stage_logger_prints():
    bus = EventBus()
    buf = StringIO()
    attach_stage_logger(bus, stream=buf)
    bus.publish(UserMessageEvent(text="ping"))
    bus.publish(ResponseReadyEvent(text="pong"))
    out = buf.getvalue()
    assert "[stage:Observe]" in out
    assert "[stage:Act/Speak]" in out
