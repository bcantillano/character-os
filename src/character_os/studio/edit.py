"""In-place character.yaml edits with validate-before-commit."""

from __future__ import annotations

from pathlib import Path

import yaml

from character_os.studio.validate import DRIVE_KEYS, validate_character_pack


def read_character_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"character.yaml root must be a mapping: {path}")
    return data


def write_character_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def apply_character_edits(
    data: dict,
    *,
    name: str | None = None,
    description: str | None = None,
    world_id: str | None = None,
    add_traits: list[str] | None = None,
    remove_traits: list[str] | None = None,
    add_fears: list[str] | None = None,
    remove_fears: list[str] | None = None,
    add_preferences: list[str] | None = None,
    remove_preferences: list[str] | None = None,
    drives: dict[str, float] | None = None,
    voice_tone: str | None = None,
    add_quirks: list[str] | None = None,
    remove_quirks: list[str] | None = None,
    default_trust: float | None = None,
    default_familiarity: float | None = None,
    add_goal: tuple[str, str] | None = None,
    remove_goal_id: str | None = None,
    goal_priority: dict[str, str] | None = None,
    goal_status: dict[str, str] | None = None,
    goal_description: dict[str, str] | None = None,
) -> dict:
    """Mutate a character.yaml mapping in place and return it."""
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if world_id is not None:
        data["world"] = world_id

    personality = data.setdefault("personality", {})
    if not isinstance(personality, dict):
        raise ValueError("personality must be a mapping")

    def _edit_list(key: str, add: list[str] | None, remove: list[str] | None) -> None:
        if not add and not remove:
            return
        items = list(personality.get(key) or [])
        if add:
            for item in add:
                if item not in items:
                    items.append(item)
        if remove:
            drop = set(remove)
            items = [x for x in items if x not in drop]
        personality[key] = items

    _edit_list("traits", add_traits, remove_traits)
    _edit_list("fears", add_fears, remove_fears)
    _edit_list("preferences", add_preferences, remove_preferences)

    voice = personality.setdefault("voice", {})
    if not isinstance(voice, dict):
        raise ValueError("personality.voice must be a mapping")
    if voice_tone is not None:
        voice["tone"] = voice_tone
    if add_quirks or remove_quirks:
        quirks = list(voice.get("quirks") or [])
        if add_quirks:
            for quirk in add_quirks:
                if quirk not in quirks:
                    quirks.append(quirk)
        if remove_quirks:
            remove = set(remove_quirks)
            quirks = [q for q in quirks if q not in remove]
        voice["quirks"] = quirks

    if drives:
        block = data.setdefault("emotional_drives", {})
        if not isinstance(block, dict):
            raise ValueError("emotional_drives must be a mapping")
        for key, value in drives.items():
            if key not in DRIVE_KEYS:
                raise ValueError(f"Unknown drive key: {key}")
            num = float(value)
            if not 0.0 <= num <= 1.0:
                raise ValueError(f"Drive {key}={num} out of range 0.0–1.0")
            block[key] = num

    if default_trust is not None or default_familiarity is not None:
        rel = data.setdefault("relationships", {})
        if not isinstance(rel, dict):
            raise ValueError("relationships must be a mapping")
        if default_trust is not None:
            num = float(default_trust)
            if not 0.0 <= num <= 1.0:
                raise ValueError(f"default_trust={num} out of range 0.0–1.0")
            rel["default_trust"] = num
        if default_familiarity is not None:
            num = float(default_familiarity)
            if not 0.0 <= num <= 1.0:
                raise ValueError(f"default_familiarity={num} out of range 0.0–1.0")
            rel["default_familiarity"] = num

    if add_goal is not None:
        goal_id, goal_desc = add_goal
        goals = data.setdefault("goals", [])
        if not isinstance(goals, list):
            raise ValueError("goals must be a list")
        if any(isinstance(g, dict) and g.get("id") == goal_id for g in goals):
            raise ValueError(f"Goal already exists: {goal_id}")
        goals.append(
            {
                "id": goal_id,
                "description": goal_desc,
                "priority": "medium",
                "status": "active",
            }
        )

    if remove_goal_id is not None:
        goals = data.get("goals") or []
        if not isinstance(goals, list):
            raise ValueError("goals must be a list")
        new_goals = [
            g for g in goals if not (isinstance(g, dict) and g.get("id") == remove_goal_id)
        ]
        if len(new_goals) == len(goals):
            raise ValueError(f"Goal not found: {remove_goal_id}")
        data["goals"] = new_goals

    if goal_priority or goal_status or goal_description:
        goals = data.get("goals") or []
        if not isinstance(goals, list):
            raise ValueError("goals must be a list")
        by_id = {g.get("id"): g for g in goals if isinstance(g, dict) and g.get("id")}
        for gid, priority in (goal_priority or {}).items():
            if gid not in by_id:
                raise ValueError(f"Goal not found: {gid}")
            if priority not in {"high", "medium", "low"}:
                raise ValueError(f"Invalid goal priority: {priority}")
            by_id[gid]["priority"] = priority
        for gid, status in (goal_status or {}).items():
            if gid not in by_id:
                raise ValueError(f"Goal not found: {gid}")
            if status not in {"active", "paused", "completed", "failed"}:
                raise ValueError(f"Invalid goal status: {status}")
            by_id[gid]["status"] = status
        for gid, desc in (goal_description or {}).items():
            if gid not in by_id:
                raise ValueError(f"Goal not found: {gid}")
            by_id[gid]["description"] = desc

    return data


def save_character_edits(
    character_id: str,
    data: dict,
    *,
    characters_dir: Path,
    worlds_dir: Path,
) -> Path:
    """Write character.yaml with backup; roll back if validation fails."""
    yaml_path = characters_dir / character_id / "character.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Missing character.yaml: {yaml_path}")

    backup = yaml_path.with_suffix(".yaml.bak")
    original = yaml_path.read_text(encoding="utf-8")
    backup.write_text(original, encoding="utf-8")

    try:
        write_character_yaml(yaml_path, data)
        report = validate_character_pack(
            character_id,
            characters_dir=characters_dir,
            worlds_dir=worlds_dir,
        )
        if not report.ok:
            yaml_path.write_text(original, encoding="utf-8")
            raise ValueError(
                "Edit rejected by validation:\n"
                + "\n".join(f"- {e}" for e in report.errors)
            )
    except Exception:
        if backup.is_file():
            yaml_path.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        raise

    return yaml_path
