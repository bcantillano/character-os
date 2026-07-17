"""Phase 2 Character Studio CLI — inspect packs and memories; scaffold characters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from character_os.studio.service import StudioService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="character-os-studio",
        description="Character Studio (Phase 2) — list/show packs, inspect memories, scaffold characters",
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
                print(f"Edit {path / 'character.yaml'} then chat with: character-os --character {args.character_id}")
            return 0
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


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
    return "\n".join(
        [
            f"{d['name']} ({d['id']})",
            f"World: {d['world']}",
            f"TTS voice: {d['tts_voice']}",
            f"Traits: {', '.join(d['traits']) or '(none)'}",
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
    return "\n".join(
        [
            f"{d['name']} ({d['id']})",
            f"Knowledge entries: {d['knowledge_count']}",
            f"Ids: {ids}{more}",
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


if __name__ == "__main__":
    raise SystemExit(main())
