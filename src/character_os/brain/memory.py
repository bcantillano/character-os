"""In-memory long-term memory placeholder (SQLite persistence comes next)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryFact:
    id: str
    content: str
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)


class MemoryStore:
    """In-process fact cache loaded from / synced to persistence."""

    def __init__(self) -> None:
        self._facts: dict[str, MemoryFact] = {}

    def add(self, fact: MemoryFact) -> None:
        self._facts[fact.id] = fact

    def find_similar(self, content: str) -> MemoryFact | None:
        needle = _normalize(content)
        for fact in self._facts.values():
            if _normalize(fact.content) == needle:
                return fact
        return None

    def all(self) -> list[MemoryFact]:
        return sorted(self._facts.values(), key=lambda f: -f.importance)

    def decay_importance(self, amount: float = 0.01) -> None:
        for fact in self._facts.values():
            fact.importance = max(0.0, fact.importance - amount)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())
