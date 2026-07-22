"""Speak action — triggers thoughts → response pipeline."""

from __future__ import annotations

from character_os.events.types import IntentDecidedEvent, ThoughtsGeneratedEvent
from character_os.llm.provider import LLMMessage, LLMProvider
from character_os.loader.prompts import PromptLoader


class SpeakAction:
    intent_kind = "speak"

    def __init__(
        self,
        bus,
        prompts: PromptLoader,
        llm: LLMProvider,
        get_context,
        character_id: str,
        session_id: str,
        prompt_overrides: dict[str, str] | None = None,
    ) -> None:
        self.bus = bus
        self.prompts = prompts
        self.llm = llm
        self.get_context = get_context
        self.character_id = character_id
        self.session_id = session_id
        self.prompt_overrides = prompt_overrides or {}

    def execute(self, event: IntentDecidedEvent) -> None:
        ctx = self.get_context()
        template = self.prompts.load(
            "internal_thoughts",
            self.prompt_overrides.get("internal_thoughts"),
        )
        prompt = self.prompts.render(template, ctx["thought_vars"])
        thoughts = self.llm.complete(
            [
                LLMMessage(role="system", content=prompt),
                LLMMessage(role="user", content="Generate internal thoughts now."),
            ]
        )
        state = self.get_context().get("state")
        if state is not None:
            state.last_thoughts = thoughts
        self.bus.publish(
            ThoughtsGeneratedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                thoughts=thoughts,
                intent=event.intent,
            )
        )
