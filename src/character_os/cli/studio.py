"""Phase 2 Character Studio CLI — inspect, validate, edit, debug, and serve packs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from character_os.studio.service import StudioService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="character-os-studio",
        description=(
            "Character Studio (Phase 2) — list/show/validate/edit packs, "
            "inspect memories, stage-debug, optional web UI"
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Runtime data dir for SQLite (default: <root>/data)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List content packs")
    list_p.add_argument("kind", choices=["characters", "worlds"])

    show_p = sub.add_parser("show", help="Show a character or world pack")
    show_p.add_argument("kind", choices=["character", "world"])
    show_p.add_argument("id")

    val_p = sub.add_parser("validate", help="Validate a character or world pack")
    val_p.add_argument("kind", choices=["character", "world"])
    val_p.add_argument("id")

    set_p = sub.add_parser(
        "set",
        help="Edit character.yaml or world.yaml in place (rewrites YAML; keeps .bak)",
    )
    set_p.add_argument("kind", choices=["character", "world"])
    set_p.add_argument("id")
    # Character fields
    set_p.add_argument("--name")
    set_p.add_argument("--description")
    set_p.add_argument("--world", dest="world_id")
    set_p.add_argument("--add-trait", action="append", default=[])
    set_p.add_argument("--remove-trait", action="append", default=[])
    set_p.add_argument("--add-fear", action="append", default=[])
    set_p.add_argument("--remove-fear", action="append", default=[])
    set_p.add_argument("--add-preference", action="append", default=[])
    set_p.add_argument("--remove-preference", action="append", default=[])
    set_p.add_argument(
        "--drive",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Set emotional drive (repeatable), e.g. curiosity=0.7",
    )
    set_p.add_argument("--voice-tone")
    set_p.add_argument("--add-quirk", action="append", default=[])
    set_p.add_argument("--remove-quirk", action="append", default=[])
    set_p.add_argument("--default-trust", type=float)
    set_p.add_argument("--default-familiarity", type=float)
    set_p.add_argument(
        "--add-goal",
        metavar="ID:DESCRIPTION",
        help="Add a goal as id:description",
    )
    set_p.add_argument("--remove-goal", dest="remove_goal_id")
    set_p.add_argument(
        "--goal-priority",
        action="append",
        default=[],
        metavar="ID=PRIORITY",
        help="Set goal priority (high|medium|low), e.g. scout=high",
    )
    set_p.add_argument(
        "--goal-status",
        action="append",
        default=[],
        metavar="ID=STATUS",
        help="Set goal status (active|paused|completed|failed)",
    )
    set_p.add_argument(
        "--goal-description",
        action="append",
        default=[],
        metavar="ID:DESCRIPTION",
        help="Rewrite a goal description as id:new text",
    )
    # World fields
    set_p.add_argument("--era")
    set_p.add_argument("--tone")
    set_p.add_argument("--add-rule", action="append", default=[])
    set_p.add_argument("--remove-rule", action="append", default=[])

    mem_p = sub.add_parser("memories", help="Inspect persisted memories/drives for a character")
    mem_p.add_argument("character_id")
    mem_p.add_argument(
        "--no-archived",
        action="store_true",
        help="Omit archived memories",
    )

    create_p = sub.add_parser("create-character", help="Scaffold a minimal character pack")
    create_p.add_argument("character_id")
    create_p.add_argument("--name", required=True)
    create_p.add_argument("--world", required=True, dest="world_id")
    create_p.add_argument("--description", default=None)
    create_p.add_argument("--force", action="store_true")

    create_w = sub.add_parser("create-world", help="Scaffold a minimal world pack")
    create_w.add_argument("world_id")
    create_w.add_argument("--name", required=True)
    create_w.add_argument("--description", default=None)
    create_w.add_argument("--era", default="")
    create_w.add_argument("--tone", default="")
    create_w.add_argument("--force", action="store_true")

    know_p = sub.add_parser("add-knowledge", help="Append a knowledge entry to a world pack")
    know_p.add_argument("world_id")
    know_p.add_argument("--id", required=True, dest="entry_id")
    know_p.add_argument("--summary", required=True)
    know_p.add_argument("--topic", default="general")
    know_p.add_argument("--details", default="")
    know_p.add_argument(
        "--file",
        default="knowledge/general.yaml",
        dest="knowledge_file",
        help="Knowledge YAML relative to the world pack (default: knowledge/general.yaml)",
    )

    trace_p = sub.add_parser(
        "trace",
        help="Run one message through the lifecycle and print stage lines",
    )
    trace_p.add_argument("character_id")
    trace_p.add_argument("message")
    trace_p.add_argument(
        "--provider",
        default="stub",
        choices=["stub", "openai"],
        help="LLM provider for the trace (default: stub)",
    )
    trace_p.add_argument(
        "--persist",
        action="store_true",
        help="Persist memories from the trace (default: ephemeral)",
    )

    serve_p = sub.add_parser("serve", help="Optional stdlib web UI for Studio")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    studio = StudioService(root=args.root, data_dir=args.data_dir)

    try:
        if args.command == "list":
            rows = studio.list_characters() if args.kind == "characters" else studio.list_worlds()
            payload = [r.__dict__ for r in rows]
            return _emit(payload, as_json=args.json, human=_format_pack_list)

        if args.command == "show":
            if args.kind == "character":
                detail = studio.show_character(args.id)
                return _emit(detail.__dict__, as_json=args.json, human=_format_character)
            world = studio.show_world(args.id)
            return _emit(world, as_json=args.json, human=_format_world)

        if args.command == "validate":
            report = (
                studio.validate_character(args.id)
                if args.kind == "character"
                else studio.validate_world(args.id)
            )
            if args.json:
                print(json.dumps(report.as_dict(), indent=2))
            else:
                print(_format_validation(report.as_dict()))
            return 0 if report.ok else 2

        if args.command == "set":
            if args.kind == "character":
                return _cmd_set_character(studio, args)
            return _cmd_set_world(studio, args)

        if args.command == "memories":
            snap = studio.inspect_runtime(
                args.character_id,
                include_archived=not args.no_archived,
            )
            return _emit(snap.__dict__, as_json=args.json, human=_format_runtime)

        if args.command == "create-character":
            path = studio.create_character(
                args.character_id,
                name=args.name,
                world_id=args.world_id,
                description=args.description,
                force=args.force,
            )
            payload = {"created": str(path), "id": args.character_id}
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"Created character pack: {path}")
                print(
                    f"Edit {path / 'character.yaml'} then chat with: "
                    f"character-os --character {args.character_id}"
                )
            return 0

        if args.command == "create-world":
            path = studio.create_world(
                args.world_id,
                name=args.name,
                description=args.description,
                era=args.era,
                tone=args.tone,
                force=args.force,
            )
            payload = {"created": str(path), "id": args.world_id}
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"Created world pack: {path}")
                print(f"Add lore with: character-os-studio add-knowledge {args.world_id} ...")
            return 0

        if args.command == "add-knowledge":
            path = studio.add_world_knowledge(
                args.world_id,
                entry_id=args.entry_id,
                summary=args.summary,
                topic=args.topic,
                details=args.details,
                knowledge_file=args.knowledge_file,
            )
            payload = {"updated": str(path), "id": args.entry_id, "world": args.world_id}
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(f"Added knowledge entry {args.entry_id!r} → {path}")
            return 0

        if args.command == "trace":
            result = studio.stage_trace(
                args.character_id,
                args.message,
                provider_name=args.provider,
                persist=args.persist,
            )
            if args.json:
                print(json.dumps(result.as_dict(), indent=2))
            else:
                print(_format_trace(result.as_dict()))
            return 0

        if args.command == "serve":
            from character_os.studio.web import serve_studio

            serve_studio(studio, host=args.host, port=args.port)
            return 0
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


def _cmd_set_character(studio: StudioService, args) -> int:
    drives = _parse_drives(args.drive)
    add_goal = _parse_goal(args.add_goal) if args.add_goal else None
    goal_priority = _parse_kv(args.goal_priority, label="--goal-priority")
    goal_status = _parse_kv(args.goal_status, label="--goal-status")
    goal_description = _parse_goal_descriptions(args.goal_description)
    if not _has_character_set_changes(
        args, drives, add_goal, goal_priority, goal_status, goal_description
    ):
        print("Error: no changes specified", file=sys.stderr)
        return 1
    path = studio.edit_character(
        args.id,
        name=args.name,
        description=args.description,
        world_id=args.world_id,
        add_traits=args.add_trait or None,
        remove_traits=args.remove_trait or None,
        add_fears=args.add_fear or None,
        remove_fears=args.remove_fear or None,
        add_preferences=args.add_preference or None,
        remove_preferences=args.remove_preference or None,
        drives=drives or None,
        voice_tone=args.voice_tone,
        add_quirks=args.add_quirk or None,
        remove_quirks=args.remove_quirk or None,
        default_trust=args.default_trust,
        default_familiarity=args.default_familiarity,
        add_goal=add_goal,
        remove_goal_id=args.remove_goal_id,
        goal_priority=goal_priority or None,
        goal_status=goal_status or None,
        goal_description=goal_description or None,
    )
    payload = {"updated": str(path), "id": args.id, "kind": "character"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Updated {path}")
        print("(Backup written beside it as character.yaml.bak)")
    return 0


def _cmd_set_world(studio: StudioService, args) -> int:
    if not _has_world_set_changes(args):
        print("Error: no changes specified", file=sys.stderr)
        return 1
    path = studio.edit_world(
        args.id,
        name=args.name,
        description=args.description,
        era=args.era,
        tone=args.tone,
        add_rules=args.add_rule or None,
        remove_rules=args.remove_rule or None,
    )
    payload = {"updated": str(path), "id": args.id, "kind": "world"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Updated {path}")
        print("(Backup written beside it as world.yaml.bak)")
    return 0


def _has_character_set_changes(
    args, drives, add_goal, goal_priority, goal_status, goal_description
) -> bool:
    return any(
        [
            args.name,
            args.description,
            args.world_id,
            args.add_trait,
            args.remove_trait,
            args.add_fear,
            args.remove_fear,
            args.add_preference,
            args.remove_preference,
            drives,
            args.voice_tone,
            args.add_quirk,
            args.remove_quirk,
            args.default_trust is not None,
            args.default_familiarity is not None,
            add_goal,
            args.remove_goal_id,
            goal_priority,
            goal_status,
            goal_description,
        ]
    )


def _has_world_set_changes(args) -> bool:
    return any(
        [
            args.name,
            args.description,
            args.era,
            args.tone,
            args.add_rule,
            args.remove_rule,
        ]
    )


def _parse_drives(items: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --drive {item!r}; expected key=value")
        key, raw = item.split("=", 1)
        out[key.strip()] = float(raw.strip())
    return out


def _parse_kv(items: list[str], *, label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid {label} {item!r}; expected id=value")
        key, raw = item.split("=", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or not raw:
            raise ValueError(f"Invalid {label} {item!r}; expected id=value")
        out[key] = raw
    return out


def _parse_goal(raw: str) -> tuple[str, str]:
    if ":" not in raw:
        raise ValueError("--add-goal must be ID:DESCRIPTION")
    goal_id, desc = raw.split(":", 1)
    goal_id = goal_id.strip()
    desc = desc.strip()
    if not goal_id or not desc:
        raise ValueError("--add-goal must be ID:DESCRIPTION")
    return goal_id, desc


def _parse_goal_descriptions(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        goal_id, desc = _parse_goal(item)
        out[goal_id] = desc
    return out


def _emit(payload: object, *, as_json: bool, human) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(human(payload))
    return 0


def _format_pack_list(rows: list[dict]) -> str:
    if not rows:
        return "(none)"
    lines = [f"{r['id']:24} {r['name']}  ({r['path']})" for r in rows]
    return "\n".join(lines)


def _format_character(d: dict) -> str:
    goals = "\n".join(
        f"  - [{g['priority']}/{g['status']}] {g['id']}: {g['description']}" for g in d["goals"]
    ) or "  (none)"
    drives = ", ".join(f"{k}={v:.2f}" for k, v in d["drives"].items())
    overrides = ", ".join(d["prompt_overrides"]) or "(none)"
    fears = ", ".join(d.get("fears") or []) or "(none)"
    prefs = ", ".join(d.get("preferences") or []) or "(none)"
    return "\n".join(
        [
            f"{d['name']} ({d['id']})",
            f"World: {d['world']}",
            f"TTS voice: {d['tts_voice']}",
            f"Traits: {', '.join(d['traits']) or '(none)'}",
            f"Fears: {fears}",
            f"Preferences: {prefs}",
            f"Defaults: trust={d['trust_default']:.2f} familiarity={d['familiarity_default']:.2f}",
            f"Drives (pack): {drives}",
            f"Knowledge entries: {d['knowledge_count']}",
            f"Prompt overrides: {overrides}",
            "Goals:",
            goals,
            "",
            d["description"],
        ]
    )


def _format_world(d: dict) -> str:
    ids = ", ".join(d["knowledge_ids"][:12])
    more = "" if len(d["knowledge_ids"]) <= 12 else f" …(+{len(d['knowledge_ids']) - 12})"
    era = d.get("era") or "(none)"
    tone = d.get("tone") or "(none)"
    rules = d.get("rules") or []
    rule_lines = "\n".join(f"  - {r}" for r in rules) or "  (none)"
    return "\n".join(
        [
            f"{d['name']} ({d['id']})",
            f"Era: {era}",
            f"Tone: {tone}",
            f"Knowledge entries: {d['knowledge_count']}",
            f"Ids: {ids}{more}",
            "Rules:",
            rule_lines,
            "",
            d["description"],
        ]
    )


def _format_runtime(d: dict) -> str:
    drives = ", ".join(f"{k}={v:.2f}" for k, v in d["drives"].items())
    lines = [
        f"Runtime — {d['character_id']}",
        f"DB: {d['db_path']}",
        f"Trust={d['trust']:.2f} familiarity={d['familiarity']:.2f}",
        f"Drives: {drives}",
        f"Active memories ({len(d['active_memories'])}):",
    ]
    if not d["active_memories"]:
        lines.append("  (none)")
    else:
        for m in d["active_memories"]:
            lines.append(f"  - [{m['importance']:.2f}] {m['content']}")
    lines.append(f"Archived memories ({len(d['archived_memories'])}):")
    if not d["archived_memories"]:
        lines.append("  (none)")
    else:
        for m in d["archived_memories"][:20]:
            lines.append(f"  - [{m['importance']:.2f}] {m['content']}")
        if len(d["archived_memories"]) > 20:
            lines.append(f"  …(+{len(d['archived_memories']) - 20} more)")
    return "\n".join(lines)


def _format_validation(d: dict) -> str:
    status = "OK" if d["ok"] else "FAILED"
    lines = [f"[{status}] {d['kind']} {d['id']}", f"Path: {d['path']}"]
    if d["errors"]:
        lines.append("Errors:")
        lines.extend(f"  - {e}" for e in d["errors"])
    if d["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"  - {w}" for w in d["warnings"])
    if d["ok"] and not d["warnings"]:
        lines.append("No issues.")
    return "\n".join(lines)


def _format_trace(d: dict) -> str:
    lines = [
        f"Trace — {d['character_id']} ({d['provider']})",
        f"User: {d['user_message']}",
        "",
        "Stages:",
    ]
    if not d["stages"]:
        lines.append("  (none captured)")
    else:
        for s in d["stages"]:
            detail = f" {s['detail']}" if s.get("detail") else ""
            lines.append(f"  [{s['stage']}]{detail}")
    lines.extend(
        [
            "",
            f"Thoughts: {d['thoughts'] or '(none)'}",
            f"Reply: {d['reply'] or '(none)'}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
