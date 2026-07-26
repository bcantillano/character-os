"""Phase 3 STT tests."""

from pathlib import Path

from character_os.awareness.bridge import SpeechInputBridge
from character_os.awareness.providers.stub import StubSTTProvider
from character_os.events.bus import EventBus
from character_os.events.types import (
    ResponseReadyEvent,
    SpeechRecognizedEvent,
    UserMessageEvent,
)
from character_os.llm.providers.stub import StubProvider
from character_os.session import CharacterSession


def test_stub_stt_reads_txt(tmp_path: Path):
    path = tmp_path / "utterance.txt"
    path.write_text("Ahoy from a text fixture\n", encoding="utf-8")
    assert StubSTTProvider().transcribe(path) == "Ahoy from a text fixture"


def test_stub_stt_default_for_non_txt(tmp_path: Path):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"not-real-audio")
    assert StubSTTProvider().transcribe(path) == StubSTTProvider().default_transcript


def test_speech_bridge_publishes_user_message():
    bus = EventBus()
    SpeechInputBridge(bus).wire()
    seen: list[UserMessageEvent] = []
    bus.subscribe(UserMessageEvent, seen.append)
    bus.publish(
        SpeechRecognizedEvent(
            character_id="c1",
            session_id="s1",
            text="Hello captain",
            provider="stub",
        )
    )
    assert len(seen) == 1
    assert seen[0].text == "Hello captain"
    assert seen[0].character_id == "c1"


def test_speech_recognized_pipeline(tmp_path: Path):
    session = CharacterSession(
        llm=StubProvider(),
        enable_scheduler=False,
        persist=False,
        enable_stt=True,
        stt_provider_name="stub",
        data_dir=tmp_path,
    )
    session.bus.start_recording()
    result = session.send_speech("Ahoy there, captain!", provider="stub")
    history = session.bus.stop_recording()
    session.close()

    types = [type(e) for e in history]
    assert SpeechRecognizedEvent in types
    assert UserMessageEvent in types
    assert ResponseReadyEvent in types
    assert result.text
    assert session.last_stt_transcript == "Ahoy there, captain!"


def test_send_audio_stub_txt(tmp_path: Path):
    fixture = tmp_path / "said.txt"
    fixture.write_text("I brought flatbread\n", encoding="utf-8")
    session = CharacterSession(
        character_id="lumen",
        llm=StubProvider(),
        enable_scheduler=False,
        persist=False,
        enable_stt=True,
        stt_provider_name="stub",
        data_dir=tmp_path / "data",
    )
    result = session.send_audio(fixture)
    session.close()
    assert "flatbread" in session.last_stt_transcript.lower()
    assert result.text
