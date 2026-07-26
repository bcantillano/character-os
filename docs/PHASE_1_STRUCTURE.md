# Phase 1 Structure

Proposed repository layout for Phase 1. No code implemented yet — this document defines where modules live and how they connect.

Character OS is **event-driven from day one**. All inputs — conversation, time, and (eventually) vision, sensors, and robotics — enter the system as events and flow through the same pipeline. Modules communicate through an event bus; they do not call each other directly.

---

## Repository Layout

```
character-os/
│
├── characters/                    # Character packs (data)
│   └── <character_id>/
│       ├── character.yaml
│       └── assets/
│
├── worlds/                        # Reusable world packs (data)
│   └── <world_id>/
│       ├── world.yaml
│       └── knowledge/
│
├── prompts/                       # Default LLM prompt templates
│
├── data/                          # Runtime persistence (gitignored)
│
├── docs/
│
├── src/
│   └── character_os/
│       ├── __init__.py
│       │
│       ├── events/                # Central communication layer
│       │   ├── types.py           # Event definitions (all sources)
│       │   ├── bus.py             # Publish / subscribe dispatcher
│       │   └── registry.py        # Handler registration
│       │
│       ├── cli/                   # Phase 1 entry point
│       │   └── chat.py            # Publishes UserMessageEvent; renders output
│       │
│       ├── core/                  # Shared types, interfaces, exceptions
│       │   ├── types.py           # CharacterState, Intent, Action, etc.
│       │   └── interfaces.py      # EventHandler, BehaviorHandler, etc.
│       │
│       ├── loader/                # Dynamic resource loading
│       │   ├── character.py
│       │   ├── world.py
│       │   └── prompts.py
│       │
│       ├── persistence/           # Durable storage (long-term only)
│       │   ├── database.py
│       │   └── repositories/
│       │       ├── long_term_memory.py
│       │       ├── emotion.py
│       │       └── relationships.py
│       │
│       ├── interpreter/           # Conversation Interpreter
│       │   └── handler.py         # UserMessageEvent → InputInterpretedEvent
│       │
│       ├── brain/                 # Character Brain (Reflect + Remember)
│       │   ├── orchestrator.py    # Subscribes to events; coordinates state
│       │   ├── scheduler.py       # Publishes TimeTickEvent (state updates only in Phase 1 CLI)
│       │   ├── personality.py
│       │   ├── knowledge.py
│       │   ├── memory.py          # Long-term memory access
│       │   ├── conversation.py    # Session-only conversation state
│       │   ├── emotion.py         # Emotional drives (0.0–1.0)
│       │   ├── goals.py
│       │   └── relationships.py
│       │
│       ├── decision/              # Decide — Intent
│       │   └── engine.py          # StateChangedEvent → IntentDecidedEvent
│       │
│       ├── behavior/              # Act — execution
│       │   ├── executor.py        # IntentDecidedEvent → dispatches behaviors
│       │   └── actions/           # Pluggable action handlers
│       │       ├── speak.py       # User-triggered dialogue path only in Phase 1
│       │       ├── wait.py        # Defer, observe, idle
│       │       └── update_state.py # Tick-driven internal updates (no speech)
│       │
│       ├── thoughts/              # Internal monologue stage
│       │   └── handler.py         # SpeakIntent → ThoughtsGeneratedEvent
│       │
│       ├── response/              # Dialogue generation stage
│       │   └── handler.py         # ThoughtsGenerated → ResponseReadyEvent
│       │
│       └── llm/                   # Provider-agnostic LLM layer
│           ├── provider.py        # Abstract LLMProvider interface
│           └── providers/
│               └── openai.py      # Default Phase 1 implementation
│
├── tests/
│   ├── events/
│   ├── brain/
│   ├── decision/
│   ├── behavior/
│   └── integration/
│
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## Design Principles

### 1. Events are the only communication path

Modules publish events and subscribe to events. No direct cross-module method calls outside the event bus.

```python
# Phase 1
UserMessageEvent          # from cli/
TimeTickEvent             # from brain/scheduler.py
InputInterpretedEvent     # from interpreter/
StateChangedEvent         # from brain/
IntentDecidedEvent        # from decision/
BehaviorRequestedEvent    # from behavior/executor.py
ThoughtsGeneratedEvent    # from thoughts/
ResponseReadyEvent        # from response/

