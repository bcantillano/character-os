# Roadmap

## Phase 1

Character Brain (text)

- personality
- long-term memory (persists across sessions)
- conversation state (session-only)
- knowledge
- emotional drives (Curiosity, Trust, Excitement, Fear, Confidence, Energy)
- goals
- decision engine (intent)
- behavior executor (action)
- internal thoughts
- text conversation (CLI)
- event bus (central communication)
- time-tick scheduler (internal state only — no unprompted CLI speech)
- provider-agnostic LLM layer (OpenAI default)
- data-driven character and world packs (YAML + Markdown prompts)
- character lifecycle: Observe → Interpret → Reflect → Decide → Act → Remember

### Phase 1 success criteria

Not a chatbot. A successful demo shows consistent personality, persistent memory, emotional consistency, world awareness, goal-driven conversation, and natural curiosity. After ~10 minutes the user should describe meeting a character, not using an AI.

---

## Phase 1b

Voice output

- text-to-speech (TTS)
- character voice profiles
- no speech recognition (deferred to Phase 3)

---

## Phase 2

Character Studio

- create characters
- edit personalities
- inspect memories
- edit worlds
- debugging tools

See `docs/PHASE_2_STUDIO.md`. CLI: `character-os-studio` (list/show/validate/set, create character & world, add-knowledge, memories, stage `trace`, optional `serve` web UI).

---

## Phase 3

World Awareness

- speech recognition
- computer vision
- context awareness

---

## Phase 4

Embodiment

- robot hardware
- motors
- LEDs
- facial expressions
- movement

---

## Phase 5

Interactive Experiences

- queue entertainment
- multiple characters
- guest interactions
- collaborative storytelling