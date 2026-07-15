"""Event bus unit tests."""

from character_os.events.bus import EventBus
from character_os.events.types import TimeTickEvent, UserMessageEvent


def test_publish_delivers_to_subscriber():
    bus = EventBus()
    received = []

    def handler(event: UserMessageEvent) -> None:
        received.append(event.text)

    bus.subscribe(UserMessageEvent, handler)
    bus.publish(UserMessageEvent(text="ahoy", character_id="captain-redbeard"))

    assert received == ["ahoy"]


def test_handlers_are_type_specific():
    bus = EventBus()
    user_hits = []
    tick_hits = []

    bus.subscribe(UserMessageEvent, lambda e: user_hits.append(e))
    bus.subscribe(TimeTickEvent, lambda e: tick_hits.append(e))

    bus.publish(UserMessageEvent(text="hi"))
    bus.publish(TimeTickEvent(tick_index=1))

    assert len(user_hits) == 1
    assert len(tick_hits) == 1


def test_recording_history():
    bus = EventBus()
    bus.start_recording()
    bus.publish(UserMessageEvent(text="one"))
    bus.publish(TimeTickEvent(tick_index=1))
    history = bus.stop_recording()
    assert len(history) == 2
    assert isinstance(history[0], UserMessageEvent)
