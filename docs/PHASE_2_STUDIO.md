# Phase 2 — Character Studio

Character Studio is the authoring and debugging layer for Character OS content packs.

It sits **atop** `loader/` and `persistence/` — it does not replace the event-driven brain pipeline.

## Phase 2 goals (roadmap)

- create characters
- edit personalities
- inspect memories
- edit worlds
- debugging tools
- optional web UI

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
character-os-studio reset-memories lumen --confirm
character-os-studio create-character my-bot --name "My Bot" --world everyday-present
character-os-studio create-world my-world --name "My World" --era now --tone calm
character-os-studio set character my-bot --add-trait calm --drive curiosity=0.7
character-os-studio set character my-bot --add-fear silence --add-preference tea
character-os-studio set character my-bot --add-goal scout:Look around carefully
character-os-studio set character my-bot --goal-priority scout=high --goal-status scout=active
character-os-studio set world my-world --add-rule "Stay consistent with lore" --tone curious
character-os-studio add-knowledge my-world --id harbor_map --summary "A map of the harbor"
character-os-studio trace lumen "Hello there." --provider stub
character-os-studio serve --port 8765
```

Add `--json` for machine-readable output. `validate` exits `2` on failure.

### `set` notes

- Rewrites `character.yaml` or `world.yaml` (comments/formatting may change)
- Writes `.yaml.bak` beside the pack before saving
- Rolls back if validation / loader reject the result
- Character: traits, fears, preferences, quirks, drives, goals (priority/status/description), relationship defaults
- World: name, description, era, tone, rules

### `trace` notes

- Runs one message through `CharacterSession` (Observe → … → Act)
- Default provider is `stub`; use `--provider openai` for live LLM
- Ephemeral by default (`persist=False`); pass `--persist` to write SQLite
- Loads character packs from the repo loader paths (not an alternate `--root` scaffold-only tree)

### `serve` notes

- Optional stdlib HTTP UI at `http://127.0.0.1:8765`
- Same `StudioService` as the CLI (list/show/validate/memories/stage-trace)
- No extra dependencies; chat still goes through `character-os`

### Design choices

1. **CLI before GUI** — authoring and debug on the same `StudioService`; web UI is a thin optional surface.
2. **No bus bypass for chat** — Studio inspects/scaffolds/edits packs; conversation still goes through `character-os` / `CharacterSession`.
3. **Validate via loader** — packs must round-trip through `load_character` / `load_world`.
4. **Scaffold + targeted set** — create minimal packs, then patch common fields; deep polish can still be hand-edited.

### `reset-memories` notes

- Clears active + archived SQLite memories for one character
- Restores emotional drives and relationship trust/familiarity to pack defaults
- Requires `--confirm` (irreversible for that character's rows)
- Same wipe path as chat `/reset confirm` (Studio does not clear an active chat session)

## Phase 2 status

Done for this phase slice:

- Character create / validate / set (including fears, preferences, goal fields)
- World create / validate / set / add-knowledge
- Memory inspect + `reset-memories`
- Stage-debug `trace` + optional `serve` web UI
