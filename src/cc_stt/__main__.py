"""Entry point for cc-stt module — dispatches to listen or hook handler."""

from __future__ import annotations

import sys


def main() -> None:
    """Route to subcommand: listen (default) or hook."""
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        from cc_stt.hook_handler import should_auto_listen

        if should_auto_listen():
            print("auto-listen: enabled", file=sys.stderr)
        sys.exit(0)

    print("cc-stt: listen mode not yet implemented", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
