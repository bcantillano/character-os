"""Deterministic stub LLM for offline development and tests."""

from __future__ import annotations

from character_os.llm.provider import LLMMessage, LLMProvider


class StubProvider(LLMProvider):
    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.7) -> str:
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        system = next((m.content for m in messages if m.role == "system"), "")
        system_l = system.lower()

        # Order matters — response_generator.md mentions "Internal Thoughts" as a section.
        if system.lstrip().startswith("# Response Generator") or "spoken dialogue" in system_l:
            snippet = user.strip()[:80] if user else "silence"
            return (
                f"Aye, I hear ye. Ye speak of '{snippet}'... "
                "The sea keeps her secrets, and so do I. What business brings ye near my cove?"
            )

        if system.lstrip().startswith("# Internal Thoughts") or (
            "private internal monologue" in system_l
        ):
            return (
                "That stranger speaks bold. I do not trust them yet, but I am curious. "
                "Maybe they know something about the map. Steady now — do not give too much away."
            )

        if system.lstrip().startswith("# Decision Engine") or "primary_action" in system_l:
            return (
                "primary_action: engage\n"
                "goal_focus: size_up_stranger\n"
                "emotional_shift: curiosity up slightly\n"
                "trust_delta: 0\n"
                "reasoning: Newcomer may be useful; stay guarded."
            )

        if system.lstrip().startswith("# Conversation Interpreter"):
            return (
                "intent: greet_or_converse\n"
                "topics: stranger, introduction\n"
                "emotional_tone: curious\n"
                "relationship_signals: unfamiliar\n"
                "notable_facts: none yet"
            )

        snippet = user.strip()[:80] if user else "silence"
        return (
            f"Aye, I hear ye. Ye speak of '{snippet}'... "
            "The sea keeps her secrets, and so do I. What business brings ye near my cove?"
        )
