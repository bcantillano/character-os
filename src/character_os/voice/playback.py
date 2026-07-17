"""Best-effort local playback for synthesized speech (Phase 1b CLI)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_player: subprocess.Popen[bytes] | None = None


def stop_audio() -> None:
    """Stop any in-progress background playback started by ``play_audio``."""
    global _player
    if _player is not None and _player.poll() is None:
        _player.terminate()
        try:
            _player.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            _player.kill()
    _player = None


def play_audio(path: Path, *, block: bool = False) -> bool:
    """Play an audio file if a system player is available.

    Non-blocking mode (default for CLI) starts playback in the background and
    stops any previous clip first so new replies can interrupt old ones.
    """
    global _player
    if path.suffix.lower() == ".txt":
        return False
    if not path.is_file():
        return False

    stop_audio()

    if sys.platform == "darwin" and shutil.which("afplay"):
        cmd = ["afplay", str(path)]
    elif shutil.which("ffplay"):
        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
    elif shutil.which("paplay"):
        cmd = ["paplay", str(path)]
    else:
        return False

    if block:
        subprocess.run(cmd, check=False)
        return True

    _player = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True
