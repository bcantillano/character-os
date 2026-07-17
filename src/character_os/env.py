"""Load project .env into process environment."""

from __future__ import annotations

from pathlib import Path


def load_env(start: Path | None = None) -> Path | None:
    """Load nearest .env file. Safe if python-dotenv is missing or file absent."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        env_path = candidate / ".env"
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return env_path
        # Stop at repo root (characters/ + worlds/).
        if (candidate / "characters").is_dir() and (candidate / "worlds").is_dir():
            break
    return None
