"""Conversation Interpreter — Observe → Interpret."""

from __future__ import annotations

import re

from character_os.core.types import Interpretation
from character_os.events.bus import EventBus
from character_os.events.types import InputInterpretedEvent, UserMessageEvent
from character_os.llm.provider import LLMMessage, LLMProvider
from character_os.loader.prompts import PromptLoader


class ConversationInterpreter:
    def __init__(
        self,
        bus: EventBus,
        prompts: PromptLoader,
        llm: LLMProvider,
        character_id: str,
        session_id: str,
        character_name: str,
    ) -> None:
        self.bus = bus
        self.prompts = prompts
        self.llm = llm
        self.character_id = character_id
        self.session_id = session_id
        self.character_name = character_name

    def wire(self) -> None:
        self.bus.subscribe(UserMessageEvent, self.on_user_message)

    def on_user_message(self, event: UserMessageEvent) -> None:
        template = self.prompts.load("conversation_interpreter")
        prompt = self.prompts.render(
            template,
            {
                "character_name": self.character_name,
                "user_message": event.text,
                "memory_context": "(none yet)",
            },
        )
        raw = self.llm.complete(
            [
                LLMMessage(role="system", content=prompt),
                LLMMessage(role="user", content=event.text),
            ],
            temperature=0.2,
        )
        interpretation = self._parse(raw, event.text)
        self.bus.publish(
            InputInterpretedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                interpretation=interpretation,
            )
        )

    def _parse(self, raw: str, message: str) -> Interpretation:
        fields = _parse_labeled_lines(raw)
        topics = [t.strip() for t in fields.get("topics", "").split(",") if t.strip()]
        facts = [t.strip() for t in fields.get("notable_facts", "").split(",") if t.strip()]
        if facts == ["none yet"]:
            facts = []
        return Interpretation(
            intent=fields.get("intent") or "converse",
            topics=topics or _heuristic_topics(message),
            emotional_tone=fields.get("emotional_tone") or "neutral",
            relationship_signals=fields.get("relationship_signals") or "",
            notable_facts=facts,
            raw_message=message,
        )


def _parse_labeled_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip().lower().replace(" ", "_")] = value.strip()
    return result


def _heuristic_topics(message: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']{4,}", message.lower())
    return words[:3]
