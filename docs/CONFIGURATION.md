# Configuration

Character OS is **data-driven**. Characters and worlds are defined through YAML configuration, Markdown prompts, and supporting assets — not application code.

Creating a new character means adding a folder under `characters/`. Creating a new world means adding a folder under `worlds/`. The engine loads everything dynamically at runtime.

---

## Design Principles

1. **Configuration over code** — personality, knowledge, goals, and world rules live in YAML and Markdown files.
2. **Separation of concerns** — character identity is separate from shared world knowledge.
3. **Reusable world packs** — multiple characters can reference the same `worlds/<name>/` pack.
4. **Editable prompts** — all LLM prompts are Markdown files under `prompts/`, never embedded in source.
5. **Dynamic loading** — the engine discovers and loads resources by path; no code changes required for new content.

---

## Repository Layout

```
character-os/
├── characters/
│   └── <character_id>/
│       ├── character.yaml      # identity, personality, goals, world reference
│       └── assets/             # portraits, audio refs, optional prompt overrides
├── worlds/
│   └── <world_id>/
│       ├── world.yaml          # world metadata, rules, knowledge index
│       └── knowledge/          # reusable facts, locations, factions, lore
├── prompts/
│   ├── conversation_interpreter.md
│   ├── decision_engine.md
│   ├── internal_thoughts.md
│   └── response_generator.md
└── data/                       # runtime persistence (SQLite, per-character memory)
```

---

## Character Packs

Path: `characters/<character_id>/`

Each character is a self-contained pack. `character.yaml` is required.

### character.yaml

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique slug; must match folder name |
| `name` | yes | Display name |
| `world` | yes | Reference to a `worlds/<world_id>/` pack |
| `description` | yes | Short identity summary |
| `personality` | yes | Traits, voice (writing style), fears, preferences |
| `emotional_drives` | no | Initial Curiosity, Trust, Excitement, Fear, Confidence, Energy (each 0.0–1.0); defaults if omitted |
| `goals` | yes | What the character wants |
| `knowledge` | no | Character-specific facts not in the world pack |
| `relationships` | no | Default trust baselines for long-term relationship state |
| `prompts` | no | Per-character prompt overrides (paths to `.md` files) |
| `assets` | no | Paths to supporting files under `assets/` |
| `tts` | no | Phase 1b voice profile (provider, voice id, model, instructions) |

Characters **inherit world knowledge** from their referenced world pack. The `knowledge` block in `character.yaml` adds private or character-specific facts only.

### TTS profile (`tts`)

Optional. Separate from `personality.voice` (dialogue writing style). Used when the CLI enables TTS (`--tts` / `--tts-play`).

With `--tts-play`, speech is synthesized in sentence-sized chunks so playback can start after the first chunk (lower time-to-first-audio). `--tts` without play still synthesizes the full reply as one file.

| Field | Default | Description |
|-------|---------|-------------|
| `provider` | `stub` | `stub` or `openai` |
| `voice` | `alloy` | Provider voice id (e.g. OpenAI `onyx`) |
| `model` | `gpt-4o-mini-tts` | TTS model id |
| `format` | `mp3` | Audio container (`mp3`, `wav`, …) |
| `speed` | `1.0` | Playback speed (provider-dependent) |
| `instructions` | _(empty)_ | Style prompt for `gpt-4o-mini-tts` (ignored by `tts-1`) |
| `normalize_speech` | `false` | Soften dialect orthography for TTS only (CLI text unchanged) |
| `emotion_overlay` | `true` | Append mild delivery hints from current emotional drives |

### assets/

Optional directory for non-YAML content: images, voice profile hints, character-specific prompt files.

```
characters/captain-redbeard/
├── character.yaml
└── assets/
    └── portrait.png

characters/lumen/
├── character.yaml
└── assets/
```

---

## World Packs

Path: `worlds/<world_id>/`

World packs are shared environments. Any number of characters can set `world: <world_id>`.

### world.yaml

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique slug; must match folder name |
| `name` | yes | Display name |
| `description` | yes | Setting summary |
| `era` | no | Time period or genre framing |
| `tone` | no | Atmospheric guidance for the engine |
| `rules` | no | In-world constraints the character must respect |
| `knowledge_files` | yes | List of paths (relative to world folder) to knowledge YAML/MD files |

### knowledge/

Reusable lore split into focused files for maintainability:

```
worlds/caribbean-1790/
├── world.yaml
└── knowledge/
    ├── locations.yaml
    ├── factions.yaml
    └── glossary.yaml
```

Knowledge files use a consistent entry format:

```yaml
entries:
  - id: port_royal
    topic: locations
    summary: A bustling harbor town under naval patrol.
    details: |
      Port Royal is the largest settlement in the region.
      Pirates avoid it unless they have business in the taverns.
```

---

## Prompts

Path: `prompts/`

All LLM-facing prompt templates are Markdown files. The engine loads them at runtime and injects context variables (e.g. `{{character_name}}`, `{{emotional_state}}`).

Default prompts cover each pipeline stage:

| File | Stage |
|------|-------|
| `conversation_interpreter.md` | Input parsing |
| `decision_engine.md` | Behavioral decision |
| `internal_thoughts.md` | Private monologue |
| `response_generator.md` | Spoken dialogue |

Characters may override any prompt via the `prompts` block in `character.yaml`:

```yaml
prompts:
  internal_thoughts: characters/captain-redbeard/assets/internal_thoughts.md
```

Prompt files must remain **templates only**. Business logic (memory updates, emotion changes, goal progress) stays in Python modules.

---

## Loading Contract

The engine resolves content in this order:

1. Load `characters/<id>/character.yaml`
2. Load referenced `worlds/<world_id>/world.yaml`
3. Load all `knowledge_files` listed in the world pack
4. Merge character-specific `knowledge` entries on top of world knowledge
5. Load default prompts from `prompts/`, applying per-character overrides if present
6. Load runtime state (memory, emotion, relationships) from `data/`

No step requires modifying application source code.

---

## Adding a New Character

1. Create `characters/<new_id>/character.yaml`
2. Set `world:` to an existing world pack (or create a new one first)
3. Define personality, goals, and any character-specific knowledge
4. Optionally add `assets/`
5. Run the CLI — the engine discovers the new character automatically

## Adding a New World

1. Create `worlds/<new_id>/world.yaml`
2. Add `knowledge/` files and list them in `knowledge_files`
3. Reference `world: <new_id>` from any character
