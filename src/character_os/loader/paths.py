"""Path helpers for content and data roots."""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from start (or this file) until characters/ and worlds/ exist."""
    here = start or Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "characters").is_dir() and (candidate / "worlds").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate repository root (expected characters/ and worlds/)."
    )


def default_characters_dir(root: Path | None = None) -> Path:
    return (root or find_repo_root()) / "characters"


def default_worlds_dir(root: Path | None = None) -> Path:
    return (root or find_repo_root()) / "worlds"


def default_prompts_dir(root: Path | None = None) -> Path:
    return (root or find_repo_root()) / "prompts"


def default_data_dir(root: Path | None = None) -> Path:
    return (root or find_repo_root()) / "data"
