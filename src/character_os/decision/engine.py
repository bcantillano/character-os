"""Decision Engine — Decide (intent only)."""

from __future__ import annotations

from character_os.core.types import CharacterState, Goal, Intent, IntentKind
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
            goal = _pick_goal(state)
            curiosity = state.emotional_drives.curiosity
            trust = state.user_trust
            reasoning = (
                f"Engage user; focus goal={goal}; "
                f"curiosity={curiosity:.2f}; trust={trust:.2f}."
            )
            intent = Intent(
                kind=IntentKind.SPEAK,
                goal_focus=goal,
                reasoning=reasoning,
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


def _pick_goal(state: CharacterState) -> str | None:
    active = [g for g in state.goals if g.status == "active"]
    if not active:
        return None

    topics = " ".join(state.last_interpretation.topics).lower() if state.last_interpretation else ""
    message = (state.last_interpretation.raw_message if state.last_interpretation else "").lower()
    haystack = f"{topics} {message}"

    scored: list[tuple[int, Goal]] = []
    for goal in active:
        score = _priority_score(goal.priority)
        blob = f"{goal.id} {goal.description}".lower()
        if any(token in haystack for token in blob.split() if len(token) > 4):
            score += 3
        if "map" in haystack and "map" in blob:
            score += 4
        if "navy" in haystack and "navy" in blob:
            score += 4
        if state.user_familiarity < 0.25 and "stranger" in blob:
            score += 2
        scored.append((score, goal))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1].id


def _priority_score(priority: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(priority.lower(), 1)
