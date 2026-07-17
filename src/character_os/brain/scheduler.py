"""Publishes TimeTickEvent on an interval. Phase 1: state-only downstream."""

from __future__ import annotations

import threading
import time

from character_os.events.bus import EventBus
from character_os.events.types import TimeTickEvent

DEFAULT_TICK_INTERVAL_SECONDS = 30.0


class BrainScheduler:
    def __init__(
        self,
        bus: EventBus,
        character_id: str,
        session_id: str,
        interval_seconds: float = DEFAULT_TICK_INTERVAL_SECONDS,
    ) -> None:
        self.bus = bus
        self.character_id = character_id
        self.session_id = session_id
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._tick_index = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="brain-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval_seconds + 1)
            self._thread = None

    def tick_once(self) -> None:
        """Publish a single tick (useful in tests and controlled demos)."""
        self._tick_index += 1
        self.bus.publish(
            TimeTickEvent(
                character_id=self.character_id,
                session_id=self.session_id,
                tick_index=self._tick_index,
                interval_seconds=self.interval_seconds,
            )
        )

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self.tick_once()
