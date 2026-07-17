"""Text CLI — Phase 1 entry point.

Publishes UserMessageEvent and prints ResponseReadyEvent output.
"""

from __future__ import annotations

import argparse
import os
import sys

from character_os.brain.scheduler import DEFAULT_TICK_INTERVAL_SECONDS
from character_os.env import load_env
from character_os.session import CharacterSession


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def main(argv: list[str] | None = None) -> int:
    load_env()

    parser = argparse.ArgumentParser(description="Character OS text chat (Phase 1)")
    parser.add_argument(
        "--character",
        default=os.getenv("CHARACTER_OS_CHARACTER", "captain-redbeard"),
        help="Character pack id under characters/",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("CHARACTER_OS_LLM_PROVIDER", "stub"),
        choices=["stub", "openai"],
        help="LLM provider (default from CHARACTER_OS_LLM_PROVIDER or stub)",
    )
    parser.add_argument(
        "--once",
        metavar="MESSAGE",
        help="Send a single message and exit (useful for smoke tests)",
    )
    parser.add_argument(
        "--tick-interval",
        type=float,
        default=float(
            os.getenv(
                "CHARACTER_OS_TICK_INTERVAL_SECONDS",
                str(DEFAULT_TICK_INTERVAL_SECONDS),
            )
        ),
        help="Seconds between internal state ticks (default 30; no unprompted speech)",
    )
    parser.add_argument(
        "--enable-ticks",
        action="store_true",
        help="Run background TimeTickEvent scheduler (state-only)",
    )
    parser.add_argument(
        "--show-thoughts",
        action="store_true",
        help="Print internal thoughts for debugging",
    )
    parser.add_argument(
        "--debug-stages",
        action="store_true",
        default=_env_flag("CHARACTER_OS_DEBUG_STAGES"),
        help="Print Observe→Act stage lines on stderr (or CHARACTER_OS_DEBUG_STAGES=1)",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Disable SQLite persistence for this session",
    )
    parser.add_argument(
        "--tts",
        nargs="?",
        const="auto",
        default=None,
        metavar="PROVIDER",
        help="Enable Phase 1b TTS (optional provider: stub|openai; default from character.yaml / CHARACTER_OS_TTS_PROVIDER)",
    )
    parser.add_argument(
        "--tts-play",
        action="store_true",
        help="Play synthesized audio via system player (implies --tts)",
    )
    args = parser.parse_args(argv)

    enable_tts = args.tts is not None or args.tts_play or _env_flag("CHARACTER_OS_TTS")
    tts_provider_name: str | None = None
    if args.tts and args.tts != "auto":
        tts_provider_name = args.tts
    elif enable_tts and os.getenv("CHARACTER_OS_TTS_PROVIDER"):
        tts_provider_name = os.getenv("CHARACTER_OS_TTS_PROVIDER")

    try:
        session = CharacterSession(
            character_id=args.character,
            provider_name=args.provider,
            tick_interval_seconds=args.tick_interval,
            enable_scheduler=args.enable_ticks and not args.once,
            persist=not args.no_persist,
            debug_stages=args.debug_stages,
            enable_tts=enable_tts,
            tts_provider_name=tts_provider_name,
            tts_play=args.tts_play,
        )
    except (ValueError, ImportError) as exc:
        print(f"Error starting session: {exc}", file=sys.stderr)
        return 1

    print(f"Character OS — chatting with {session.character.name}")
    print(f"World: {session.world.name}")
    print(f"Provider: {args.provider}")
    if enable_tts:
        tts_label = tts_provider_name or session.character.tts.provider
        play_note = " + play" if args.tts_play else ""
        print(f"TTS: {tts_label}{play_note} (voice={session.character.tts.voice})")
    if args.once:
        print()
        try:
            result = session.send_message(args.once)
            if args.show_thoughts and result.thoughts:
                print(f"(thoughts) {result.thoughts}")
            print(f"{session.character.name}> {result.text}")
            if result.audio_path:
                print(f"[tts] {result.audio_path}")
        finally:
            session.close()
        return 0

    print(
        "Type a message. Commands: /quit  /tick  /state  /dedupe  "
        "/forget  /archive  /restore <n|id>"
    )
    print()
    archived_listing: list = []

    try:
        while True:
            try:
                line = input("You> ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue
            if line in {"/quit", "/exit", "/q"}:
                break
            if line == "/tick":
                session.tick()
                drives = session.brain.state.emotional_drives.as_dict()
                print(f"[tick] drives={drives}")
                continue
            if line == "/state":
                from character_os.brain.emotion import format_relationship_stance

                s = session.brain.state
                print(f"[state] trust={s.user_trust:.2f} familiarity={s.user_familiarity:.2f}")
                print(f"[state] rapport={format_relationship_stance(s.user_trust, s.user_familiarity)}")
                print(f"[state] drives={s.emotional_drives.as_dict()}")
                print(f"[state] ticks={s.tick_count}")
                print(f"[state] memories:\n{session.brain.memory_context()}")
                continue
            if line == "/dedupe":
                if session.persistence is None:
                    removed = session.brain.memory.dedupe()
                    print(f"[dedupe] removed {len(removed)} in-memory duplicate(s)")
                else:
                    removed = session.persistence.dedupe_memories()
                    session.brain.memory = session.persistence.load_memory_store()
                    print(f"[dedupe] removed {removed} duplicate row(s) from SQLite")
                print(f"[dedupe] memories:\n{session.brain.memory_context()}")
                continue
            if line == "/forget":
                if session.persistence is None:
                    forgotten = session.brain.memory.forget_stale()
                    print(f"[forget] archived {len(forgotten)} in-memory fact(s)")
                else:
                    forgotten = session.persistence.forget_stale_memories(session.brain.memory)
                    print(f"[forget] archived {forgotten} fact(s) to SQLite archive")
                print(f"[forget] active memories:\n{session.brain.memory_context()}")
                continue
            if line == "/archive":
                if session.persistence is None:
                    print("[archive] persistence disabled — no SQLite archive")
                    continue
                archived_listing = session.persistence.list_archived_memories()
                if not archived_listing:
                    print("[archive] (empty)")
                    continue
                for i, fact in enumerate(archived_listing, start=1):
                    short = fact.id[:8]
                    print(
                        f"[archive] {i}. {short}… imp={fact.importance:.2f} "
                        f"{fact.content[:80]}"
                    )
                continue
            if line.startswith("/restore"):
                parts = line.split(maxsplit=1)
                if len(parts) < 2 or not parts[1].strip():
                    print("[restore] usage: /restore <n|memory_id_prefix>")
                    continue
                if session.persistence is None:
                    print("[restore] persistence disabled — cannot restore")
                    continue
                token = parts[1].strip()
                memory_id = _resolve_archive_id(token, archived_listing, session)
                if memory_id is None:
                    print(f"[restore] no archived match for {token!r}")
                    continue
                restored = session.persistence.restore_archived_memory(memory_id)
                if restored is None:
                    print(f"[restore] failed for {memory_id}")
                    continue
                session.brain.memory = session.persistence.load_memory_store()
                print(
                    f"[restore] restored imp={restored.importance:.2f} "
                    f"{restored.content[:80]}"
                )
                print(f"[restore] active memories:\n{session.brain.memory_context()}")
                continue

            result = session.send_message(line)
            if args.show_thoughts and result.thoughts:
                print(f"(thoughts) {result.thoughts}")
            print(f"{session.character.name}> {result.text}")
            if result.audio_path:
                print(f"[tts] {result.audio_path}")
            print()
    finally:
        session.close()

    return 0


def _resolve_archive_id(token: str, listing: list, session: CharacterSession) -> str | None:
    """Resolve /restore arg to a full memory_id."""
    archived = listing or (
        session.persistence.list_archived_memories() if session.persistence else []
    )
    if not archived:
        return None
    if token.isdigit():
        idx = int(token)
        if 1 <= idx <= len(archived):
            return archived[idx - 1].id
        return None
    matches = [f for f in archived if f.id.startswith(token) or f.id == token]
    if len(matches) == 1:
        return matches[0].id
    return None


if __name__ == "__main__":
    sys.exit(main())
