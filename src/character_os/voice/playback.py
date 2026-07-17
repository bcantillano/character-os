"""Best-effort local playback for synthesized speech (Phase 1b CLI)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def play_audio(path: Path) -> bool:
    """Play an audio file if a system player is available. Returns True if started."""
    if path.suffix.lower() == ".txt":
        return False
    if not path.is_file():
        return False

    if sys.platform == "darwin" and shutil.which("afplay"):
        subprocess.run(["afplay", str(path)], check=False)
        return True
    if shutil.which("ffplay"):
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            check=False,
        )
        return True
    if shutil.which("paplay"):
        subprocess.run(["paplay", str(path)], check=False)
        return True
    return False
