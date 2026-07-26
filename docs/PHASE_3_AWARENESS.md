# Phase 3 — World Awareness

Phase 3 adds perception inputs that publish onto the same event bus as Phase 1 text chat. **STT ships first**; vision and richer context awareness follow.

## STT MVP

### Flow

```
mic / audio file
  → awareness STT provider (stub | openai Whisper)
  → SpeechRecognizedEvent          # Observe (speech)
  → SpeechInputBridge
  → UserMessageEvent               # shared Interpret → … → Remember path
```

Typed CLI input still publishes `UserMessageEvent` directly. Speech never bypasses the bus or calls interpreter/brain methods.

### CLI

| Flag / command | Role |
|----------------|------|
| `--stt [stub\|openai]` | Enable STT provider |
| `--stt-file PATH` | Transcribe one file and exit (`.txt` works with stub) |
| `/listen` | Push-to-talk when STT is enabled (`ffmpeg` for real mic; stub needs no mic) |
| `CHARACTER_OS_STT=1` | Env enable |
| `CHARACTER_OS_STT_PROVIDER` | `stub` (default) or `openai` |
| `CHARACTER_OS_STT_MODEL` | Whisper model (default `whisper-1`) |

Examples:

```bash
# Stub smoke (no API, no mic)
character-os --character lumen --provider stub --stt stub --stt-file /tmp/said.txt --no-persist

# OpenAI Whisper + push-to-talk (needs OPENAI_API_KEY + ffmpeg)
character-os --character lumen --provider openai --stt openai --tts-play --show-thoughts
# then type: /listen
```

### Layout

```
src/character_os/awareness/
  provider.py          # STTProvider + factory
  bridge.py            # SpeechRecognizedEvent → UserMessageEvent
  capture.py           # ffmpeg push-to-talk helper
  providers/
    stub.py
    openai.py
```

### Out of scope (later Phase 3)

- Continuous always-on listening / VAD polish
- `VisionDetectedEvent` / sensors
- Local offline Whisper models
