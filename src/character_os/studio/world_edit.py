"""World pack scaffold and in-place edits with validate-before-commit."""

from __future__ import annotations

from pathlib import Path

import yaml

from character_os.studio.validate import validate_world_pack


def read_world_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"world.yaml root must be a mapping: {path}")
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def create_world_pack(
    world_id: str,
    *,
    worlds_dir: Path,
    name: str,
    description: str | None = None,
    era: str = "",
    tone: str = "",
    force: bool = False,
) -> Path:
    if not world_id or "/" in world_id or "\\" in world_id:
        raise ValueError(f"Invalid world id: {world_id!r}")
    pack_dir = worlds_dir / world_id
    yaml_path = pack_dir / "world.yaml"
    if yaml_path.exists() and not force:
        raise FileExistsError(f"World pack already exists: {pack_dir}")

    knowledge_dir = pack_dir / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    general_path = knowledge_dir / "general.yaml"
    if not general_path.exists() or force:
        write_yaml(
            general_path,
            {
                "entries": [
                    {
                        "id": f"{world_id}_overview",
                        "topic": "general",
                        "summary": f"Overview notes for {name}.",
                        "details": "",
                    }
                ]
            },
        )

    payload = {
        "id": world_id,
        "name": name,
        "description": (description or f"{name} — a Character OS world pack.").strip(),
        "era": era,
        "tone": tone,
        "rules": [
            "Stay consistent with established lore.",
            "Do not invent private facts the characters were not told.",
        ],
        "knowledge_files": ["knowledge/general.yaml"],
    }
    write_yaml(yaml_path, payload)
    return pack_dir


def apply_world_edits(
    data: dict,
    *,
    name: str | None = None,
    description: str | None = None,
    era: str | None = None,
    tone: str | None = None,
    add_rules: list[str] | None = None,
    remove_rules: list[str] | None = None,
) -> dict:
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if era is not None:
        data["era"] = era
    if tone is not None:
        data["tone"] = tone

    if add_rules or remove_rules:
        rules = list(data.get("rules") or [])
        if add_rules:
            for rule in add_rules:
                if rule not in rules:
                    rules.append(rule)
        if remove_rules:
            remove = set(remove_rules)
            rules = [r for r in rules if r not in remove]
        data["rules"] = rules
    return data


def save_world_edits(world_id: str, data: dict, *, worlds_dir: Path) -> Path:
    yaml_path = worlds_dir / world_id / "world.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Missing world.yaml: {yaml_path}")
    backup = yaml_path.with_suffix(".yaml.bak")
    original = yaml_path.read_text(encoding="utf-8")
    backup.write_text(original, encoding="utf-8")
    try:
        write_yaml(yaml_path, data)
        report = validate_world_pack(world_id, worlds_dir=worlds_dir)
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


def add_knowledge_entry(
    world_id: str,
    *,
    worlds_dir: Path,
    entry_id: str,
    summary: str,
    topic: str = "general",
    details: str = "",
    knowledge_file: str = "knowledge/general.yaml",
) -> Path:
    """Append a knowledge entry; create the knowledge file if needed."""
    pack_dir = worlds_dir / world_id
    world_path = pack_dir / "world.yaml"
    if not world_path.is_file():
        raise FileNotFoundError(f"Missing world.yaml: {world_path}")

    data = read_world_yaml(world_path)
    files = list(data.get("knowledge_files") or [])
    if knowledge_file not in files:
        files.append(knowledge_file)
        data["knowledge_files"] = files
        save_world_edits(world_id, data, worlds_dir=worlds_dir)

    kpath = pack_dir / knowledge_file
    if kpath.is_file():
        with kpath.open(encoding="utf-8") as f:
            kdata = yaml.safe_load(f) or {}
    else:
        kdata = {"entries": []}
    if not isinstance(kdata, dict):
        raise ValueError(f"Knowledge file root must be a mapping: {kpath}")
    entries = kdata.setdefault("entries", [])
    if not isinstance(entries, list):
        raise ValueError("knowledge entries must be a list")
    if any(isinstance(e, dict) and e.get("id") == entry_id for e in entries):
        raise ValueError(f"Knowledge entry already exists: {entry_id}")
    entries.append(
        {
            "id": entry_id,
            "topic": topic,
            "summary": summary,
            "details": details,
        }
    )
    write_yaml(kpath, kdata)
    report = validate_world_pack(world_id, worlds_dir=worlds_dir)
    if not report.ok:
        raise ValueError(
            "Knowledge add left pack invalid:\n"
            + "\n".join(f"- {e}" for e in report.errors)
        )
    return kpath
