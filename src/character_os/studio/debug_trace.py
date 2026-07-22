"""One-shot lifecycle stage traces for Studio debugging."""

from __future__ import annotations

from dataclasses import dataclass, field

from character_os.debug.stages import format_stage_line
from character_os.session import CharacterSession, SessionResult


@dataclass
class StageTraceResult:
    character_id: str
    user_message: str
    reply: str
    thoughts: str
    stages: list[dict[str, str]] = field(default_factory=list)
    provider: str = "stub"

    def as_dict(self) -> dict[str, object]:
        return {
            "character_id": self.character_id,
            "user_message": self.user_message,
            "reply": self.reply,
            "thoughts": self.thoughts,
            "provider": self.provider,
            "stages": list(self.stages),
        }


def run_stage_trace(
    character_id: str,
    message: str,
    *,
    provider_name: str = "stub",
    persist: bool = False,
    characters_dir=None,
) -> StageTraceResult:
    """Run one user message through the pipeline and capture stage lines.

    Uses bus recording (not subscribe_all) so nested publish cascades still
    yield Observe → Interpret → … order.
    """
    # characters_dir is reserved for future Studio root overrides; session uses repo loaders.
    _ = characters_dir

    session = CharacterSession(
        character_id=character_id,
        provider_name=provider_name,
        enable_scheduler=False,
        persist=persist,
        enable_tts=False,
        debug_stages=False,
    )
    session.bus.start_recording()
    try:
        result: SessionResult = session.send_message(message)
        history = session.bus.stop_recording()
    finally:
        session.close()

    stages: list[dict[str, str]] = []
    for event in history:
        line = format_stage_line(event)
        if not line:
            continue
        body = line[len("[stage:") :] if line.startswith("[stage:") else line
        if "]" in body:
            label, _, detail = body.partition("]")
            stages.append({"stage": label.strip(), "detail": detail.strip()})
        else:
            stages.append({"stage": body.strip(), "detail": ""})

    return StageTraceResult(
        character_id=character_id,
        user_message=message,
        reply=result.text,
        thoughts=result.thoughts,
        stages=stages,
        provider=provider_name,
    )
