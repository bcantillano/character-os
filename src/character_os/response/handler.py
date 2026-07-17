"""Response Generator — dialogue after thoughts."""

from __future__ import annotations

from character_os.events.bus import EventBus
from character_os.events.types import ResponseReadyEvent, ThoughtsGeneratedEvent
from character_os.llm.provider import LLMMessage, LLMProvider
from character_os.loader.prompts import PromptLoader


class ResponseGenerator:
    def __init__(
        self,
        bus: EventBus,
        prompts: PromptLoader,
        llm: LLMProvider,
        get_context,
        character_id: str,
        session_id: str,
        on_response=None,
    ) -> None:
        self.bus = bus
        self.prompts = prompts
        self.llm = llm
        self.get_context = get_context
        self.on_response = on_response
        self.character_id = character_id
        self.session_id = session_id

    def wire(self) -> None:
        self.bus.subscribe(ThoughtsGeneratedEvent, self.on_thoughts)

    def on_thoughts(self, event: ThoughtsGeneratedEvent) -> None:
        ctx = self.get_context()
        vars_ = dict(ctx["response_vars"])
        vars_["internal_thoughts"] = event.thoughts
        template = self.prompts.load("response_generator")
        prompt = self.prompts.render(template, vars_)
        text = self.llm.complete(
            [
                LLMMessage(role="system", content=prompt),
                LLMMessage(
                    role="user",
                    content=vars_.get("user_message", "Continue the conversation."),
                ),
            ]
        )
        if self.on_response is not None:
            self.on_response(text)
        self.bus.publish(
            ResponseReadyEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                text=text,
                thoughts=event.thoughts,
            )
        )
