"""Entry point for cc-stt module — dispatches to listen or hook handler."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Route to subcommand: listen (default), hook, or file transcription."""
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        from cc_stt.hook_handler import should_auto_listen

        if should_auto_listen():
            print("auto-listen: enabled", file=sys.stderr)
        sys.exit(0)

    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1])
        if candidate.is_file():
            from cc_stt.listen import transcribe_file

            text = transcribe_file(str(candidate))
            print(text)
            return

    from cc_stt.listen import listen_live

    listen_live()


if __name__ == "__main__":
    main()