# Future phases (same bus, new publishers)
VisionDetectedEvent       # Phase 3
SensorReadingEvent        # Phase 3
SpeechRecognizedEvent     # Phase 3
MotionCompletedEvent      # Phase 4
```

### 2. Decision and behavior are separate

| Layer | Question | Output |
|-------|----------|--------|
| **decision/** | What does the character *want* to do? | `IntentDecidedEvent` (intent, goal focus, emotional shift) |
| **behavior/** | How does the character *act* on that intent? | Dispatches to action handlers; may emit further events |

Decision produces **intent**. Behavior produces **action**. This keeps Phase 4 robotics (motors, LEDs, expressions) in `behavior/actions/` without touching decision logic.

### 3. Character Brain evolves on time ticks (state-only in Phase 1 CLI)

`brain/scheduler.py` publishes `TimeTickEvent` so internal state changes without user input:

- Emotional decay / recovery
- Energy changes
- Goal progression
- Memory importance changes
- Relationship updates

Phase 1 CLI ticks must **not** cause unprompted speech. Act for ticks uses `update_state` (or wait), not `speak`. Later embodiments may allow proactive outward behavior on idle ticks.

Reactive path: `UserMessageEvent` → Observe → Interpret → Reflect → Decide → Act (speak) → Remember.

Tick path: `TimeTickEvent` → Reflect → Decide → Act (state only) → Remember.

### 4. Long-term memory ≠ conversation state

- **Long-term memory** — persisted across sessions (names, preferences, experiences, relationship history)
- **Conversation state** — in-memory for the active interaction only (topic, recent turns, temporary context)

`persistence/` stores long-term data. Conversation state lives in `brain/conversation.py` and is discarded when the session ends.

### 5. LLM layer is provider-agnostic

Default provider: OpenAI (`llm/providers/openai.py`). Brain, decision, thoughts, and response modules depend only on `llm/provider.py`. Never import OpenAI SDKs outside `llm/providers/`.

### 6. Content stays separate from engine

`characters/`, `worlds/`, and `prompts/` remain at repo root. The engine loads them via `loader/` and never embeds character definitions in source.

### 7. Lifecycle foundation

All modules implement stages of Observe → Interpret → Reflect → Decide → Act → Remember. See `docs/CHARACTER_LIFECYCLE.md`.

---

## Event Flow (Phase 1)

### Reactive — user sends a message

```
cli/chat.py
  publishes UserMessageEvent
    → interpreter/handler.py
        publishes InputInterpretedEvent
          → brain/orchestrator.py (updates state)
              publishes StateChangedEvent
                → decision/engine.py
                    publishes IntentDecidedEvent
                      → behavior/executor.py
                          dispatches speak action
                            → thoughts/handler.py
                                publishes ThoughtsGeneratedEvent
                                  → response/handler.py
                                      publishes ResponseReadyEvent
                                        → cli/chat.py (renders text)
```

### Time tick — state only (no CLI speech)

```
brain/scheduler.py
  publishes TimeTickEvent
    → brain/orchestrator.py (emotional decay, energy, goals, memory importance, relationships)
        publishes StateChangedEvent
          → decision/engine.py
              publishes IntentDecidedEvent (typically update_state / wait)
                → behavior/executor.py
                    dispatches update_state (never speak in Phase 1 CLI idle path)
```

---

## Folder Rationale

| Folder | Role | Future expansion |
|--------|------|------------------|
| `events/` | Central bus; all modules connect here | New event types for vision, sensors, robotics plug in without pipeline changes |
| `brain/scheduler.py` | Time-driven internal evolution | Later: idle ticks may trigger proactive speak/move for embodiment |
| `brain/conversation.py` | Session-only dialogue context | Cleared per session; never written as long-term fact without Remember filtering |
| `decision/` | Intent only | Unchanged when embodiment arrives |
| `behavior/` | Action execution | Phase 1b adds `actions/speak_voice.py`; Phase 4 adds proactive and motion actions |
| `llm/` | Abstract provider + OpenAI default | Anthropic / Ollama providers drop in beside OpenAI |
| `interpreter/` | Converts raw input events to structured signals | Phase 3 adds vision/speech interpreters publishing the same `InputInterpretedEvent` |
| `cli/` | Publishes `UserMessageEvent` | Phase 3 STT publishes `SpeechRecognizedEvent`; bridge emits `UserMessageEvent` for the shared interpret path |

---

## Deliberately Not in Phase 1

| Future module | Phase | How it connects |
|---------------|-------|-----------------|
| `voice/` | 1b | `behavior/actions/speak_voice.py` handles TTS on `ResponseReadyEvent` |
| `studio/` | 2 | UI atop `loader/` paths |
| `awareness/` | 3 | Publishes `VisionDetectedEvent`, `SpeechRecognizedEvent`, `SensorReadingEvent` |
| `embodiment/` | 4 | `behavior/actions/` for motors, LEDs, expressions |
| `experiences/` | 5 | Multi-character event orchestration above single brain instances |

---

## Pipeline vs. Previous Proposal

Changes from the earlier linear pipeline:

1. **Added `events/`** — replaces direct module-to-module calls
2. **Split `decision/` and `behavior/`** — intent vs execution
3. **Added `brain/scheduler.py`** — proactive `TimeTickEvent` loops
4. **`interpreter/`, `thoughts/`, `response/`** — become event handlers, not sequential function calls
5. **`cli/`** — publishes and consumes events rather than driving the pipeline directly

Everything else (`loader/`, `persistence/`, `llm/`, content folders) is unchanged.
