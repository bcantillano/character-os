"""Behavior Executor — Act."""

from __future__ import annotations

from character_os.core.types import IntentKind
from character_os.events.bus import EventBus
from character_os.events.types import BehaviorRequestedEvent, IntentDecidedEvent


class BehaviorExecutor:
    def __init__(self, bus: EventBus, character_id: str, session_id: str) -> None:
        self.bus = bus
        self.character_id = character_id
        self.session_id = session_id
        self._actions: dict[IntentKind, object] = {}

    def register(self, kind: IntentKind, action) -> None:
        self._actions[kind] = action

    def wire(self) -> None:
        self.bus.subscribe(IntentDecidedEvent, self.on_intent)

    def on_intent(self, event: IntentDecidedEvent) -> None:
        if not event.intent:
            return
        self.bus.publish(
            BehaviorRequestedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                intent=event.intent,
            )
        )
        action = self._actions.get(event.intent.kind)
        if action is None:
            return
        action.execute(event)
