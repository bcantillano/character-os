"""Load Markdown prompt templates and render {{variables}}."""

from __future__ import annotations

import re
from pathlib import Path

from character_os.loader.paths import default_prompts_dir, find_repo_root

_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class PromptLoader:
    def __init__(self, prompts_dir: Path | None = None, repo_root: Path | None = None):
        self.repo_root = repo_root or find_repo_root()
        self.prompts_dir = prompts_dir or default_prompts_dir(self.repo_root)

    def load(self, name: str, override_path: str | None = None) -> str:
        if override_path:
            path = Path(override_path)
            if not path.is_absolute():
                path = self.repo_root / path
        else:
            filename = name if name.endswith(".md") else f"{name}.md"
            path = self.prompts_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Prompt not found: {path}")
        return path.read_text(encoding="utf-8")

    def render(self, template: str, variables: dict[str, str]) -> str:
        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return variables.get(key, match.group(0))

        return _VAR.sub(repl, template)

    def load_and_render(
        self,
        name: str,
        variables: dict[str, str],
        override_path: str | None = None,
    ) -> str:
        return self.render(self.load(name, override_path), variables)
