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


# Sentence end: . ! ? … (optional closing quote) then whitespace or end.
_SENTENCE_END = re.compile(r'(?<=[.!?…])["\']?\s+')
_MIN_CHUNK_CHARS = 28


def split_speak_chunks(text: str) -> list[str]:
    """Split spoken text into sentence-sized chunks for early playback.

    Short trailing fragments are merged into the previous chunk so TTS does not
    get tiny one-word clips.
    """
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return []

    parts = [p.strip() for p in _SENTENCE_END.split(cleaned) if p.strip()]
    if not parts:
        return [cleaned]
    if len(parts) == 1:
        return parts

    chunks: list[str] = []
    buf = parts[0]
    for part in parts[1:]:
        # Merge short fragments into the current buffer.
        if len(buf) < _MIN_CHUNK_CHARS or len(part) < _MIN_CHUNK_CHARS:
            buf = f"{buf} {part}".strip()
        else:
            chunks.append(buf)
            buf = part
    if buf:
        # If the last piece is tiny, fold into previous when possible.
        if chunks and len(buf) < _MIN_CHUNK_CHARS:
            chunks[-1] = f"{chunks[-1]} {buf}".strip()
        else:
            chunks.append(buf)
    return chunks or [cleaned]
