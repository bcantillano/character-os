"""Relationship updates from interpreter signals (user trust / familiarity).

Scoring is character-agnostic: cooperation *with* the character raises trust;
hostility *toward* the character lowers it. Shared plans (even risky ones) are
not treated as hostility.
"""

from __future__ import annotations

import re

from character_os.brain.emotion import nudge
from character_os.core.types import CharacterState, Interpretation

# Per-turn caps so one message cannot swing the relationship wildly.
_TRUST_MIN, _TRUST_MAX = -0.12, 0.12
_FAM_MIN, _FAM_MAX = 0.0, 0.08

_POSITIVE_TRUST = {
    "trust",
    "trusting",
    "honest",
    "open",
    "friendly",
    "warm",
    "cooperative",
    "cooperate",
    "cooperation",
    "helpful",
    "help",
    "assist",
    "ally",
    "allied",
    "alliance",
    "partner",
    "partnership",
    "collaborate",
    "collaboration",
    "sincere",
    "apology",
    "apologetic",
    "grateful",
    "respectful",
    "gift",
    "offer",
    "share",
    "shared",
    "sharing",
    "reassure",
    "reassuring",
    "loyal",
    "loyalty",
    "bargain",
    "deal",
    "together",
    "propose",
    "proposal",
    "pledge",
}

# Hostility directed at the character — not generic violence/crime vocabulary.
_NEGATIVE_TRUST = {
    "threat",
    "threaten",
    "threatening",
    "hostile",
    "hostility",
    "insult",
    "insulting",
    "lie",
    "liar",
    "deceit",
    "deceptive",
    "betray",
    "betrayal",
    "mock",
    "mocking",
    "ridicule",
    "menace",
    "blackmail",
    "extort",
    "enemy",
}

_COOPERATION = {
    "cooperate",
    "cooperative",
    "cooperation",
    "ally",
    "allied",
    "alliance",
    "partner",
    "partnership",
    "collaborate",
    "collaboration",
    "bargain",
    "negotiate",
    "deal",
    "propose",
    "proposal",
    "together",
    "help",
    "assist",
    "join",
    "team",
    "split",
    "share",
    "shared",
    "sharing",
    "offer",
    "gift",
    "pledge",
    "plan",
    "loyal",
}

_HOSTILITY = {
    "threat",
    "threaten",
    "threatening",
    "hostile",
    "hostility",
    "insult",
    "insulting",
    "betray",
    "betrayal",
    "blackmail",
    "extort",
    "enemy",
    "arrest",  # "I will have you arrested"
    "kill you",
    "hurt you",
    "ruin you",
}

_FAMILIARITY_CUES = {
    "familiar",
    "acquaintance",
    "known",
    "name",
    "introduce",
    "introduction",
    "personal",
    "share",
    "shared",
    "sharing",
    "remember",
    "reunion",
}


def compute_relationship_deltas(interp: Interpretation) -> tuple[float, float]:
    """Return (trust_delta, familiarity_delta) for this interpretation.

    Prefers explicit numeric deltas from the interpreter when present;
    otherwise scores intent / tone / relationship_signals heuristics.

    Safety net: cooperation *with* the character cannot produce negative trust
    unless there is also hostility *toward* the character.
    """
    h_trust, h_fam = _heuristic_deltas(interp)
    trust = interp.trust_delta if interp.trust_delta is not None else h_trust
    fam = interp.familiarity_delta if interp.familiarity_delta is not None else h_fam

    coop = _is_cooperation_with_character(interp)
    hostile = _is_hostility_toward_character(interp)
    if coop and not hostile and trust < 0:
        # LLM sometimes scores shared risky plans as "bad"; override to at least
        # a small cooperative bump (or the heuristic if higher).
        trust = max(h_trust, 0.03)

    return _clamp_deltas(trust, fam)


def apply_relationship_update(state: CharacterState, interp: Interpretation) -> tuple[float, float]:
    """Mutate user trust/familiarity (and lightly nudge drive trust). Returns applied deltas."""
    dt, df = compute_relationship_deltas(interp)
    state.user_trust = _clamp01(state.user_trust + dt)
    state.user_familiarity = _clamp01(state.user_familiarity + df)
    if abs(dt) > 1e-9:
        state.emotional_drives = nudge(state.emotional_drives, trust=dt * 0.5)
    return dt, df


def _clamp_deltas(trust: float, familiarity: float) -> tuple[float, float]:
    return (
        max(_TRUST_MIN, min(_TRUST_MAX, trust)),
        max(_FAM_MIN, min(_FAM_MAX, familiarity)),
    )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _token_blob(interp: Interpretation) -> str:
    return " ".join(
        [
            interp.intent or "",
            interp.emotional_tone or "",
            interp.relationship_signals or "",
            interp.raw_message or "",
        ]
    ).lower()


