"""Long-term memory fact store (in-process cache synced to SQLite)."""

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
        self._dirty_ids: set[str] = set()

    def add(self, fact: MemoryFact, *, dirty: bool = True) -> None:
        self._facts[fact.id] = fact
        if dirty:
            self._dirty_ids.add(fact.id)

    def mark_dirty(self, fact_id: str) -> None:
        if fact_id in self._facts:
            self._dirty_ids.add(fact_id)

    def find_similar(self, content: str) -> MemoryFact | None:
        needle = _normalize(content)
        for fact in self._facts.values():
            if _normalize(fact.content) == needle:
                return fact
        return None

    def all(self) -> list[MemoryFact]:
        return sorted(self._facts.values(), key=lambda f: -f.importance)

    def dirty_facts(self) -> list[MemoryFact]:
        return [self._facts[fid] for fid in self._dirty_ids if fid in self._facts]

    def clear_dirty(self) -> None:
        self._dirty_ids.clear()

    def decay_importance(self, amount: float = 0.01) -> None:
        for fact in self._facts.values():
            before = fact.importance
            fact.importance = max(0.0, fact.importance - amount)
            if fact.importance != before:
                self._dirty_ids.add(fact.id)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())
