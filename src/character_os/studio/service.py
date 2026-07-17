"""Studio operations atop loader/ and persistence/ (no event-bus chat)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from character_os.loader import load_character, load_world
from character_os.loader.paths import (
    default_characters_dir,
    default_data_dir,
    default_worlds_dir,
    find_repo_root,
)
from character_os.persistence import CharacterPersistence


@dataclass(frozen=True)
class PackSummary:
    id: str
    name: str
    path: str


@dataclass(frozen=True)
class CharacterDetail:
    id: str
    name: str
    world: str
    description: str
    traits: list[str]
    goals: list[dict[str, str]]
    drives: dict[str, float]
    trust_default: float
    familiarity_default: float
    tts_voice: str
    prompt_overrides: list[str]
    knowledge_count: int


@dataclass(frozen=True)
class RuntimeSnapshot:
    character_id: str
    trust: float
    familiarity: float
    drives: dict[str, float]
    active_memories: list[dict[str, object]]
    archived_memories: list[dict[str, object]]
    db_path: str


class StudioService:
    """Read/inspect content packs and persisted character state."""

    def __init__(self, root: Path | None = None, data_dir: Path | None = None) -> None:
        self.root = root or find_repo_root()
        self.characters_dir = default_characters_dir(self.root)
        self.worlds_dir = default_worlds_dir(self.root)
        self.data_dir = data_dir or default_data_dir(self.root)

    def list_characters(self) -> list[PackSummary]:
        results: list[PackSummary] = []
        if not self.characters_dir.is_dir():
            return results
        for path in sorted(self.characters_dir.iterdir()):
            yaml_path = path / "character.yaml"
            if not path.is_dir() or not yaml_path.is_file():
                continue
            with yaml_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            results.append(
                PackSummary(
                    id=str(data.get("id") or path.name),
                    name=str(data.get("name") or path.name),
                    path=str(path.relative_to(self.root)),
                )
            )
        return results

    def list_worlds(self) -> list[PackSummary]:
        results: list[PackSummary] = []
        if not self.worlds_dir.is_dir():
            return results
        for path in sorted(self.worlds_dir.iterdir()):
            yaml_path = path / "world.yaml"
            if not path.is_dir() or not yaml_path.is_file():
                continue
            with yaml_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            results.append(
                PackSummary(
                    id=str(data.get("id") or path.name),
                    name=str(data.get("name") or path.name),
                    path=str(path.relative_to(self.root)),
                )
            )
        return results

    def show_character(self, character_id: str) -> CharacterDetail:
        character = load_character(character_id, characters_dir=self.characters_dir)
        return CharacterDetail(
            id=character.id,
            name=character.name,
            world=character.world,
            description=character.description.strip(),
            traits=list(character.personality.traits),
            goals=[
                {
                    "id": g.id,
                    "priority": g.priority,
                    "status": g.status,
                    "description": g.description,
                }
                for g in character.goals
            ],
            drives=character.emotional_drives.as_dict(),
            trust_default=character.default_trust,
            familiarity_default=character.default_familiarity,
            tts_voice=character.tts.voice,
            prompt_overrides=sorted(character.prompts.keys()),
            knowledge_count=len(character.knowledge),
        )

    def show_world(self, world_id: str) -> dict[str, object]:
        world = load_world(world_id, worlds_dir=self.worlds_dir)
        return {
            "id": world.id,
            "name": world.name,
            "description": world.description.strip(),
            "knowledge_count": len(world.knowledge),
            "knowledge_ids": [e.id for e in world.knowledge],
        }

    def inspect_runtime(self, character_id: str, *, include_archived: bool = True) -> RuntimeSnapshot:
        # Validate pack exists before opening DB.
        character = load_character(character_id, characters_dir=self.characters_dir)
        persistence = CharacterPersistence(character_id, data_dir=self.data_dir)
        store = persistence.load_memory_store()
        drives = persistence.load_drives(character.emotional_drives)
        rel = persistence.load_relationship(
            character.default_trust,
            character.default_familiarity,
        )
        archived = persistence.list_archived_memories() if include_archived else []
        return RuntimeSnapshot(
            character_id=character_id,
            trust=rel.trust,
            familiarity=rel.familiarity,
            drives=drives.as_dict(),
            active_memories=[
                {
                    "id": f.id,
                    "importance": round(f.importance, 3),
                    "content": f.content,
                    "tags": list(f.tags),
                }
                for f in store.all()
            ],
            archived_memories=[
                {
                    "id": f.id,
                    "importance": round(f.importance, 3),
                    "content": f.content,
                    "tags": list(f.tags),
                }
                for f in archived
            ],
            db_path=str(persistence.db.path),
        )

    def create_character(
        self,
        character_id: str,
        *,
        name: str,
        world_id: str,
        description: str | None = None,
        force: bool = False,
    ) -> Path:
        """Scaffold a minimal character pack. Does not overwrite unless force=True."""
        if not character_id or "/" in character_id or "\\" in character_id:
            raise ValueError(f"Invalid character id: {character_id!r}")
        # Ensure world exists.
        load_world(world_id, worlds_dir=self.worlds_dir)

        pack_dir = self.characters_dir / character_id
        yaml_path = pack_dir / "character.yaml"
        if yaml_path.exists() and not force:
            raise FileExistsError(f"Character pack already exists: {pack_dir}")

        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "assets").mkdir(exist_ok=True)
        gitkeep = pack_dir / "assets" / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")

        desc = (description or f"{name} — a Character OS pack scaffold.").strip()
        payload = {
            "id": character_id,
            "name": name,
            "world": world_id,
            "description": desc,
            "personality": {
                "traits": ["curious"],
                "voice": {"tone": "clear and natural", "quirks": []},
                "fears": [],
                "preferences": [],
            },
            "emotional_drives": {
                "curiosity": 0.55,
                "trust": 0.4,
                "excitement": 0.4,
                "fear": 0.3,
                "confidence": 0.5,
                "energy": 0.5,
            },
            "goals": [
                {
                    "id": "understand_person",
                    "description": "Understand the person speaking over time",
                    "priority": "high",
                    "status": "active",
                }
            ],
            "relationships": {
                "default_trust": 0.4,
                "default_familiarity": 0.0,
            },
            "assets": {"portrait": "assets/portrait.png"},
        }
        with yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
        return pack_dir
