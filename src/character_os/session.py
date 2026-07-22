"""Wire a character session onto the event bus."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from character_os.behavior.actions.speak import SpeakAction
from character_os.behavior.actions.update_state import UpdateStateAction
from character_os.behavior.actions.wait import WaitAction
from character_os.behavior.executor import BehaviorExecutor
from character_os.brain.emotion import format_relationship_stance
from character_os.brain.orchestrator import BrainOrchestrator
from character_os.brain.scheduler import DEFAULT_TICK_INTERVAL_SECONDS, BrainScheduler
from character_os.core.types import IntentKind
from character_os.decision.engine import DecisionEngine
from character_os.events.bus import EventBus
from character_os.events.registry import EventRegistry
from character_os.events.types import ResponseReadyEvent, UserMessageEvent
from character_os.interpreter.handler import ConversationInterpreter
from character_os.loader import PromptLoader, load_character, load_world
from character_os.llm import LLMProvider, create_provider
from character_os.persistence import create_persistence
from character_os.response.handler import ResponseGenerator


@dataclass
class SessionResult:
    text: str
    thoughts: str = ""
    audio_path: str = ""


class CharacterSession:
    """Owns one bus + lifecycle wiring for a character interaction."""

    def __init__(
        self,
        character_id: str = "captain-redbeard",
        llm: LLMProvider | None = None,
        provider_name: str | None = None,
        tick_interval_seconds: float = DEFAULT_TICK_INTERVAL_SECONDS,
        enable_scheduler: bool = False,
        data_dir: Path | None = None,
        persist: bool = True,
        debug_stages: bool = False,
        enable_tts: bool = False,
        tts_provider_name: str | None = None,
        tts_play: bool = False,
    ) -> None:
        self.character_id = character_id
        self.session_id = str(uuid4())
        self.bus = EventBus()
        self.registry = EventRegistry(self.bus)
        if debug_stages:
            from character_os.debug import attach_stage_logger

            attach_stage_logger(self.bus)
        self.character = load_character(character_id)
        self.world = load_world(self.character.world)
        self.prompts = PromptLoader()
        self.llm = llm or create_provider(provider_name)
        self.provider_name = provider_name or type(self.llm).__name__
        self.last_response: SessionResult | None = None
        self._pending: SessionResult | None = None
        self.last_audio_path: Path | None = None
        self.speak_voice = None

        self.persistence = create_persistence(self.character, data_dir=data_dir) if persist else None
        self.brain = BrainOrchestrator(
            self.bus,
            self.character,
            self.world,
            self.session_id,
            persistence=self.persistence,
        )
        self.scheduler = BrainScheduler(
            self.bus,
            character_id=self.character.id,
            session_id=self.session_id,
            interval_seconds=tick_interval_seconds,
        )

        interpreter = ConversationInterpreter(
            self.bus,
            self.prompts,
            self.llm,
            character_id=self.character.id,
            session_id=self.session_id,
            character_name=self.character.name,
            get_memory_context=self.brain.memory_context,
        )
        decision = DecisionEngine(
            self.bus,
            get_state=lambda: self.brain.state,
            character_id=self.character.id,
            session_id=self.session_id,
        )
        executor = BehaviorExecutor(
            self.bus, character_id=self.character.id, session_id=self.session_id
        )
        speak = SpeakAction(
            self.bus,
            self.prompts,
            self.llm,
            get_context=self._context,
            character_id=self.character.id,
            session_id=self.session_id,
            prompt_overrides=self.character.prompts,
        )
        executor.register(IntentKind.SPEAK, speak)
        executor.register(IntentKind.WAIT, WaitAction())
        executor.register(IntentKind.UPDATE_STATE, UpdateStateAction())

        response = ResponseGenerator(
            self.bus,
            self.prompts,
            self.llm,
            get_context=self._context,
            character_id=self.character.id,
            session_id=self.session_id,
            prompt_overrides=self.character.prompts,
        )

        interpreter.wire()
        self.brain.wire()
        decision.wire()
        executor.wire()
        response.wire()

        if enable_tts:
            from character_os.behavior.actions.speak_voice import SpeakVoiceAction
            from character_os.loader.paths import default_data_dir
            from character_os.voice import create_tts_provider

            root = data_dir or default_data_dir()
            audio_dir = root / "audio" / self.character.id / self.session_id
            # CLI/env provider overrides pack default; pack still supplies voice/model.
            tts_name = tts_provider_name or self.character.tts.provider
            self.speak_voice = SpeakVoiceAction(
                self.bus,
                create_tts_provider(tts_name),
                self.character.tts,
                audio_dir,
                character_id=self.character.id,
                session_id=self.session_id,
                play=tts_play,
                get_drives=lambda: self.brain.state.emotional_drives,
            )
            # Wire before session ResponseReady handler so SessionResult includes audio_path.
            self.speak_voice.wire()

        self.bus.subscribe(ResponseReadyEvent, self._on_response_ready)

        self.registry.register("interpreter", lambda bus: None)
        self.registry.register("brain", lambda bus: None)
        self.registry.register("decision", lambda bus: None)
        self.registry.register("behavior", lambda bus: None)
        self.registry.register("response", lambda bus: None)
        if enable_tts:
            self.registry.register("voice", lambda bus: None)

        if enable_scheduler:
            self.scheduler.start()

    def _on_response_ready(self, event: ResponseReadyEvent) -> None:
        audio = ""
        if self.speak_voice is not None and self.speak_voice.last_audio_path is not None:
            audio = str(self.speak_voice.last_audio_path)
            self.last_audio_path = self.speak_voice.last_audio_path
        self._pending = SessionResult(
            text=event.text,
            thoughts=event.thoughts,
            audio_path=audio,
        )
        self.last_response = self._pending

    def _context(self) -> dict:
        state = self.brain.state
        drives = ", ".join(f"{k}={v:.2f}" for k, v in state.emotional_drives.as_dict().items())
        goals = "\n".join(
            f"- ({g.priority}) {g.description}" for g in state.goals if g.status == "active"
        )
        knowledge_bits = []
        for entry in self.world.knowledge[:5]:
            knowledge_bits.append(f"- {entry.summary}")
        for entry in self.character.knowledge:
            knowledge_bits.append(f"- {entry.summary}")
        personality = (
            f"Traits: {', '.join(self.character.personality.traits)}. "
            f"Voice: {self.character.personality.voice}."
        )
        interp = state.last_interpretation
        interpretation = ""
        if interp:
            interpretation = (
                f"intent={interp.intent}; topics={interp.topics}; "
                f"tone={interp.emotional_tone}"
            )
        decision = ""
        if state.last_intent:
            decision = (
                f"{state.last_intent.kind.value}: {state.last_intent.reasoning} "
                f"(goal={state.last_intent.goal_focus})"
            )
        user_message = interp.raw_message if interp else ""

        memory_context = self.brain.memory_context()
        speech_memory = self.brain.memory_context(
            for_speech=True,
            user_message=user_message,
        )
        recent = self.brain.conversation.state.recent_turns[-6:]
        if recent:
            recent_dialogue = "\n".join(
                f"{'User' if t.get('role') == 'user' else self.character.name}: {t.get('text', '')}"
                for t in recent
            )
        else:
            recent_dialogue = "(none yet this session)"
        thought_vars = {
            "character_name": self.character.name,
            "character_description": self.character.description,
            "personality_summary": personality,
            "emotional_state": drives,
            "relationship_stance": format_relationship_stance(
                state.user_trust,
                state.user_familiarity,
            ),
            "active_goals": goals or "(none)",
            "interpretation": interpretation or "(none)",
            "decision": decision or "(none)",
            "memory_context": memory_context,
            "user_message": user_message,
            "recent_dialogue": recent_dialogue,
        }
        response_vars = {
            **thought_vars,
            "internal_thoughts": state.last_thoughts,
            "relevant_knowledge": "\n".join(knowledge_bits) or "(none)",
            "memory_context": speech_memory,
        }
        return {
            "thought_vars": thought_vars,
            "response_vars": response_vars,
            "state": state,
        }

    def send_message(self, text: str) -> SessionResult:
        self._pending = None
        self.bus.publish(
            UserMessageEvent(
                character_id=self.character.id,
                session_id=self.session_id,
                text=text,
            )
        )
        if self._pending is None:
            raise RuntimeError("Pipeline did not produce ResponseReadyEvent")
        return self._pending

    def tick(self) -> None:
        self.scheduler.tick_once()

    def reset(self) -> dict[str, int]:
        """Reset conversation, memories, drives, and relationship to pack defaults."""
        if self.speak_voice is not None:
            self.speak_voice.stop()
        self.last_response = None
        self._pending = None
        self.last_audio_path = None
        return self.brain.reset()

    def close(self) -> None:
        self.scheduler.stop()
        if self.speak_voice is not None:
            self.speak_voice.stop()
        if self.persistence is not None:
            self.persistence.close()
