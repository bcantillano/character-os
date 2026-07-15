# Cursor Rules

You are helping build Character OS.

This project is a long-term software platform for creating believable interactive fictional characters.

## Core Philosophy

The objective is not to build a chatbot.

The objective is to build believable characters.

Always optimize for the illusion of life.

## Architecture

The Character Brain owns all state.

Characters and worlds are data-driven. Configuration lives in YAML (`characters/`, `worlds/`). Prompts live in Markdown (`prompts/`). Never embed prompts or character definitions in source code.

Never place business logic inside prompts.

The engine is event-driven. All modules communicate through `events/` — no direct cross-module calls.

Decision (intent) and behavior (execution) are separate modules.

Characters follow Observe → Interpret → Reflect → Decide → Act → Remember (`docs/CHARACTER_LIFECYCLE.md`).

Long-term memory persists across sessions. Conversation state is session-only. Do not conflate them.

Emotional state uses explicit drives (Curiosity, Trust, Excitement, Fear, Confidence, Energy), each 0.0–1.0 — not valence/arousal.

LLM access goes through `llm/` only. OpenAI is the default provider; the brain must remain provider-agnostic.

Phase 1 time ticks update internal state only. They must not produce unprompted CLI speech.

The LLM should only:

- reason
- plan
- generate dialogue

Everything else belongs in software.

## Design

Favor clean architecture.

Favor modular systems.

Avoid tight coupling.

Avoid unnecessary abstraction.

Keep code maintainable.

Explain architectural tradeoffs before making major changes.

## Personality

Characters should

- have flaws
- make mistakes
- become distracted
- ask questions
- remember
- pursue goals

They should never feel like assistants.

## Future Compatibility

Every system should be designed so that future robotics, vision, sensors, and animation can connect without changing the Character Brain.

Protect the architecture.

## Engineering Journal

Every development session updates `docs/engineering-journal/YYYY-MM-DD.md`.

Sections: Today's Goal, What We Learned, Architectural Decisions, Problems, Future Ideas.

Hooks and `.cursor/rules/engineering-journal.mdc` enforce this automatically.