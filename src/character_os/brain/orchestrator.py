"""Character Brain orchestrator — Reflect + Remember."""

from __future__ import annotations

from character_os.brain.conversation import ConversationStore
from character_os.brain.emotion import (
    apply_interpretation_drives,
    apply_tick_decay,
    nudge,
    unstick_pegged_drives,
)
from character_os.brain.memory import MemoryStore
from character_os.brain.relationship import apply_relationship_update
from character_os.brain.speech_memory import format_speech_memory_context
from character_os.core.types import CharacterDefinition, CharacterState, WorldDefinition
from character_os.events.bus import EventBus
from character_os.events.types import (
    InputInterpretedEvent,
    ResponseReadyEvent,
    StateChangedEvent,
    TimeTickEvent,
)
from character_os.persistence.store import CharacterPersistence


class BrainOrchestrator:
    def __init__(
        self,
        bus: EventBus,
        character: CharacterDefinition,
        world: WorldDefinition,
        session_id: str,
        persistence: CharacterPersistence | None = None,
    ) -> None:
        self.bus = bus
        self.character = character
        self.world = world
        self.session_id = session_id
        self.persistence = persistence
        self.conversation = ConversationStore()

        if persistence is not None:
            self.memory = persistence.load_memory_store()
            drives = unstick_pegged_drives(
                persistence.load_drives(character.emotional_drives)
            )
            rel = persistence.load_relationship(
                character.default_trust, character.default_familiarity
            )
            user_trust = rel.trust
            user_familiarity = rel.familiarity
        else:
            self.memory = MemoryStore()
            drives = character.emotional_drives
            user_trust = character.default_trust
            user_familiarity = character.default_familiarity

        self.state = CharacterState(
            character_id=character.id,
            emotional_drives=drives,
            goals=list(character.goals),
            user_trust=user_trust,
            user_familiarity=user_familiarity,
        )

    def wire(self) -> None:
        self.bus.subscribe(InputInterpretedEvent, self.on_interpreted)
        self.bus.subscribe(TimeTickEvent, self.on_tick)
        self.bus.subscribe(ResponseReadyEvent, self.on_response_ready)

    def on_interpreted(self, event: InputInterpretedEvent) -> None:
        if not event.interpretation:
            return
        interp = event.interpretation
        self.state.last_interpretation = interp
        self.conversation.state.add_turn("user", interp.raw_message)
        if interp.topics:
            self.conversation.state.current_topic = interp.topics[0]

        self.state.emotional_drives = apply_interpretation_drives(
            self.state.emotional_drives,
            interp,
        )
        trust_delta, familiarity_delta = apply_relationship_update(self.state, interp)

        self._remember_notable_facts(interp.notable_facts, interp.raw_message)

        self.bus.publish(
            StateChangedEvent(
                character_id=self.character.id,
                session_id=self.session_id,
                trigger="user_message",
                summary=(
                    f"Interpreted user intent={interp.intent}; "
                    f"trust{trust_delta:+.3f} familiarity{familiarity_delta:+.3f}"
                ),
                state_snapshot={
                    "drives": self.state.emotional_drives.as_dict(),
                    "trust": self.state.user_trust,
                    "familiarity": self.state.user_familiarity,
                    "trust_delta": trust_delta,
                    "familiarity_delta": familiarity_delta,
                },
            )
        )
        self._persist()

    def on_tick(self, event: TimeTickEvent) -> None:
        self.state.tick_count += 1
        self.state.emotional_drives = apply_tick_decay(self.state.emotional_drives)
        self.memory.decay_importance()
        self.state.emotional_drives = nudge(self.state.emotional_drives, energy=0.01)

        self.bus.publish(
            StateChangedEvent(
                character_id=self.character.id,
                session_id=self.session_id,
                trigger="time_tick",
                summary=f"Tick {event.tick_index}: internal state updated",
                state_snapshot={
                    "drives": self.state.emotional_drives.as_dict(),
                    "tick_count": self.state.tick_count,
                },
            )
        )
        self._persist()

    def on_response_ready(self, event: ResponseReadyEvent) -> None:
        self.conversation.state.add_turn("character", event.text)
        self._persist()

    def remember_response(self, text: str) -> None:
        """Legacy hook; Remember runs on ResponseReadyEvent."""
        return

    def _remember_notable_facts(self, facts: list[str], raw_message: str) -> None:
        from character_os.brain.memory import MemoryFact, canonicalize_fact_content

        for fact in facts:
            if not fact or fact.lower() in {"none", "none yet", "n/a"}:
                continue
            content = fact if fact != raw_message else f"User said: {fact}"
            content = canonicalize_fact_content(content)
            existing = self.memory.find_similar(content)
            if existing is not None:
                existing.importance = min(1.0, existing.importance + 0.05)
                # Upgrade short / non-canonical wording when a richer form arrives.
                if len(content) > len(existing.content):
                    existing.content = content
                self.memory.mark_dirty(existing.id)
                continue
            if self.persistence is not None:
                stored = self.persistence.remember_fact(content, importance=0.6, tags=["interaction"])
                self.memory.add(stored, dirty=False)  # already written via remember_fact
            else:
                from uuid import uuid4

                self.memory.add(
                    MemoryFact(id=str(uuid4()), content=content, importance=0.6, tags=["interaction"])
                )

    def _persist(self) -> None:
        if self.persistence is None:
            return
        self.persistence.persist_runtime(
            self.state.emotional_drives,
            self.state.user_trust,
            self.state.user_familiarity,
            self.memory,
            only_dirty_memories=True,
        )

    def memory_context(self, *, for_speech: bool = False, user_message: str = "") -> str:
        if for_speech:
            return format_speech_memory_context(self.memory, user_message=user_message)
        facts = self.memory.all()[:8]
        if not facts:
            return "(no long-term memories yet)"
        lines = [
            "Facts you already know and should use when relevant:",
        ]
        for fact in facts:
            lines.append(f"- {fact.content}")
        return "\n".join(lines)
