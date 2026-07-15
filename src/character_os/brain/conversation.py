"""Session-only conversation state."""

from __future__ import annotations

from character_os.core.types import ConversationState


class ConversationStore:
    def __init__(self) -> None:
        self._state = ConversationState()

    @property
    def state(self) -> ConversationState:
        return self._state

    def reset(self) -> None:
        self._state = ConversationState()
