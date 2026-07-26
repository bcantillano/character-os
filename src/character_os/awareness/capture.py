"""Best-effort local mic capture for Phase 3 CLI push-to-talk."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def record_push_to_talk(output_path: Path) -> Path:
    """Record from the default mic until the user presses Enter.

    Uses ``ffmpeg`` when available (same spirit as TTS system playback).
    Raises ``RuntimeError`` with install guidance if ffmpeg is missing.
    """
    if not ffmpeg_available():
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg to use /listen, "
            "or pass --stt-file path/to/audio.wav instead."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    cmd = _record_cmd(output_path)
    print("[stt] Recording… press Enter to stop.", file=sys.stderr)
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        input()
    except EOFError:
        pass
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1.0)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(
            "Recording produced no audio. Check microphone permissions / ffmpeg device."
        )
    return output_path


def _record_cmd(output_path: Path) -> list[str]:
    """Build an ffmpeg capture command for the current platform."""
    path = str(output_path)
    if sys.platform == "darwin":
        # Default audio input device index 0 on macOS.
        return [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-i",
            ":0",
            "-ac",
            "1",
            "-ar",
            "16000",
            path,
        ]
    if sys.platform.startswith("linux"):
        return [
            "ffmpeg",
            "-y",
            "-f",
            "alsa",
            "-i",
            "default",
            "-ac",
            "1",
            "-ar",
            "16000",
            path,
        ]
    # Windows / other: try dshow default — may need user device name.
    return [
        "ffmpeg",
        "-y",
        "-f",
        "dshow",
        "-i",
        "audio=default",
        "-ac",
        "1",
        "-ar",
        "16000",
        path,
    ]
