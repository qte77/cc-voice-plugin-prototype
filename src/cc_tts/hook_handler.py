"""Stop hook handler for auto-read mode.

This hook fires on EVERY Claude response (registered as a Stop hook in
.claude/settings.json). It is intentionally always-registered rather than
dynamically added/removed because CC hooks don't hot-reload — they require
a session restart to take effect.

The cost is negligible when auto_read = false (the default): the handler
loads config, sees auto_read is off, and exits immediately (~200ms Python
startup, no audio processing). Only when auto_read = true does it extract
the assistant's response and speak it.

Performance: the handler forks immediately after extracting the text. The
parent exits (~100ms) so CC unblocks and accepts the next user input. The
child process synthesizes and plays audio in the background. This means
the user can type while the previous response is still being spoken.

Latency: batch mode — speaks AFTER the full response is generated, not
during. For streaming TTS (sentence-by-sentence as Claude types), use the
PTY wrapper instead: `make run_voice_stream` / `cc-tts-wrap claude`. Do
not enable both simultaneously or you'll get double speaking.
"""

from __future__ import annotations

import json
import os
import sys

from cc_tts.config import load_config
from cc_tts.speak import synthesize_and_play


def extract_assistant_text(stdin_data: str) -> str:
    """Extract the last assistant message from CC Stop hook JSON payload.

    CC sends: {"last_assistant_message": "...", "session_id": "...", ...}
    """
    try:
        payload = json.loads(stdin_data)
    except (json.JSONDecodeError, TypeError):
        return ""

    return str(payload.get("last_assistant_message", ""))


def main() -> None:
    """Entry point for the Stop hook. Reads stdin, speaks if auto_read enabled.

    Forks after extracting text: parent exits immediately so CC unblocks,
    child synthesizes and plays in background.
    """
    config = load_config()
    if not config.auto_read:
        return

    stdin_data = sys.stdin.read()
    text = extract_assistant_text(stdin_data)
    if not text:
        return

    # Fork: parent returns immediately (CC unblocks), child speaks in background.
    pid = os.fork()
    if pid != 0:
        return

    # Child process: synthesize and play, then exit.
    try:
        synthesize_and_play(text, config=config)
    except Exception:
        pass  # noqa: S110 — child must not propagate exceptions to CC
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()