def _is_cooperation_with_character(interp: Interpretation) -> bool:
    intent = (interp.intent or "").lower()
    signals = (interp.relationship_signals or "").lower()
    blob = _token_blob(interp)
    tokens = set(re.findall(r"[a-z']+", f"{intent} {signals}"))

    if any(
        k in intent
        for k in (
            "bargain",
            "negotiate",
            "deal",
            "ally",
            "alliance",
            "cooperate",
            "collaborate",
            "propose",
            "offer",
            "help",
            "assist",
            "partner",
            "share",
            "gift",
            "pledge",
        )
    ):
        return True
    if tokens & _COOPERATION:
        return True
    # Shared-plan phrasing in the user message.
    if any(
        phrase in blob
        for phrase in (
            "we can",
            "let's",
            "lets ",
            "together",
            "split the",
            "split it",
            "with you",
            "help you",
            "help me help",
            "our plan",
            "work with",
            "side with",
        )
    ):
        return True
    return False


def _is_hostility_toward_character(interp: Interpretation) -> bool:
    intent = (interp.intent or "").lower()
    tone = (interp.emotional_tone or "").lower()
    signals = (interp.relationship_signals or "").lower()
    raw = (interp.raw_message or "").lower()
    blob = f"{intent} {tone} {signals}"
    tokens = set(re.findall(r"[a-z']+", blob))

    if any(k in intent for k in ("threat", "insult", "intimidate", "blackmail", "betray")):
        return True
    if any(k in tone for k in ("hostile", "threatening", "contempt", "hateful")):
        return True
    if tokens & _HOSTILITY:
        return True
    # Direct second-person harm toward the character.
    if any(
        phrase in raw
        for phrase in (
            "kill you",
            "hurt you",
            "arrest you",
            "ruin you",
            "turn you in",
            "betray you",
            "you scum",
            "hate you",
        )
    ):
        return True
    return False


def _heuristic_deltas(interp: Interpretation) -> tuple[float, float]:
    trust = 0.0
    familiarity = 0.01  # every real exchange slightly increases familiarity

    intent = (interp.intent or "").lower()
    tone = (interp.emotional_tone or "").lower()
    signals = (interp.relationship_signals or "").lower()
    blob = f"{intent} {tone} {signals}"
    tokens = set(re.findall(r"[a-z']+", blob))

    hostile = _is_hostility_toward_character(interp)
    coop = _is_cooperation_with_character(interp)

    # Intent-shaped priors — hostility toward character first.
    if hostile or any(k in intent for k in ("threat", "insult")):
        trust -= 0.10
    elif any(k in intent for k in ("accuse",)) and not coop:
        trust -= 0.04
    elif any(
        k in intent
        for k in (
            "bargain",
            "negotiate",
            "deal",
            "ally",
            "alliance",
            "cooperate",
            "collaborate",
            "propose",
            "partner",
        )
    ):
        trust += 0.04
        familiarity += 0.02
    elif any(k in intent for k in ("share", "confess", "gift", "offer", "help", "assist", "pledge")):
        trust += 0.04
        familiarity += 0.03
    elif any(k in intent for k in ("greet", "introduce", "hello", "ahoy")):
        trust += 0.015
        familiarity += 0.025
    elif any(k in intent for k in ("joke", "banter", "tease")):
        trust += 0.02
        familiarity += 0.02
    elif any(k in intent for k in ("ask", "question", "inquire")):
        familiarity += 0.01
    elif any(k in intent for k in ("apolog", "thank")):
        trust += 0.05
        familiarity += 0.02
    elif coop:
        trust += 0.03
        familiarity += 0.02

    # Tone — do not punish "excited/intense" shared plans as hostility.
    if hostile or any(k in tone for k in ("hostile", "threatening", "contempt")):
        trust -= 0.05
    elif any(k in tone for k in ("warm", "friendly", "grateful", "sincere", "kind", "eager")):
        trust += 0.03
    elif any(k in tone for k in ("suspicious", "wary", "guarded")) and not coop:
        trust -= 0.02

    # Free-text relationship signals
    pos = len(tokens & _POSITIVE_TRUST)
    neg = 0 if coop and not hostile else len(tokens & _NEGATIVE_TRUST)
    trust += 0.025 * pos
    trust -= 0.035 * neg

    fam_hits = tokens & _FAMILIARITY_CUES
    if fam_hits and "unfamiliar" not in signals and "stranger" not in signals:
        familiarity += 0.02 * len(fam_hits)

    # Sharing a durable personal fact (e.g. name) deepens familiarity
    for fact in interp.notable_facts:
        fl = fact.lower()
        if "name" in fl or fl.startswith("the user"):
            familiarity += 0.03
            trust += 0.02
            break

    return trust, familiarity
