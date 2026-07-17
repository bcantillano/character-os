"""End-to-end lifecycle smoke tests with stub LLM."""

from character_os.core.types import IntentKind
from character_os.events.types import (
    InputInterpretedEvent,
    IntentDecidedEvent,
    ResponseReadyEvent,
    StateChangedEvent,
    ThoughtsGeneratedEvent,
    UserMessageEvent,
)
from character_os.llm.providers.stub import StubProvider
from character_os.session import CharacterSession


def test_user_message_pipeline_emits_expected_events():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    session.bus.start_recording()
    result = session.send_message("Ahoy there, captain!")
    history = session.bus.stop_recording()
    session.close()

    types = [type(e) for e in history]
    assert UserMessageEvent in types
    assert InputInterpretedEvent in types
    assert StateChangedEvent in types
    assert IntentDecidedEvent in types
    assert ThoughtsGeneratedEvent in types
    assert ResponseReadyEvent in types
    assert result.text
    assert "Aye" in result.text or len(result.text) > 10


def test_time_tick_does_not_speak():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    session.bus.start_recording()
    before = session.brain.state.emotional_drives.as_dict()
    session.tick()
    history = session.bus.stop_recording()

    assert any(isinstance(e, StateChangedEvent) and e.trigger == "time_tick" for e in history)
    intent_events = [e for e in history if isinstance(e, IntentDecidedEvent)]
    assert intent_events
    assert intent_events[-1].intent is not None
    assert intent_events[-1].intent.kind == IntentKind.UPDATE_STATE
    assert not any(isinstance(e, ResponseReadyEvent) for e in history)

    after = session.brain.state.emotional_drives.as_dict()
    # Drives should still be present (may have moved slightly).
    assert set(after) == set(before)
    assert session.brain.state.tick_count == 1
    session.close()
