"""Allow running as python -m cc_tts [speak|wrap]."""

import sys


def _main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "wrap":
        sys.argv = sys.argv[1:]  # shift so pty_proxy sees ["wrap", "claude", ...]
        from cc_tts.pty_proxy import main

        main()
    else:
        from cc_tts.speak import main

        main()


_main()
