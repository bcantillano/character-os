"""Load world.yaml packs and knowledge files."""

from __future__ import annotations

from pathlib import Path

import yaml

from character_os.core.types import KnowledgeEntry, WorldDefinition
from character_os.loader.paths import default_worlds_dir


def _load_knowledge_file(path: Path) -> list[KnowledgeEntry]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    entries = data.get("entries") or []
    return [
        KnowledgeEntry(
            id=item["id"],
            topic=item.get("topic", "general"),
            summary=item.get("summary", ""),
            details=item.get("details", "") or "",
        )
        for item in entries
    ]


def load_world(world_id: str, worlds_dir: Path | None = None) -> WorldDefinition:
    base = worlds_dir or default_worlds_dir()
    world_path = base / world_id / "world.yaml"
    if not world_path.is_file():
        raise FileNotFoundError(f"World pack not found: {world_path}")

    with world_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if data.get("id") != world_id:
        raise ValueError(
            f"world.yaml id '{data.get('id')}' does not match folder '{world_id}'"
        )

    knowledge: list[KnowledgeEntry] = []
    for relative in data.get("knowledge_files") or []:
        kpath = (base / world_id / relative).resolve()
        if not kpath.is_file():
            raise FileNotFoundError(f"Knowledge file missing: {kpath}")
        knowledge.extend(_load_knowledge_file(kpath))

    return WorldDefinition(
        id=data["id"],
        name=data["name"],
        description=(data.get("description") or "").strip(),
        era=data.get("era") or "",
        tone=data.get("tone") or "",
        rules=list(data.get("rules") or []),
        knowledge=knowledge,
    )
