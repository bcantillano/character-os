"""Tests for relationship trust / familiarity updates."""

from character_os.brain.relationship import apply_relationship_update, compute_relationship_deltas
from character_os.core.types import CharacterState, EmotionalDrives, Interpretation
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


def test_explicit_deltas_are_clamped():
    trust, fam = compute_relationship_deltas(
        _interp(trust_delta=0.5, familiarity_delta=0.5)
    )
    assert trust == 0.12
    assert fam == 0.08


def test_threat_heuristic_lowers_trust():
    trust, fam = compute_relationship_deltas(
        _interp(
            intent="threaten",
            emotional_tone="hostile",
            relationship_signals="threat, hostility",
            trust_delta=None,
            familiarity_delta=None,
        )
    )
    assert trust < -0.05
    assert fam > 0  # still known a bit better


def test_share_name_heuristic_raises_familiarity():
    trust, fam = compute_relationship_deltas(
        _interp(
            intent="share",
            emotional_tone="open",
            relationship_signals="sharing name",
            notable_facts=["The user's name is Byron"],
            trust_delta=None,
            familiarity_delta=None,
        )
    )
    assert trust > 0.03
    assert fam >= 0.05


def test_apply_updates_state_and_drive_trust():
    state = CharacterState(
        character_id="captain-redbeard",
        emotional_drives=EmotionalDrives(trust=0.5),
        goals=[],
        user_trust=0.2,
        user_familiarity=0.0,
    )
    before_drive = state.emotional_drives.trust
    dt, df = apply_relationship_update(
        state,
        _interp(trust_delta=0.08, familiarity_delta=0.05),
    )
    assert dt == 0.08
    assert df == 0.05
    assert state.user_trust == 0.28
    assert state.user_familiarity == 0.05
    assert state.emotional_drives.trust == before_drive + 0.04


def test_pipeline_greeting_moves_relationship():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    before_t = session.brain.state.user_trust
    before_f = session.brain.state.user_familiarity
    session.send_message("Ahoy there, captain!")
    assert session.brain.state.user_trust > before_t
    assert session.brain.state.user_familiarity > before_f
    session.close()


def test_shared_plan_raises_trust_even_if_risky():
    trust, fam = compute_relationship_deltas(
        _interp(
            intent="propose_alliance",
            emotional_tone="eager",
            relationship_signals="shared plan, steal from rivals, split treasure",
            raw_message=(
                "What if we use the coins to buy weapons to steal the map from them. "
                "We can split the treasure."
            ),
            trust_delta=None,
            familiarity_delta=None,
        )
    )
    assert trust > 0
    assert fam > 0


def test_llm_negative_delta_overridden_for_cooperation():
    """Safety net: cooperation without hostility cannot stay negative."""
    trust, _fam = compute_relationship_deltas(
        _interp(
            intent="bargain",
            emotional_tone="eager",
            relationship_signals="alliance, shared heist plan",
            raw_message="Let's take it together and split it.",
            trust_delta=-0.08,  # mis-scored by LLM
            familiarity_delta=0.03,
        )
    )
    assert trust >= 0.03


def test_hostility_toward_character_still_lowers_trust():
    trust, fam = compute_relationship_deltas(
        _interp(
            intent="threaten",
            emotional_tone="hostile",
            relationship_signals="threat toward character",
            raw_message="I will have you arrested.",
            trust_delta=None,
            familiarity_delta=None,
        )
    )
    assert trust < -0.05
    assert fam > 0


def test_pipeline_shared_plan_increases_trust():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    session.brain.state.user_trust = 0.24
    session.send_message(
        "What if we buy weapons to steal the map from the guards. We can split the treasure."
    )
    assert session.brain.state.user_trust > 0.24
    session.close()


def test_pipeline_threat_reduces_trust():
    session = CharacterSession(llm=StubProvider(), enable_scheduler=False, persist=False)
    session.brain.state.user_trust = 0.4
    session.send_message("I will have you arrested, you scum!")
    assert session.brain.state.user_trust < 0.4
    session.close()
