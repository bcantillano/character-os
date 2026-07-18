# Character OS

> A configurable AI framework for creating believable interactive characters.

## Overview

Character OS is an open architecture for building characters that feel alive.

Unlike traditional chatbots, Character OS is designed around the principles of personality, memory, emotion, goals, contextual reasoning, and purposeful behavior.

The long-term vision is for the same character brain to power robots, animatronics, AR experiences, VR experiences, games, and interactive attractions without changing the underlying intelligence.

The physical embodiment is interchangeable.

The brain is the product.

---

## Project Goals

Character OS aims to answer one question:

> Can software make people emotionally believe they are interacting with a fictional character?

Rather than creating an assistant that answers questions, Character OS creates characters with their own motivations, personalities, and memories.

The system should make interactions feel natural, imperfect, emotional, and authentic.

---

## Current Phase

Phase 1 focuses on the Character Brain through text conversation.

No robotics.

No computer vision.

No movement.

Voice output (TTS) is Phase 1b and optional via `--tts` / `--tts-play`. Speech recognition remains Phase 3.

The goal is to create a believable character through text conversation alone (Phase 1), then layer spoken delivery without changing the brain pipeline.

Success means the user feels they met a character — not that they used an AI. See Phase 1 success criteria in `docs/ROADMAP.md` and the lifecycle in `docs/CHARACTER_LIFECYCLE.md`.

---

## Long-Term Vision

Future versions will support:

- Robotics
- Animatronics
- Interactive queue experiences
- Theme park attractions
- AR characters
- VR characters
- Digital NPCs
- Educational companions

The Character Brain should remain independent from any hardware platform.

---

## Content Model

Characters and worlds are defined through YAML configuration and Markdown prompts — not application code.

- `characters/<name>/` — character packs (`character.yaml` + assets)
- `worlds/<name>/` — reusable world packs (shared lore and rules)
- `prompts/` — editable LLM prompt templates

See `docs/CONFIGURATION.md` for full schemas.

---

## How to run

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[openai,dev]"
cp .env.example .env   # set OPENAI_API_KEY if using OpenAI
```

Chat (stub LLM, no API key):

```bash
character-os --character captain-redbeard
```

Live OpenAI:

```bash
character-os --provider openai --character captain-redbeard
```

Companion robot (Phase 1 reference; easier TTS target):

```bash
character-os --provider openai --tts --tts-play --character lumen
```

Useful flags: `--show-thoughts`, `--debug-stages`, `--enable-ticks`, `--once "hello"`, `--no-persist`, `--tts` / `--tts-play` (Phase 1b voice).

### Character Studio (Phase 2)

```bash
character-os-studio list characters
character-os-studio show character lumen
character-os-studio validate character lumen
character-os-studio memories lumen
character-os-studio create-character my-bot --name "My Bot" --world everyday-present
character-os-studio set character my-bot --add-trait calm --drive curiosity=0.7
```

See `docs/PHASE_2_STUDIO.md`.

Live OpenAI chat with spoken replies:

```bash
character-os --provider openai --tts --tts-play --character captain-redbeard
```

Run from the repo with the venv activated (`character-os` is installed into that environment). Equivalent: `python -m character_os.cli.chat …`.