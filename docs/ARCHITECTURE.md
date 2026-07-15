# Architecture

Character OS is composed of independent systems connected through an **event bus**.

The LLM is not the character.

The LLM is only responsible for language generation and reasoning.

Persistent state belongs entirely to Character OS.

Every character follows the same conceptual loop — **Observe → Interpret → Reflect → Decide → Act → Remember** — regardless of embodiment. See `docs/CHARACTER_LIFECYCLE.md`.

## Event-Driven Core

All inputs enter the system as **events** and flow through the same pipeline:

- **Phase 1** — `UserMessageEvent`, `TimeTickEvent`
- **Phase 3** — `VisionDetectedEvent`, `SpeechRecognizedEvent`, `SensorReadingEvent`
- **Phase 4** — `MotionCompletedEvent`, robotics feedback

Modules publish and subscribe through `events/`. They do not call each other directly.

## Pipeline Stages

Event in (Observe)

↓

Conversation Interpreter (Interpret)

↓

Character Brain — Reflect

    Personality

    Knowledge

    Long-term Memory

    Conversation State (session-only)

    Emotional Drives

    Goals

    Relationships

    Scheduler (TimeTickEvent)

↓

Decision Engine — Decide (intent)

↓

Behavior Executor — Act

↓

Internal Thoughts

↓

Response Generator

↓

Remember (persist long-term state)

↓

Event out (ResponseReadyEvent)

---

**Decision** determines what the character wants to do (intent).

**Behavior** executes that intent (speak, wait, pursue goal, and eventually move or express).

The Character Brain runs **time ticks** so internal state evolves without user input. In Phase 1 CLI, ticks update state only — they do not speak unprompted. Proactive outward behavior comes with embodiment in later phases.

---

## LLM Providers

Default Phase 1 provider: **OpenAI**.

The Character Brain must never depend on OpenAI (or any vendor) directly. All LLM use goes through `llm/` with an abstract provider interface so Anthropic, Ollama, and future providers can be swapped without changing business logic.

---

## Emotional Drives

Phase 1 does **not** use valence/arousal. Characters use explicit emotional drives, each normalized to `0.0–1.0`:

| Drive | Role |
|-------|------|
| Curiosity | Drive to ask, explore, notice gaps |
| Trust | Openness and willingness to share |
| Excitement | Intensity and engagement |
| Fear | Caution, evasion, superstition |
| Confidence | Certainty and boldness of claims |
| Energy | Pace, stamina, willingness to continue |

These drives influence decision making, dialogue, and future behavior. Higher-level models can be derived later if needed.

---

## Memory vs Conversation State

| Concept | Lifetime | Contents |
|---------|----------|----------|
| **Long-term memory** | Persists across sessions | Meaningful facts, preferences, user names, shared experiences, relationship history |
| **Conversation state** | Active interaction only | Current topic, recent dialogue, temporary context |

These are separate architectural concepts. Conversation state must not be treated as permanent memory.

---

## Time Ticks (Phase 1)

`TimeTickEvent` updates internal state only:

- emotional decay / recovery
- energy changes
- goal progression
- memory importance changes
- relationship updates

When the user next interacts, those changes influence the response naturally. Idle ticks must **not** produce unprompted CLI speech in Phase 1.

---

## Phase 1 Success Criteria

Phase 1 succeeds when users experience a **believable character**, not a chatbot.

A successful interaction demonstrates:

- Consistent personality
- Persistent long-term memory
- Emotional consistency
- World awareness
- Goal-driven conversation
- Natural curiosity (the character asks questions)
- Non-assistant behavior

After about ten minutes, the user should describe the experience as meeting a character rather than using an AI.

---

Future systems

Vision

Motion

Robotics

Speech

Sensors

Dashboard

These systems publish events into the same bus without tightly coupling to the Character Brain.

---

## Content Model

Characters and worlds are **data-driven**, not code-driven.

```
characters/<character_id>/character.yaml   → identity, personality, goals
worlds/<world_id>/world.yaml               → shared environment and lore
prompts/*.md                               → editable LLM templates
```

- Characters reference a world pack via `world: <world_id>`
- World knowledge is reusable across characters
- Prompts are Markdown files loaded at runtime — never embedded in source
- New characters require configuration and content only, not application code changes

See `docs/CONFIGURATION.md` for schemas and loading contract.
