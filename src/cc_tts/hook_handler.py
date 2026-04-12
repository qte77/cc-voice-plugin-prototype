"""Stop hook handler for auto-read mode.

This hook fires on EVERY Claude response (registered as a Stop hook in
hooks/hooks.json via the cc-voice plugin). It is intentionally always-registered rather than
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
import sys

from cc_tts.config import load_config


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

    Graceful no-op when deps are missing (team members without TTS setup).
    """
    try:
        config = load_config()
    except Exception:
        # Config or TTS modules not available — deps not installed.
        return

    if not config.auto_read:
        return

    stdin_data = sys.stdin.read()
    text = extract_assistant_text(stdin_data)
    if not text:
        return

    # Launch TTS in a detached subprocess so CC can't kill it when the
    # hook shell exits. os.fork() doesn't work here because CC kills the
    # entire process group on hook completion — the forked child dies
    # before it can synthesize audio. subprocess.Popen with
    # start_new_session=True creates an independent session/process group.
    import shutil
    import subprocess

    if shutil.which("uv") is None:
        return

    try:
        subprocess.Popen(
            ["uv", "run", "python", "-m", "cc_tts.speak", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return


if __name__ == "__main__":
    main()
