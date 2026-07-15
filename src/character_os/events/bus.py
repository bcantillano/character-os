"""Synchronous in-process event bus."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from character_os.events.types import Event

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=Event)
Handler = Callable[[Event], None]


class EventBus:
    """Publish/subscribe dispatcher. Handlers run synchronously in order."""

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[Handler]] = defaultdict(list)
        self._wildcard: list[Handler] = []
        self._history: list[Event] = []
        self._recording: bool = False

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    def subscribe_all(self, handler: Handler) -> None:
        self._wildcard.append(handler)

    def unsubscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:  # type: ignore[operator]
            handlers.remove(handler)  # type: ignore[arg-type]

    def publish(self, event: Event) -> None:
        if self._recording:
            self._history.append(event)

        # Exact type handlers, then wildcard.
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except Exception:
                logger.exception("Handler failed for %s", type(event).__name__)
                raise

        for handler in list(self._wildcard):
            try:
                handler(event)
            except Exception:
                logger.exception("Wildcard handler failed for %s", type(event).__name__)
                raise

    def clear(self) -> None:
        self._handlers.clear()
        self._wildcard.clear()

    def start_recording(self) -> None:
        self._recording = True
        self._history.clear()

    def stop_recording(self) -> list[Event]:
        self._recording = False
        history = list(self._history)
        self._history.clear()
        return history

    def handler_count(self, event_type: type[Event] | None = None) -> int:
        if event_type is None:
            return sum(len(h) for h in self._handlers.values()) + len(self._wildcard)
        return len(self._handlers.get(event_type, []))
