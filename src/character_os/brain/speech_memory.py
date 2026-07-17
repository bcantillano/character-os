"""Helpers for surfacing long-term memory in spoken dialogue prompts."""

from __future__ import annotations

import re

from character_os.brain.memory import MemoryFact, MemoryStore, extract_name

_RECALL_RE = re.compile(
    r"\b(remember|recall|my name|who am i|what('?s| is) my name)\b",
    re.IGNORECASE,
)


def extract_known_name(facts: list[MemoryFact]) -> str | None:
    for fact in facts:
        name = extract_name(fact.content)
        if name:
            return name
    return None


def user_asks_about_memory(message: str) -> bool:
    return bool(_RECALL_RE.search(message or ""))


def format_speech_memory_context(store: MemoryStore, *, user_message: str = "") -> str:
    """Build a speech-oriented memory block that is hard to ignore."""
    facts = store.all()[:8]
    if not facts:
        return "(no long-term memories yet)"

    known_name = extract_known_name(facts)
    lines: list[str] = [
        "Known facts about this person (you already know these — use them when relevant):",
    ]
    if known_name:
        lines.append(f"- Their name is {known_name}. Address or acknowledge them by name when natural.")
    for fact in facts:
        lines.append(f"- {fact.content}")

    if user_asks_about_memory(user_message):
        lines.append("")
        lines.append(
            "The user is asking what you remember. Answer using the facts above. "
            "Do not claim you forgot a listed name or preference."
        )
        if known_name:
            lines.append(f"If asked for their name, say {known_name}.")

    return "\n".join(lines)
