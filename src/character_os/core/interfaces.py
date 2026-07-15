"""Shared interfaces for event and behavior handlers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from character_os.events.types import Event


@runtime_checkable
class EventHandler(Protocol):
    def handle(self, event: Event) -> None:
        """Handle a published event."""


@runtime_checkable
class BehaviorHandler(Protocol):
    intent_kind: str

    def execute(self, event: Event) -> None:
        """Execute a decided intent."""
