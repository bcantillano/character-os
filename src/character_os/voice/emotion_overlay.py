"""Subtle emotional-drive hints appended to TTS instructions."""

from __future__ import annotations

from character_os.core.types import EmotionalDrives


def emotion_delivery_overlay(drives: EmotionalDrives) -> str:
    """Return a short delivery nudge from current drives (may be empty).

    Kept intentionally mild so restrained characters (e.g. Lumen) stay in character.
    """
    hints: list[str] = []
    d = drives.clamp()

    if d.curiosity >= 0.7:
        hints.append("Lean gently into curiosity — a soft lift when asking or noticing.")
    if d.fear >= 0.55:
        hints.append("Speak a little softer and more carefully; reassure without urgency.")
    if d.excitement >= 0.65:
        hints.append("Allow only a mild brightening — stay mostly restrained.")
    elif d.excitement <= 0.25 and d.energy <= 0.4:
        hints.append("Keep the energy quiet and unhurried, without dragging.")
    if d.confidence >= 0.7:
        hints.append("Hold a steady, clear confidence — no boastfulness.")
    elif d.confidence <= 0.35:
        hints.append("Sound slightly more tentative and thoughtful.")
    if d.trust >= 0.65:
        hints.append("Warmth may rise slightly; still avoid perkiness.")

    if not hints:
        return ""
    return "Momentary delivery (from current state):\n- " + "\n- ".join(hints)
