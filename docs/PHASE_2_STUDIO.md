"""Phase 2 — Character Studio

Character Studio is the authoring and debugging layer for Character OS content packs.

It sits **atop** `loader/` and `persistence/` — it does not replace the event-driven brain pipeline.

## Phase 2 goals (roadmap)

- create characters
- edit personalities
- inspect memories
- edit worlds
- debugging tools

## MVP shipped first (CLI)

Entry point: `character-os-studio`

```bash
character-os-studio list characters
character-os-studio list worlds
character-os-studio show character lumen
character-os-studio show world caribbean-1790
character-os-studio memories lumen
character-os-studio create-character my-bot --name "My Bot" --world everyday-present
```

Add `--json` for machine-readable output.

### Design choices

1. **CLI before GUI** — fastest path to inspect packs and SQLite state using existing loaders; a later web UI can call the same `StudioService`.
2. **No bus bypass for chat** — Studio inspects/scaffolds; conversation still goes through `character-os` / `CharacterSession`.
3. **Scaffold, then hand-edit** — `create-character` writes a minimal valid `character.yaml`; personality polish stays data-driven in the pack.

## Later Studio slices

- Interactive YAML edit / validation
- World pack scaffolding and knowledge editors
- Stage-debug viewer (wire `--debug-stages` history)
- Optional web UI under `studio/` frontend
"""
