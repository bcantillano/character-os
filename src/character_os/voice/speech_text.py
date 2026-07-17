"""Speech-only text helpers (printed dialogue stays unchanged)."""

from __future__ import annotations

import re

# Orthography that often triggers a cartoon "pirate act" in TTS.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[Aa]rrr+\b[!.,]?"), ""),
    (re.compile(r"\bye\b"), "you"),
    (re.compile(r"\bYe\b"), "You"),
    (re.compile(r"\byer\b"), "your"),
    (re.compile(r"\bYer\b"), "Your"),
    (re.compile(r"\bfer\b"), "for"),
    (re.compile(r"\bFer\b"), "For"),
    (re.compile(r"\bo'\b"), "of"),
    (re.compile(r"\bme\b(?=\s+(?:heart|mate|lad|friend|boy|beauty)\b)", re.I), "my"),
    (re.compile(r"\bMe\b(?=\s+(?:heart|mate|lad|friend|boy|beauty)\b)"), "My"),
    (re.compile(r"\b'em\b"), "them"),
]


def normalize_for_speech(text: str) -> str:
    """Soften dialect spellings for synthesis; keep meaning and energy."""
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\s+([,.;!?])", r"\1", out)
    return out.strip()
