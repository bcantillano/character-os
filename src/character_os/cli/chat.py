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
        "--no-persist",
        action="store_true",
        help="Disable SQLite persistence for this session",
    )
    args = parser.parse_args(argv)

    try:
        session = CharacterSession(
            character_id=args.character,
            provider_name=args.provider,
            tick_interval_seconds=args.tick_interval,
            enable_scheduler=args.enable_ticks and not args.once,
            persist=not args.no_persist,
        )
    except (ValueError, ImportError) as exc:
        print(f"Error starting session: {exc}", file=sys.stderr)
        return 1

    print(f"Character OS — chatting with {session.character.name}")
    print(f"World: {session.world.name}")
    print(f"Provider: {args.provider}")
    if args.once:
        print()
        try:
            result = session.send_message(args.once)
            if args.show_thoughts and result.thoughts:
                print(f"(thoughts) {result.thoughts}")
            print(f"{session.character.name}> {result.text}")
        finally:
            session.close()
        return 0

    print("Type a message. Commands: /quit  /tick  /state")
    print()

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
                s = session.brain.state
                print(f"[state] trust={s.user_trust:.2f} familiarity={s.user_familiarity:.2f}")
                print(f"[state] drives={s.emotional_drives.as_dict()}")
                print(f"[state] ticks={s.tick_count}")
                print(f"[state] memories:\n{session.brain.memory_context()}")
                continue

            result = session.send_message(line)
            if args.show_thoughts and result.thoughts:
                print(f"(thoughts) {result.thoughts}")
            print(f"{session.character.name}> {result.text}")
            print()
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
