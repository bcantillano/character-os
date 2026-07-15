"""Conversation Interpreter — Observe → Interpret."""

from __future__ import annotations

import re
from collections.abc import Callable

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
        get_memory_context: Callable[[], str] | None = None,
    ) -> None:
        self.bus = bus
        self.prompts = prompts
        self.llm = llm
        self.character_id = character_id
        self.session_id = session_id
        self.character_name = character_name
        self.get_memory_context = get_memory_context or (lambda: "(none yet)")

    def wire(self) -> None:
        self.bus.subscribe(UserMessageEvent, self.on_user_message)

    def on_user_message(self, event: UserMessageEvent) -> None:
        template = self.prompts.load("conversation_interpreter")
        prompt = self.prompts.render(
            template,
            {
                "character_name": self.character_name,
                "user_message": event.text,
                "memory_context": self.get_memory_context(),
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
        interpretation.notable_facts = [
            _canonicalize_fact(f) for f in interpretation.notable_facts
        ]
        self.bus.publish(
            InputInterpretedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                interpretation=interpretation,
            )
        )

    def _parse(self, raw: str, message: str) -> Interpretation:
        fields = _parse_labeled_lines(raw)
        topics = _split_list(fields.get("topics", ""))
        facts = _split_facts(fields.get("notable_facts", ""))
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
        # Allow "1. intent: ..." or "**intent**: ..."
        cleaned = re.sub(r"^\s*\d+\.\s*", "", line)
        cleaned = cleaned.replace("*", "").strip()
        if ":" not in cleaned:
            continue
        key, value = cleaned.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        if key:
            result[key] = value.strip()
    return result


def _split_list(raw: str) -> list[str]:
    if not raw or raw.lower() in {"none", "n/a", "none yet"}:
        return []
    parts = re.split(r"[,;]", raw)
    return [p.strip() for p in parts if p.strip()]


def _split_facts(raw: str) -> list[str]:
    if not raw or raw.lower() in {"none", "n/a", "none yet", "nothing"}:
        return []
    # Prefer semicolons; also accept newlines / bullets.
    chunks = re.split(r"[;\n]", raw)
    facts: list[str] = []
    for chunk in chunks:
        item = re.sub(r"^\s*[-*]\s*", "", chunk).strip()
        if item and item.lower() not in {"none", "n/a"}:
            facts.append(item)
    if len(facts) == 1 and "," in facts[0] and len(facts[0]) < 80:
        # short comma list of simple facts
        return [p.strip() for p in facts[0].split(",") if p.strip()]
    return facts


def _heuristic_topics(message: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']{4,}", message.lower())
    return words[:3]


def _canonicalize_fact(fact: str) -> str:
    """Normalize common fact labels into clear declarative form."""
    text = fact.strip()
    lowered = text.lower()
    if lowered.startswith("name:"):
        return f"The user's name is {text.split(':', 1)[1].strip()}"
    if lowered.startswith("preference:") or lowered.startswith("prefers:"):
        return f"The user {text.split(':', 1)[1].strip()}"
    if lowered.startswith("preference for"):
        return f"The user has a {text}"
    return text
