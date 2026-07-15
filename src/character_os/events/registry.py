"""Handler registration helpers for wiring the lifecycle pipeline."""

from __future__ import annotations

from character_os.events.bus import EventBus


class EventRegistry:
    """Collects and applies module subscriptions onto an EventBus."""

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._wired: list[str] = []

    def register(self, name: str, wire_fn) -> None:
        """Call wire_fn(bus) and record the module name."""
        wire_fn(self.bus)
        self._wired.append(name)

    @property
    def wired_modules(self) -> list[str]:
        return list(self._wired)
