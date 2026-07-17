"""Load character.yaml packs into CharacterDefinition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from character_os.core.types import (
    CharacterDefinition,
    EmotionalDrives,
    Goal,
    KnowledgeEntry,
    Personality,
)
from character_os.loader.paths import default_characters_dir


def _drives_from_dict(raw: dict[str, Any] | None) -> EmotionalDrives:
    raw = raw or {}
    return EmotionalDrives(
        curiosity=float(raw.get("curiosity", 0.5)),
        trust=float(raw.get("trust", 0.5)),
        excitement=float(raw.get("excitement", 0.5)),
        fear=float(raw.get("fear", 0.5)),
        confidence=float(raw.get("confidence", 0.5)),
        energy=float(raw.get("energy", 0.5)),
    ).clamp()


def _knowledge_entries(raw: dict[str, Any] | None) -> list[KnowledgeEntry]:
    if not raw:
        return []
    entries = raw.get("entries", raw if isinstance(raw, list) else [])
    result: list[KnowledgeEntry] = []
    for item in entries:
        result.append(
            KnowledgeEntry(
                id=item["id"],
                topic=item.get("topic", "general"),
                summary=item.get("summary", ""),
                details=item.get("details", "") or "",
            )
        )
    return result


def load_character(
    character_id: str,
    characters_dir: Path | None = None,
) -> CharacterDefinition:
    base = characters_dir or default_characters_dir()
    path = base / character_id / "character.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Character pack not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if data.get("id") != character_id:
        raise ValueError(
            f"character.yaml id '{data.get('id')}' does not match folder '{character_id}'"
        )

    personality_raw = data.get("personality") or {}
    relationships = data.get("relationships") or {}

    return CharacterDefinition(
        id=data["id"],
        name=data["name"],
        world=data["world"],
        description=(data.get("description") or "").strip(),
        personality=Personality(
            traits=list(personality_raw.get("traits") or []),
            voice=dict(personality_raw.get("voice") or {}),
            fears=list(personality_raw.get("fears") or []),
            preferences=list(personality_raw.get("preferences") or []),
        ),
        goals=[
            Goal(
                id=g["id"],
                description=g.get("description", ""),
                priority=g.get("priority", "medium"),
                status=g.get("status", "active"),
            )
            for g in (data.get("goals") or [])
        ],
        emotional_drives=_drives_from_dict(data.get("emotional_drives")),
        knowledge=_knowledge_entries(data.get("knowledge")),
        default_trust=float(relationships.get("default_trust", 0.2)),
        default_familiarity=float(relationships.get("default_familiarity", 0.0)),
        assets=dict(data.get("assets") or {}),
        prompts=dict(data.get("prompts") or {}),
    )
