"""Pack validation helpers for Character Studio."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from character_os.loader import load_character, load_world

DRIVE_KEYS = ("curiosity", "trust", "excitement", "fear", "confidence", "energy")


@dataclass
class ValidationReport:
    ok: bool
    kind: str
    pack_id: str
    path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "kind": self.kind,
            "id": self.pack_id,
            "path": self.path,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def validate_character_pack(
    character_id: str,
    *,
    characters_dir: Path,
    worlds_dir: Path,
) -> ValidationReport:
    pack_dir = characters_dir / character_id
    yaml_path = pack_dir / "character.yaml"
    report = ValidationReport(
        ok=True,
        kind="character",
        pack_id=character_id,
        path=str(yaml_path),
    )
    if not yaml_path.is_file():
        report.ok = False
        report.errors.append(f"Missing character.yaml at {yaml_path}")
        return report

    try:
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        report.ok = False
        report.errors.append(f"YAML parse error: {exc}")
        return report

    if not isinstance(data, dict):
        report.ok = False
        report.errors.append("character.yaml root must be a mapping")
        return report

    _check_character_dict(data, character_id, worlds_dir, report)

    # Loader round-trip is the source of truth for engine compatibility.
    try:
        load_character(character_id, characters_dir=characters_dir)
    except (FileNotFoundError, ValueError, KeyError, TypeError, AttributeError) as exc:
        report.ok = False
        report.errors.append(f"Loader rejected pack: {exc}")

    # Prompt override path existence (warning if missing — loader may still accept).
    prompts = data.get("prompts") or {}
    if isinstance(prompts, dict):
        root = characters_dir.parent
        for key, rel in prompts.items():
            path = Path(str(rel))
            if not path.is_absolute():
                path = root / path
            if not path.is_file():
                report.warnings.append(f"Prompt override '{key}' path missing: {rel}")

    report.ok = report.ok and not report.errors
    return report


def validate_world_pack(world_id: str, *, worlds_dir: Path) -> ValidationReport:
    yaml_path = worlds_dir / world_id / "world.yaml"
    report = ValidationReport(
        ok=True,
        kind="world",
        pack_id=world_id,
        path=str(yaml_path),
    )
    if not yaml_path.is_file():
        report.ok = False
        report.errors.append(f"Missing world.yaml at {yaml_path}")
        return report

    try:
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        report.ok = False
        report.errors.append(f"YAML parse error: {exc}")
        return report

    if not isinstance(data, dict):
        report.ok = False
        report.errors.append("world.yaml root must be a mapping")
        return report

    for key in ("id", "name"):
        if not data.get(key):
            report.errors.append(f"Missing required field: {key}")
    if data.get("id") != world_id:
        report.errors.append(
            f"id '{data.get('id')}' does not match folder '{world_id}'"
        )

    try:
        load_world(world_id, worlds_dir=worlds_dir)
    except (FileNotFoundError, ValueError, KeyError, TypeError) as exc:
        report.ok = False
        report.errors.append(f"Loader rejected pack: {exc}")

    report.ok = report.ok and not report.errors
    return report


def _check_character_dict(
    data: dict,
    character_id: str,
    worlds_dir: Path,
    report: ValidationReport,
) -> None:
    for key in ("id", "name", "world", "description", "personality", "goals"):
        if key not in data or data.get(key) in (None, ""):
            report.errors.append(f"Missing required field: {key}")

    if data.get("id") and data.get("id") != character_id:
        report.errors.append(
            f"id '{data.get('id')}' does not match folder '{character_id}'"
        )

    world_id = data.get("world")
    if world_id and not (worlds_dir / str(world_id) / "world.yaml").is_file():
        report.errors.append(f"Referenced world pack not found: {world_id}")

    personality = data.get("personality")
    if personality is not None and not isinstance(personality, dict):
        report.errors.append("personality must be a mapping")

    goals = data.get("goals")
    if goals is not None:
        if not isinstance(goals, list):
            report.errors.append("goals must be a list")
        else:
            for i, goal in enumerate(goals):
                if not isinstance(goal, dict) or not goal.get("id"):
                    report.errors.append(f"goals[{i}] must be a mapping with id")

    drives = data.get("emotional_drives")
    if drives is not None:
        if not isinstance(drives, dict):
            report.errors.append("emotional_drives must be a mapping")
        else:
            for key, value in drives.items():
                if key not in DRIVE_KEYS:
                    report.warnings.append(f"Unknown drive key: {key}")
                    continue
                try:
                    num = float(value)
                except (TypeError, ValueError):
                    report.errors.append(f"Drive {key} must be a number")
                    continue
                if not 0.0 <= num <= 1.0:
                    report.errors.append(f"Drive {key}={num} out of range 0.0–1.0")

    relationships = data.get("relationships")
    if isinstance(relationships, dict):
        for key in ("default_trust", "default_familiarity"):
            if key in relationships:
                try:
                    num = float(relationships[key])
                except (TypeError, ValueError):
                    report.errors.append(f"relationships.{key} must be a number")
                    continue
                if not 0.0 <= num <= 1.0:
                    report.errors.append(
                        f"relationships.{key}={num} out of range 0.0–1.0"
                    )
