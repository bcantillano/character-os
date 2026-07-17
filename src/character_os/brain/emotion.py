"""Emotional drive helpers (0.0–1.0)."""

from __future__ import annotations

from character_os.core.types import EmotionalDrives, Interpretation

# Resting targets for idle / recovery (trust is relationship-driven, left alone).
_BASELINE_CURIOSITY = 0.5
_BASELINE_EXCITEMENT = 0.4
_BASELINE_FEAR = 0.35
_BASELINE_CONFIDENCE = 0.55
_BASELINE_ENERGY = 0.55


def apply_tick_decay(drives: EmotionalDrives) -> EmotionalDrives:
    """Gentle movement toward resting baselines on idle ticks."""
    rate = 0.05
    hot_rate = 0.10

    def move(current: float, target: float, r: float = rate) -> float:
        return current + (target - current) * r

    return EmotionalDrives(
        curiosity=move(drives.curiosity, _BASELINE_CURIOSITY, hot_rate),
        trust=drives.trust,
        excitement=move(drives.excitement, _BASELINE_EXCITEMENT, hot_rate),
        fear=move(drives.fear, _BASELINE_FEAR),
        confidence=move(drives.confidence, _BASELINE_CONFIDENCE),
        energy=move(drives.energy, _BASELINE_ENERGY),
    ).clamp()


def nudge(drives: EmotionalDrives, **deltas: float) -> EmotionalDrives:
    data = drives.as_dict()
    for key, delta in deltas.items():
        if key in data:
            data[key] = data[key] + delta
    return EmotionalDrives(**data).clamp()


def diminishing_nudge(drives: EmotionalDrives, **deltas: float) -> EmotionalDrives:
    """Apply deltas with soft saturation (harder to push further near 0 or 1)."""
    data = drives.as_dict()
    for key, delta in deltas.items():
        if key not in data or abs(delta) < 1e-12:
            continue
        current = data[key]
        if delta > 0:
            data[key] = current + delta * (1.0 - current)
        else:
            data[key] = current + delta * current
    return EmotionalDrives(**data).clamp()


def recover_hot_drives(drives: EmotionalDrives, *, rate: float = 0.08) -> EmotionalDrives:
    """Pull curiosity/excitement toward baseline (works without time ticks)."""

    def move(current: float, target: float) -> float:
        return current + (target - current) * rate

    return EmotionalDrives(
        curiosity=move(drives.curiosity, _BASELINE_CURIOSITY),
        trust=drives.trust,
        excitement=move(drives.excitement, _BASELINE_EXCITEMENT),
        fear=drives.fear,
        confidence=drives.confidence,
        energy=drives.energy,
    ).clamp()


def unstick_pegged_drives(
    drives: EmotionalDrives,
    *,
    threshold: float = 0.92,
    rate: float = 0.35,
) -> EmotionalDrives:
    """One-shot stronger recovery when loading already-pegged curiosity/excitement."""
    if drives.curiosity < threshold and drives.excitement < threshold:
        return drives
    return recover_hot_drives(drives, rate=rate)


def apply_interpretation_drives(
    drives: EmotionalDrives,
    interp: Interpretation,
) -> EmotionalDrives:
    """Nudge drives from interpretation signals — not a flat bump every message.

    Always recovers curiosity/excitement slightly toward baseline first so
    no-tick CLI sessions (and previously pegged SQLite values) can unstick.
    """
    # Recover before signal bumps so planning chats don't leave drives at 1.0 forever.
    drives = recover_hot_drives(drives, rate=0.08)

    intent = (interp.intent or "").lower()
    tone = (interp.emotional_tone or "").lower()
    signals = (interp.relationship_signals or "").lower()
    raw = (interp.raw_message or "").lower()

    curiosity = 0.0
    excitement = 0.0
    fear = 0.0
    confidence = 0.0
    energy = -0.008  # light cost of engaging

    # Curiosity: questions, secrets, challenges, intrigue — not every hello.
    if any(k in intent for k in ("ask", "question", "inquire", "challenge", "reveal", "secret")):
        curiosity += 0.05
    elif any(k in tone for k in ("curious", "mysterious", "intriguing", "suspicious")):
        curiosity += 0.035
    elif any(k in intent for k in ("share", "propose", "bargain", "offer", "confess")):
        curiosity += 0.02
    elif any(k in intent for k in ("greet", "hello", "ahoy")) and "unfamiliar" in signals:
        curiosity += 0.01

    # Excitement: alliances, offers, danger, humor, eager tone.
    # Avoid bumping on every mention of world keywords alone (map/navy appear constantly).
    if any(
        k in intent
        for k in (
            "threat",
            "bargain",
            "propose",
            "ally",
            "alliance",
            "gift",
            "offer",
            "joke",
            "deal",
            "pledge",
        )
    ):
        excitement += 0.04
    if any(k in tone for k in ("eager", "excited", "angry", "hostile", "warm", "grateful")):
        excitement += 0.025
    if any(k in intent for k in ("threat",)) or any(
        phrase in raw for phrase in ("royal navy", "ambush", "attack us", "arrest")
    ):
        excitement += 0.02

    # Fear / confidence: hostility toward character vs cooperation.
    if any(k in intent for k in ("threat", "insult", "intimidate", "blackmail")) or any(
        k in tone for k in ("hostile", "threatening", "contempt")
    ):
        fear += 0.05
        confidence -= 0.02
        excitement += 0.015
    elif any(
        k in intent
        for k in ("ally", "alliance", "bargain", "cooperate", "propose", "gift", "pledge", "help")
    ):
        fear -= 0.015
        confidence += 0.015

    return diminishing_nudge(
        drives,
        curiosity=curiosity,
        excitement=excitement,
        fear=fear,
        confidence=confidence,
        energy=energy,
    )


def format_relationship_stance(trust: float, familiarity: float) -> str:
    """Human-readable rapport guidance for thoughts / spoken dialogue prompts."""
    band = _rapport_band(trust, familiarity)
    numbers = f"(trust={trust:.2f}, familiarity={familiarity:.2f})"
    if band == "stranger":
        return (
            f"Stranger {numbers}. Keep your guard high. Testing motives and asking "
            "hard questions about loyalty is natural."
        )
    if band == "cautious":
        return (
            f"Cautious acquaintance {numbers}. Still wary, but engage their ideas. "
            "Do not only interrogate — mix suspicion with curiosity about the plan."
        )
    if band == "building":
        return (
            f"Building trust {numbers}. They have earned some credit. "
            "Do not restart from zero suspicion every turn. Acknowledge cooperation; "
            "prefer forward-looking questions (plan, next step, practical details) "
            "over repeating 'will you betray me?'"
        )
    return (
        f"Trusted-enough partner {numbers} — not blind. Assume good faith unless given "
        "a new reason to doubt. Focus on shared goals and plans; loyalty tests should be rare."
    )


def _rapport_band(trust: float, familiarity: float) -> str:
    score = 0.65 * trust + 0.35 * familiarity
    if score < 0.28:
        return "stranger"
    if score < 0.42:
        return "cautious"
    if score < 0.58:
        return "building"
    return "partner"
