"""Emotional drive helpers (0.0–1.0)."""

from __future__ import annotations

from character_os.core.types import EmotionalDrives


def apply_tick_decay(drives: EmotionalDrives) -> EmotionalDrives:
    """Gentle movement toward resting baselines on idle ticks."""
    baselines = EmotionalDrives(
        curiosity=0.5,
        trust=drives.trust,  # trust changes mainly via interaction
        excitement=0.4,
        fear=0.35,
        confidence=0.55,
        energy=0.55,
    )
    rate = 0.05

    def move(current: float, target: float) -> float:
        return current + (target - current) * rate

    return EmotionalDrives(
        curiosity=move(drives.curiosity, baselines.curiosity),
        trust=drives.trust,
        excitement=move(drives.excitement, baselines.excitement),
        fear=move(drives.fear, baselines.fear),
        confidence=move(drives.confidence, baselines.confidence),
        energy=move(drives.energy, baselines.energy),
    ).clamp()


def nudge(drives: EmotionalDrives, **deltas: float) -> EmotionalDrives:
    data = drives.as_dict()
    for key, delta in deltas.items():
        if key in data:
            data[key] = data[key] + delta
    return EmotionalDrives(**data).clamp()
