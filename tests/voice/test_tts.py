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


def test_session_tts_stub_attaches_audio_path(tmp_path: Path):
    session = CharacterSession(
        llm=StubProvider(),
        persist=False,
        data_dir=tmp_path,
        enable_tts=True,
        tts_provider_name="stub",
        tts_play=False,
    )
    result = session.send_message("Hello captain")
    assert result.text
    assert result.audio_path
    assert Path(result.audio_path).is_file()
    session.close()
