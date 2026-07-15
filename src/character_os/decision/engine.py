"""Decision Engine — Decide (intent only)."""

from __future__ import annotations

from character_os.core.types import CharacterState, Intent, IntentKind
from character_os.events.bus import EventBus
from character_os.events.types import IntentDecidedEvent, StateChangedEvent


class DecisionEngine:
    def __init__(
        self,
        bus: EventBus,
        get_state,
        character_id: str,
        session_id: str,
    ) -> None:
        self.bus = bus
        self.get_state = get_state
        self.character_id = character_id
        self.session_id = session_id

    def wire(self) -> None:
        self.bus.subscribe(StateChangedEvent, self.on_state_changed)

    def on_state_changed(self, event: StateChangedEvent) -> None:
        state: CharacterState = self.get_state()
        if event.trigger == "time_tick":
            intent = Intent(
                kind=IntentKind.UPDATE_STATE,
                reasoning="Idle tick — evolve internal state only (no unprompted speech).",
                source="tick",
            )
        else:
            # User-driven reflection → speak by default in Phase 1 CLI.
            goal = next((g.id for g in state.goals if g.status == "active"), None)
            intent = Intent(
                kind=IntentKind.SPEAK,
                goal_focus=goal,
                reasoning="User message received; engage in character.",
                source="user",
            )

        state.last_intent = intent
        self.bus.publish(
            IntentDecidedEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                intent=intent,
            )
        )
