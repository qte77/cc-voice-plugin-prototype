"""Bidirectional stream-json REPL with TTS — interactive Claude without PTY."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading

from cc_tts.config import load_config
from cc_tts.edge_stream import speak_streaming
from cc_tts.speak import _stop_playback  # pyright: ignore[reportPrivateUsage]
from cc_tts.stream_json import parse_stream_event

_LOCAL_COMMANDS = {"exit", "stop", "toggle"}


def parse_local_command(text: str) -> str | None:
    """Return local command name if text is a local slash command, else None."""
    stripped = text.strip()
    if stripped.startswith("/"):
        cmd = stripped[1:].split()[0].lower() if stripped[1:] else ""
        if cmd in _LOCAL_COMMANDS:
            return cmd
    return None


def format_user_message(text: str) -> str:
    """Format user text as a stream-json user message."""
    return json.dumps({
        "type": "user",
        "message": {"role": "user", "content": text},
    })


def main() -> None:
    """REPL loop: user input → claude stdin (JSON) → read deltas → print + TTS."""
    if shutil.which("claude") is None:
        print("Error: 'claude' CLI not found on PATH.", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    auto_read = config.auto_read

    proc = subprocess.Popen(
        [
            "claude", "-p",
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    # Response-complete event — set when reader sees message_stop for current turn
    turn_done = threading.Event()
    response_text: list[str] = []

    def _reader() -> None:
        """Read claude stdout line-by-line, print text deltas, signal turn completion."""
        assert proc.stdout is not None
        for line in proc.stdout:
            text = parse_stream_event(line)
            if text is not None:
                response_text.append(text)
                sys.stdout.write(text)
                sys.stdout.flush()
                continue

            # Check for message_stop (end of turn) or result (final)
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            etype = event.get("event", {}).get("type") or event.get("type")
            if etype in ("message_stop", "result"):
                turn_done.set()

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    print("cc-voice REPL • /exit to quit, /stop to interrupt TTS, /toggle for auto-read")
    print()

    try:
        while True:
            try:
                user_input = input("user> ")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            cmd = parse_local_command(user_input)
            if cmd == "exit":
                break
            if cmd == "stop":
                _stop_playback()
                continue
            if cmd == "toggle":
                auto_read = not auto_read
                print(f"auto_read: {'on' if auto_read else 'off'}")
                continue

            # Send to claude
            response_text.clear()
            turn_done.clear()
            msg = format_user_message(user_input) + "\n"
            proc.stdin.write(msg)
            proc.stdin.flush()

            # Wait for response to complete
            sys.stdout.write("\n")
            turn_done.wait(timeout=120)
            sys.stdout.write("\n\n")

            # Speak full response
            if auto_read and response_text:
                full = "".join(response_text).strip()
                if full:
                    speak_streaming(
                        full, voice=config.voice, speed=config.speed, engine=config.engine,
                    )
    except KeyboardInterrupt:
        pass
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
