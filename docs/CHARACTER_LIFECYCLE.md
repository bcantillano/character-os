# Character Lifecycle

Every Character OS character follows the same lifecycle, regardless of embodiment.

Embodiment changes **how** events arrive and **how** actions are expressed. It does not change the lifecycle itself.

This loop is the conceptual foundation for Phase 1 text conversation and for later voice, vision, robotics, sensors, and multi-character experiences.

---

## The Loop

```
Observe → Interpret → Reflect → Decide → Act → Remember
                         ↑_________________________|
```

The cycle repeats for every meaningful event — a user message, a time tick, a future sensor reading, or a motion completing.

---

## Stages

### 1. Observe

Receive events from the world through the event bus.

| Phase 1 | Later phases |
|---------|--------------|
| `UserMessageEvent` | `VisionDetectedEvent` |
| `TimeTickEvent` | `SpeechRecognizedEvent` |
| | `SensorReadingEvent` |
| | `MotionCompletedEvent` |

Observation is input-agnostic. The brain does not care whether text came from a CLI, microphone, or attraction sensor — only that an event arrived.

### 2. Interpret

Understand what the event means in context.

- Conversation Interpreter extracts intent, topics, tone, and relationship signals
- Future awareness modules normalize vision or sensor data into comparable structured signals
- Output is structured meaning, not dialogue

Produces events such as `InputInterpretedEvent`.

### 3. Reflect

Consider the character's inner life against the interpreted situation:

- **Personality** — how they tend to think and behave
- **Knowledge** — world and character facts (static configuration)
- **Memory** — long-term facts and relationships (persisted)
- **Conversation state** — current topic and recent dialogue (session-only)
- **Emotional drives** — Curiosity, Trust, Excitement, Fear, Confidence, Energy
- **Goals** — what they want right now
- **Relationships** — trust and history with the user or others

Reflection updates internal readiness for a decision. It does not choose an action yet.

The Character Brain owns this stage and publishes state changes when reflection completes.

### 4. Decide

Choose an **intent** — what the character wants to do next.

Owned by `decision/`. Produces `IntentDecidedEvent`.

Examples: speak, wait, pursue a goal, ask a question, deflect, observe further.

Decision never executes motors, TTS, or dialogue generation. It only declares intent.

### 5. Act

Turn intent into behavior.

Owned by `behavior/`.

| Phase 1 | Later phases |
|---------|--------------|
| Speak (thoughts → response → text) | Speak with voice (TTS) |
| Wait / idle (no unprompted CLI speech) | Move, gesture, facial expression |
| Update goals / internal pursuits | Coordinate attraction timing |

Action may emit further events (`ThoughtsGeneratedEvent`, `ResponseReadyEvent`, future `MotionRequestedEvent`).

### 6. Remember

Store the experience and update lasting state.

- Write meaningful facts and relationship changes to **long-term memory**
- Update emotional drives and goal progress
- Persist what should survive across sessions
- Clear or discard **conversation state** when the interaction ends

Remember closes the loop so the next Observe starts from an evolved character — not a blank slate.

---

## Phase 1 Mapping

| Lifecycle stage | Primary modules |
|-----------------|-----------------|
| Observe | `events/`, `cli/`, `brain/scheduler.py` |
| Interpret | `interpreter/` |
| Reflect | `brain/` (personality, knowledge, memory, emotion, goals, relationships) |
| Decide | `decision/` |
| Act | `behavior/`, `thoughts/`, `response/` |
| Remember | `brain/` + `persistence/` |

---

## Reactive vs Proactive

| Path | Observe trigger | Act in Phase 1 CLI |
|------|-----------------|--------------------|
| **Reactive** | User message | May speak |
| **Proactive** | Time tick | State-only — no unprompted speech |

Time ticks still run Observe → Interpret → Reflect → Decide → Act → Remember, but Phase 1 Act for ticks is limited to internal updates (emotional decay/recovery, energy, goal progression, memory importance, relationships). Unprompted speech and embodiment behaviors arrive in later phases when Act can safely express itself outside a waiting user.

---

## Embodiment Independence

```
Same lifecycle
    ├── Text CLI (Phase 1)
    ├── Voice (Phase 1b / 3)
    ├── Vision & sensors (Phase 3)
    ├── Robotics / animatronics (Phase 4)
    └── Multi-character experiences (Phase 5)
```

Changing embodiment means new event publishers (Observe) and new behavior actions (Act). Interpret, Reflect, Decide, and Remember stay in the Character Brain.

---

## Design Rules

1. Every input source must enter through **Observe** (events).
2. No module skips to Act without **Decide**.
3. **Remember** always runs after meaningful interactions — otherwise the character cannot evolve.
4. Long-term memory and conversation state remain distinct (see Architecture).
5. The lifecycle is incomplete without goals, emotion, and memory influencing Decide and Act — a response path that ignores Reflect is chatbot logic, not Character OS.
