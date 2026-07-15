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

No voice (TTS arrives in Phase 1b; speech recognition in Phase 3).

The goal is to create a believable character through text conversation alone.

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