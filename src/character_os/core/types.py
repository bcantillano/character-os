"""Shared domain types for Character OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentKind(str, Enum):
    SPEAK = "speak"
    WAIT = "wait"
    UPDATE_STATE = "update_state"


@dataclass
class EmotionalDrives:
    curiosity: float = 0.5
    trust: float = 0.5
    excitement: float = 0.5
    fear: float = 0.5
    confidence: float = 0.5
    energy: float = 0.5

    def clamp(self) -> EmotionalDrives:
        def _c(v: float) -> float:
            return max(0.0, min(1.0, v))

        return EmotionalDrives(
            curiosity=_c(self.curiosity),
            trust=_c(self.trust),
            excitement=_c(self.excitement),
            fear=_c(self.fear),
            confidence=_c(self.confidence),
            energy=_c(self.energy),
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "curiosity": self.curiosity,
            "trust": self.trust,
            "excitement": self.excitement,
            "fear": self.fear,
            "confidence": self.confidence,
            "energy": self.energy,
        }


@dataclass
class Goal:
    id: str
    description: str
    priority: str = "medium"
    status: str = "active"


@dataclass
class KnowledgeEntry:
    id: str
    topic: str
    summary: str
    details: str = ""


@dataclass
class Personality:
    traits: list[str] = field(default_factory=list)
    voice: dict[str, Any] = field(default_factory=dict)
    fears: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)


@dataclass
class TTSProfile:
    """Provider settings for Phase 1b voice output (not personality writing style)."""

    provider: str = "stub"
    voice: str = "alloy"
    model: str = "gpt-4o-mini-tts"
    instructions: str = ""
    response_format: str = "mp3"
    speed: float = 1.0


@dataclass
class CharacterDefinition:
    """Static character pack loaded from YAML (not runtime state)."""

    id: str
    name: str
    world: str
    description: str
    personality: Personality
    goals: list[Goal]
    emotional_drives: EmotionalDrives
    knowledge: list[KnowledgeEntry] = field(default_factory=list)
    default_trust: float = 0.2
    default_familiarity: float = 0.0
    assets: dict[str, str] = field(default_factory=dict)
    prompts: dict[str, str] = field(default_factory=dict)
    tts: TTSProfile = field(default_factory=TTSProfile)


@dataclass
class WorldDefinition:
    id: str
    name: str
    description: str
    era: str = ""
    tone: str = ""
    rules: list[str] = field(default_factory=list)
    knowledge: list[KnowledgeEntry] = field(default_factory=list)


@dataclass
class Intent:
    kind: IntentKind
    goal_focus: str | None = None
    reasoning: str = ""
    source: str = "user"  # "user" | "tick"


@dataclass
class Interpretation:
    intent: str
    topics: list[str] = field(default_factory=list)
    emotional_tone: str = "neutral"
    relationship_signals: str = ""
    notable_facts: list[str] = field(default_factory=list)
    raw_message: str = ""
    # Optional numeric deltas from the interpreter (None → heuristic fallback).
    trust_delta: float | None = None
    familiarity_delta: float | None = None


@dataclass
class ConversationState:
    """Session-only context. Discarded when the interaction ends."""

    current_topic: str | None = None
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    temporary_context: dict[str, Any] = field(default_factory=dict)

    def add_turn(self, role: str, text: str, max_turns: int = 20) -> None:
        self.recent_turns.append({"role": role, "text": text})
        if len(self.recent_turns) > max_turns:
            self.recent_turns = self.recent_turns[-max_turns:]


@dataclass
class CharacterState:
    """Runtime Reflect state owned by the Character Brain."""

    character_id: str
    emotional_drives: EmotionalDrives
    goals: list[Goal]
    conversation: ConversationState = field(default_factory=ConversationState)
    user_trust: float = 0.2
    user_familiarity: float = 0.0
    last_interpretation: Interpretation | None = None
    last_intent: Intent | None = None
    last_thoughts: str = ""
    tick_count: int = 0
