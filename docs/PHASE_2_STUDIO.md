"""Phase 2 — Character Studio

Character Studio is the authoring and debugging layer for Character OS content packs.

It sits **atop** `loader/` and `persistence/` — it does not replace the event-driven brain pipeline.

## Phase 2 goals (roadmap)

- create characters
- edit personalities
- inspect memories
- edit worlds
- debugging tools

## CLI (current)

Entry point: `character-os-studio`

```bash
character-os-studio list characters
character-os-studio list worlds
character-os-studio show character lumen
character-os-studio show world caribbean-1790
character-os-studio validate character lumen
character-os-studio validate world caribbean-1790
character-os-studio memories lumen
character-os-studio create-character my-bot --name "My Bot" --world everyday-present
character-os-studio set character my-bot --add-trait calm --drive curiosity=0.7
character-os-studio set character my-bot --add-goal scout:Look around carefully
```

Add `--json` for machine-readable output. `validate` exits `2` on failure.

### `set` notes

- Rewrites `character.yaml` (comments/formatting may change)
- Writes `character.yaml.bak` beside the pack before saving
- Rolls back if validation / loader reject the result

### Design choices

1. **CLI before GUI** — fastest path to inspect packs and SQLite state using existing loaders; a later web UI can call the same `StudioService`.
2. **No bus bypass for chat** — Studio inspects/scaffolds/edits packs; conversation still goes through `character-os` / `CharacterSession`.
3. **Validate via loader** — packs must round-trip through `load_character` / `load_world`.
4. **Scaffold + targeted set** — create minimal packs, then patch common fields; deep personality polish can still be hand-edited.

## Later Studio slices

- World pack scaffolding and knowledge editors
- Richer goal/personality editors (priority/status, fears/preferences lists)
- Stage-debug viewer (wire `--debug-stages` history)
- Optional web UI under `studio/` frontend
"""
