"""Entry point for cc-stt module — dispatches to listen, hook, or file transcription."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    """Route to subcommand: listen (default), hook, or file transcription.

    Positional argument `target` accepts:
      - "hook" — run the auto-listen hook handler and exit
      - any path to an audio file — transcribe and print
      - (omitted) — start live microphone listening (default)
    """
    parser = argparse.ArgumentParser(
        prog="cc_stt",
        description="Speech-to-text via Moonshine/Vosk for Claude Code.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help=(
            "'hook' to run the auto-listen hook check, "
            "or a path to an audio file to transcribe. "
            "Omit to start live microphone listening."
        ),
    )
    args = parser.parse_args()

    if args.target == "hook":
        from cc_stt.hook_handler import should_auto_listen

        if should_auto_listen():
            print("auto-listen: enabled", file=sys.stderr)
        sys.exit(0)

    if args.target:
        candidate = Path(args.target)
        if not candidate.is_file():
            print(
                f"cc_stt: target is neither 'hook' nor an existing file: {args.target}",
                file=sys.stderr,
            )
            sys.exit(2)

        from cc_stt.listen import transcribe_file

        text = transcribe_file(str(candidate))
        print(text)
        return

    from cc_stt.listen import listen_live

    listen_live()


if __name__ == "__main__":
    main()
