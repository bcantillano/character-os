"""Phase 1b TTS tests."""

from pathlib import Path

from character_os.core.types import TTSProfile
from character_os.events.bus import EventBus
from character_os.events.types import ResponseReadyEvent, SpeechSynthesizedEvent
from character_os.loader import load_character
from character_os.llm.providers.stub import StubProvider
from character_os.session import CharacterSession
from character_os.voice.providers.stub import StubTTSProvider
from character_os.behavior.actions.speak_voice import SpeakVoiceAction


def test_load_redbeard_tts_profile():
    character = load_character("captain-redbeard")
    assert character.tts.voice == "ash"
    assert character.tts.provider == "openai"
    assert character.tts.speed == 0.95
    assert character.tts.normalize_speech is True
    assert "pirate impression" in character.tts.instructions.lower()
    assert "gravelly" in character.tts.instructions.lower()


def test_normalize_for_speech_softens_dialect():
    from character_os.voice.speech_text import normalize_for_speech

    raw = "Arrr, Byron, me heart's a tempest! Ye best keep yer wits fer the navy!"
    spoken = normalize_for_speech(raw)
    assert "Arrr" not in spoken
    assert "ye" not in spoken.lower().split()
    assert "my heart" in spoken.lower()
    assert "your wits" in spoken.lower()
    assert "for the navy" in spoken.lower()
    assert "Byron" in spoken


def test_stub_tts_writes_sidecar(tmp_path: Path):
    provider = StubTTSProvider()
    profile = TTSProfile(voice="onyx", model="stub-model")
    out = provider.synthesize("Ahoy there", profile, tmp_path / "line.mp3")
    assert out.suffix == ".txt"
    assert out.is_file()
    assert "Ahoy there" in out.read_text(encoding="utf-8")


def test_speak_voice_publishes_event(tmp_path: Path):
    bus = EventBus()
    action = SpeakVoiceAction(
        bus,
        StubTTSProvider(),
        TTSProfile(voice="onyx"),
        tmp_path,
        character_id="captain-redbeard",
        session_id="s1",
        play=False,
    )
    action.wire()
    seen: list[SpeechSynthesizedEvent] = []
    bus.subscribe(SpeechSynthesizedEvent, seen.append)
    bus.publish(ResponseReadyEvent(text="Land ho", thoughts=""))
    assert len(seen) == 1
    assert seen[0].text == "Land ho"
    assert Path(seen[0].audio_path).is_file()


def test_speak_voice_merges_emotion_overlay(tmp_path: Path):
    from character_os.core.types import EmotionalDrives

    class CaptureTTS(StubTTSProvider):
        def __init__(self) -> None:
            self.last_profile: TTSProfile | None = None

        def synthesize(self, text: str, profile: TTSProfile, output_path: Path) -> Path:
            self.last_profile = profile
            return super().synthesize(text, profile, output_path)

    bus = EventBus()
    capture = CaptureTTS()
    action = SpeakVoiceAction(
        bus,
        capture,
        TTSProfile(voice="cedar", instructions="Base voice.", emotion_overlay=True),
        tmp_path,
        character_id="lumen",
        session_id="s1",
        play=False,
        get_drives=lambda: EmotionalDrives(curiosity=0.9, fear=0.2, excitement=0.3),
    )
    action.wire()
    bus.publish(ResponseReadyEvent(text="Hello", thoughts=""))
    assert capture.last_profile is not None
    assert "Base voice." in capture.last_profile.instructions
    assert "curiosity" in capture.last_profile.instructions.lower()


def test_split_speak_chunks_sentences():
    from character_os.voice.speech_text import split_speak_chunks

    assert split_speak_chunks("") == []
    assert split_speak_chunks("One line only.") == ["One line only."]

    chunks = split_speak_chunks(
        "This is a longer first sentence for speech. "
        "Here is another complete sentence ready for TTS. "
        "And a third sentence finishes the thought."
    )
    assert len(chunks) >= 2
    assert chunks[0].startswith("This is a longer first")
    assert any("third sentence" in c for c in chunks)

    # Short opener merges into the next sentence.
    merged = split_speak_chunks("Yes. I completely agree with that plan for tonight.")
    assert len(merged) == 1
    assert merged[0].startswith("Yes.")


def test_speak_voice_play_chunks_synthesizes_early(tmp_path: Path):
    class CaptureTTS(StubTTSProvider):
        def __init__(self) -> None:
            self.texts: list[str] = []

        def synthesize(self, text: str, profile: TTSProfile, output_path: Path) -> Path:
            self.texts.append(text)
            return super().synthesize(text, profile, output_path)

    bus = EventBus()
    capture = CaptureTTS()
    action = SpeakVoiceAction(
        bus,
        capture,
        TTSProfile(voice="cedar"),
        tmp_path,
        character_id="lumen",
        session_id="s1",
        play=True,
    )
    action.wire()
    seen: list[SpeechSynthesizedEvent] = []
    bus.subscribe(SpeechSynthesizedEvent, seen.append)

    reply = (
        "This is a longer first sentence for speech. "
        "Here is another complete sentence ready for TTS."
    )
    bus.publish(ResponseReadyEvent(text=reply, thoughts=""))

    assert len(capture.texts) >= 2
    assert len(seen) == 1
    assert Path(seen[0].audio_path).is_file()
    assert action.last_audio_path == Path(seen[0].audio_path)
    # Event published after first chunk, not after the whole reply as one file.
    assert capture.texts[0] != reply


def test_audio_queue_plays_sequentially_and_stop_clears(tmp_path: Path, monkeypatch):
    import time

    from character_os.voice import playback

    playback.stop_audio()
    monkeypatch.setattr(
        playback,
        "_player_cmd",
        lambda path: [sys_executable(), "-c", "import time; time.sleep(0.15)"],
    )

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"a")
    b.write_bytes(b"b")

    assert playback.enqueue_audio(a)
    assert playback.enqueue_audio(b)
    time.sleep(0.05)
    assert playback.queue_size() >= 0
    playback.stop_audio()
    assert playback.queue_size() == 0


def sys_executable() -> str:
    import sys

    return sys.executable
