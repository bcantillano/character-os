"""Long-term memory fact store (in-process cache synced to SQLite)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_NAME_RE = re.compile(
    r"(?:the user's name is|user'?s name is|name is|name:)\s+([A-Za-z][\w'-]*)",
    re.IGNORECASE,
)


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

    def remove(self, fact_id: str) -> None:
        self._facts.pop(fact_id, None)
        self._dirty_ids.discard(fact_id)

    def mark_dirty(self, fact_id: str) -> None:
        if fact_id in self._facts:
            self._dirty_ids.add(fact_id)

    def find_similar(self, content: str) -> MemoryFact | None:
        """Find an existing fact that is the same (or near-duplicate) of content."""
        needle = canonicalize_fact_content(content)
        needle_key = memory_key(needle)
        needle_norm = _normalize(needle)

        for fact in self._facts.values():
            if memory_key(fact.content) == needle_key:
                return fact

        for fact in self._facts.values():
            other = _normalize(canonicalize_fact_content(fact.content))
            if _near_duplicate_text(needle_norm, other):
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

    def dedupe(self) -> list[str]:
        """Collapse near-duplicate facts in place. Returns removed fact ids."""
        if len(self._facts) < 2:
            # Still canonicalize a lone name fact if needed.
            for fact in list(self._facts.values()):
                if _canonicalize_in_place(fact):
                    self._dirty_ids.add(fact.id)
            return []

        groups: dict[str, list[MemoryFact]] = {}
        for fact in self._facts.values():
            groups.setdefault(memory_key(fact.content), []).append(fact)

        removed: list[str] = []
        keepers: list[MemoryFact] = []
        for key, group in groups.items():
            keeper = _pick_keeper(group)
            if _merge_group_into_keeper(keeper, group, key=key):
                self._dirty_ids.add(keeper.id)
            for fact in group:
                if fact.id != keeper.id:
                    removed.append(fact.id)
            keepers.append(keeper)

        keepers, more_removed = _collapse_containment(keepers)
        for fact_id in more_removed:
            removed.append(fact_id)

        dirty = {fid for fid in self._dirty_ids if fid not in set(removed)}
        for fact in keepers:
            if getattr(fact, "_dedupe_changed", False):
                dirty.add(fact.id)
                delattr(fact, "_dedupe_changed")

        self._facts = {f.id: f for f in keepers}
        self._dirty_ids = dirty
        return removed


def canonicalize_fact_content(fact: str) -> str:
    """Normalize common fact labels into clear declarative form."""
    text = fact.strip()
    if not text:
        return text
    lowered = text.lower()
    if lowered.startswith("name:"):
        name = text.split(":", 1)[1].strip()
        return f"The user's name is {name}" if name else text
    if lowered.startswith("preference:") or lowered.startswith("prefers:"):
        rest = text.split(":", 1)[1].strip()
        if rest.lower().startswith("the user"):
            return rest
        if rest.lower().startswith("prefers "):
            return f"The user {rest}"
        return f"The user prefers {rest}"
    if re.match(r"^prefers\s+", lowered):
        return f"The user {text}"
    if lowered.startswith("preference for"):
        return f"The user has a {text}"

    name = extract_name(text)
    if name and (
        lowered.startswith("the user's name is")
        or lowered.startswith("user's name is")
        or lowered.startswith("name is ")
    ):
        return f"The user's name is {name}"
    return text


def extract_name(content: str) -> str | None:
    match = _NAME_RE.search(content or "")
    return match.group(1) if match else None


def memory_key(content: str) -> str:
    """Semantic fingerprint used to group duplicate facts."""
    canon = canonicalize_fact_content(content)
    name = extract_name(canon)
    if name:
        return f"name:{name.lower()}"
    norm = _normalize(canon)
    for prefix in (
        "the user prefers ",
        "the user has a preference for ",
        "user prefers ",
        "prefers ",
    ):
        if norm.startswith(prefix):
            return f"pref:{norm[len(prefix):]}"
    if norm.startswith("the user "):
        return f"user:{norm[len('the user '):]}"
    return f"fact:{norm}"


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _near_duplicate_text(a: str, b: str) -> bool:
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= 12 and shorter in longer:
        return True
    return False


def _pick_keeper(group: list[MemoryFact]) -> MemoryFact:
    return max(
        group,
        key=lambda f: (f.importance, len(canonicalize_fact_content(f.content)), f.id),
    )


def _canonicalize_in_place(fact: MemoryFact) -> bool:
    canon = canonicalize_fact_content(fact.content)
    if canon != fact.content:
        fact.content = canon
        return True
    return False


def _merge_group_into_keeper(keeper: MemoryFact, group: list[MemoryFact], *, key: str) -> bool:
    before = (keeper.content, keeper.importance, tuple(keeper.tags))
    for fact in group:
        keeper.importance = max(keeper.importance, fact.importance)
        for tag in fact.tags:
            if tag not in keeper.tags:
                keeper.tags.append(tag)
        cand = canonicalize_fact_content(fact.content)
        if len(cand) >= len(keeper.content):
            keeper.content = cand
    if key.startswith("name:"):
        name = extract_name(keeper.content)
        if name:
            keeper.content = f"The user's name is {name}"
    else:
        keeper.content = canonicalize_fact_content(keeper.content)
    after = (keeper.content, keeper.importance, tuple(keeper.tags))
    return after != before


def _collapse_containment(facts: list[MemoryFact]) -> tuple[list[MemoryFact], list[str]]:
    """Merge facts where one normalized content contains the other."""
    remaining = list(facts)
    removed: list[str] = []

    while True:
        pair: tuple[int, int] | None = None
        for i in range(len(remaining)):
            for j in range(i + 1, len(remaining)):
                a, b = remaining[i], remaining[j]
                key_a, key_b = memory_key(a.content), memory_key(b.content)
                if key_a.startswith("name:") and key_b.startswith("name:") and key_a != key_b:
                    continue
                na = _normalize(canonicalize_fact_content(a.content))
                nb = _normalize(canonicalize_fact_content(b.content))
                if _near_duplicate_text(na, nb):
                    pair = (i, j)
                    break
            if pair is not None:
                break
        if pair is None:
            break

        i, j = pair
        a, b = remaining[i], remaining[j]
        na = _normalize(canonicalize_fact_content(a.content))
        nb = _normalize(canonicalize_fact_content(b.content))
        if (len(nb), b.importance, b.id) > (len(na), a.importance, a.id):
            winner, loser = b, a
        else:
            winner, loser = a, b

        winner.importance = max(winner.importance, loser.importance)
        for tag in loser.tags:
            if tag not in winner.tags:
                winner.tags.append(tag)
        winner._dedupe_changed = True  # type: ignore[attr-defined]
        removed.append(loser.id)
        remaining = [f for f in remaining if f.id != loser.id]

    return remaining, removed
