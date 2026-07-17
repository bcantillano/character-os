"""Update-state action for time ticks — never speaks in Phase 1 CLI."""

from __future__ import annotations

import logging

from character_os.events.types import IntentDecidedEvent

logger = logging.getLogger(__name__)


class UpdateStateAction:
    intent_kind = "update_state"

    def execute(self, event: IntentDecidedEvent) -> None:
        # Orchestrator already applied tick updates during Reflect.
        # This action exists so Act remains explicit without producing dialogue.
        logger.debug("update_state for tick; no speech emitted")
