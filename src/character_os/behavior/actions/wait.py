"""Wait action — no outward behavior."""

from __future__ import annotations

from character_os.events.types import IntentDecidedEvent


class WaitAction:
    intent_kind = "wait"

    def execute(self, event: IntentDecidedEvent) -> None:
        return
