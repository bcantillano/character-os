"""Best-effort local playback for synthesized speech (Phase 1b CLI)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path

_player: subprocess.Popen[bytes] | None = None
_queue: deque[Path] = deque()
_lock = threading.Lock()
_worker: threading.Thread | None = None
_generation = 0


def stop_audio() -> None:
    """Stop any in-progress playback and clear the queued clips."""
    global _player, _worker, _generation
    with _lock:
        _generation += 1
        _queue.clear()
        player = _player
        _player = None
        _worker = None
    if player is not None and player.poll() is None:
        player.terminate()
        try:
            player.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            player.kill()


def play_audio(path: Path, *, block: bool = False) -> bool:
    """Play an audio file if a system player is available.

    Non-blocking mode (default for CLI) starts playback in the background and
    stops any previous clip first so new replies can interrupt old ones.
    """
    if path.suffix.lower() == ".txt":
        return False
    if not path.is_file():
        return False

    if block:
        stop_audio()
        cmd = _player_cmd(path)
        if not cmd:
            return False
        subprocess.run(cmd, check=False)
        return True

    stop_audio()
    return enqueue_audio(path)


def enqueue_audio(path: Path) -> bool:
    """Append a clip to the sequential play queue (non-blocking, interruptible).

    Starts playback immediately if nothing is playing. Subsequent calls append
    and play when the current clip finishes. Call ``stop_audio`` to cancel.
    """
    global _worker
    if path.suffix.lower() == ".txt":
        return False
    if not path.is_file():
        return False
    if not _player_cmd(path):
        return False

    with _lock:
        _queue.append(path)
        gen = _generation
        need_worker = _worker is None or not _worker.is_alive()
        if need_worker:
            _worker = threading.Thread(
                target=_drain_queue,
                args=(gen,),
                name="character-os-audio-queue",
                daemon=True,
            )
            _worker.start()
    return True


def _drain_queue(gen: int) -> None:
    global _player, _worker
    while True:
        with _lock:
            if gen != _generation:
                _player = None
                if _worker is threading.current_thread():
                    _worker = None
                return
            if not _queue:
                _player = None
                if _worker is threading.current_thread():
                    _worker = None
                return
            path = _queue.popleft()
            cmd = _player_cmd(path)
            if not cmd:
                continue
            _player = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            player = _player
        player.wait()
        with _lock:
            if gen != _generation:
                if _worker is threading.current_thread():
                    _worker = None
                return
            if _player is player:
                _player = None


def _player_cmd(path: Path) -> list[str] | None:
    if sys.platform == "darwin" and shutil.which("afplay"):
        return ["afplay", str(path)]
    if shutil.which("ffplay"):
        return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
    if shutil.which("paplay"):
        return ["paplay", str(path)]
    return None


def queue_size() -> int:
    """Queued clips not yet started (test helper)."""
    with _lock:
        return len(_queue)
