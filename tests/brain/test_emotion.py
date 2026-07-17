"""Tests for emotional drive updates and rapport stance."""

from character_os.brain.emotion import (
    apply_interpretation_drives,
    diminishing_nudge,
    format_relationship_stance,
    recover_hot_drives,
    unstick_pegged_drives,
)
from character_os.core.types import EmotionalDrives, Interpretation
from character_os.llm.providers.stub import StubProvider
from character_os.session import CharacterSession


def _interp(**kwargs) -> Interpretation:
    base = {
        "intent": "converse",
        "emotional_tone": "neutral",
        "relationship_signals": "",
        "notable_facts": [],
        "raw_message": "hello",
    }
    base.update(kwargs)
    return Interpretation(**base)


def test_diminishing_nudge_slows_near_ceiling():
    high = EmotionalDrives(curiosity=0.95, excitement=0.95)
    after = diminishing_nudge(high, curiosity=0.05, excitement=0.05)
    assert after.curiosity < 0.96
    assert after.excitement < 0.96


def test_recover_hot_drives_unsticks_ceiling():
    pegged = EmotionalDrives(curiosity=1.0, excitement=1.0)
    after = recover_hot_drives(pegged, rate=0.08)
    assert after.curiosity < 1.0
    assert after.excitement < 1.0
    assert after.curiosity > 0.9


def test_unstick_pegged_drives_on_load():
    pegged = EmotionalDrives(curiosity=1.0, excitement=1.0, energy=0.4)
    after = unstick_pegged_drives(pegged)
    assert after.curiosity < 0.9
    assert after.excitement < 0.9
    assert after.energy == 0.4


def test_greeting_does_not_raise_curiosity_toward_ceiling():
    drives = EmotionalDrives(curiosity=0.7, excitement=0.5, energy=0.6)
    after = apply_interpretation_drives(
        drives,
        _interp(intent="greet", emotional_tone="neutral", relationship_signals="unfamiliar"),
    )
    # Recovery pulls toward 0.5; greet bump is tiny — must not climb toward 1.0.
    assert after.curiosity <= drives.curiosity + 0.01


def test_alliance_proposal_raises_excitement_more_than_greeting():
    base = EmotionalDrives(curiosity=0.5, excitement=0.4)
    greet = apply_interpretation_drives(
        base,
        _interp(intent="greet", emotional_tone="neutral"),
    )
    ally = apply_interpretation_drives(
        base,
        _interp(
            intent="propose_alliance",
            emotional_tone="eager",
            relationship_signals="shared plan",
            raw_message="Let's steal the map and split it.",
        ),
    )
    assert ally.excitement > greet.excitement


def test_planning_turns_pull_curiosity_down_from_ceiling():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    session.brain.state.emotional_drives = EmotionalDrives(
        curiosity=1.0,
        excitement=1.0,
        trust=0.4,
        fear=0.4,
        confidence=0.6,
        energy=0.5,
    )
    session.send_message("Hello")
    session.send_message("Hello again")
    assert session.brain.state.emotional_drives.curiosity < 0.95
    assert session.brain.state.emotional_drives.excitement < 0.95
    session.close()


def test_relationship_stance_bands():
    stranger = format_relationship_stance(0.15, 0.05)
    building = format_relationship_stance(0.45, 0.50)
    partner = format_relationship_stance(0.75, 0.70)
    assert "Stranger" in stranger
    assert "Building trust" in building
    assert "Trusted-enough" in partner
    assert "will you betray me" in building.lower() or "betray" in building.lower()
