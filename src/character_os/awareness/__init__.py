"""Phase 3 world awareness — STT first; vision/sensors later."""

from character_os.awareness.bridge import SpeechInputBridge
from character_os.awareness.provider import STTProvider, create_stt_provider

__all__ = ["STTProvider", "SpeechInputBridge", "create_stt_provider"]
