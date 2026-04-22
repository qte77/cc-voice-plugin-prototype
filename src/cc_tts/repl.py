"""Bidirectional stream-json REPL with TTS — interactive Claude without PTY."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Iterable

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
    return json.dumps(
        {
            "type": "user",
            "message": {"role": "user", "content": text},
        }
    )


def read_stream_events(
    stdout: Iterable[str],
    on_text: Callable[[str], None],
    turn_done: threading.Event,
) -> None:
    """Read claude stdout line-by-line, call on_text for deltas, set turn_done on stop."""
    for line in stdout:
        text = parse_stream_event(line)
        if text is not None:
            on_text(text)
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        etype = event.get("event", {}).get("type") or event.get("type")
        if etype in ("message_stop", "result"):
            turn_done.set()


def _start_claude() -> subprocess.Popen[str]:
    """Launch claude in stream-json mode; exits if claude is not on PATH."""
    if shutil.which("claude") is None:
        print("Error: 'claude' CLI not found on PATH.", file=sys.stderr)
        sys.exit(1)
    return subprocess.Popen(
        [
            "claude",
            "-p",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _handle_local_cmd(cmd: str, auto_read: bool) -> tuple[bool, bool]:
    """Execute a local command. Returns (should_break, new_auto_read)."""
    if cmd == "exit":
        return True, auto_read
    if cmd == "stop":
        _stop_playback()
    elif cmd == "toggle":
        auto_read = not auto_read
        print(f"auto_read: {'on' if auto_read else 'off'}")
    return False, auto_read


def _make_on_text(buf: list[str]) -> Callable[[str], None]:
    """Return an on_text callback that appends to buf and writes to stdout."""

    def _on_text(text: str) -> None:
        buf.append(text)
        sys.stdout.write(text)
        sys.stdout.flush()

    return _on_text


def main() -> None:
    """REPL loop: user input → claude stdin (JSON) → read deltas → print + TTS."""
    config = load_config()
    auto_read = config.auto_read

    proc = _start_claude()
    assert proc.stdin is not None
    assert proc.stdout is not None

    turn_done = threading.Event()
    response_text: list[str] = []
    threading.Thread(
        target=read_stream_events,
        args=(proc.stdout, _make_on_text(response_text), turn_done),
        daemon=True,
    ).start()
    print("cc-voice REPL • /exit to quit, /stop to interrupt TTS, /toggle for auto-read\n")

    try:
        while True:
            try:
                user_input = input("user> ")
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input.strip():
                continue
            cmd = parse_local_command(user_input)
            if cmd is not None:
                should_break, auto_read = _handle_local_cmd(cmd, auto_read)
                if should_break:
                    break
                continue

            response_text.clear()
            turn_done.clear()
            proc.stdin.write(format_user_message(user_input) + "\n")
            proc.stdin.flush()
            sys.stdout.write("\n")
            turn_done.wait(timeout=120)
            sys.stdout.write("\n\n")

            if auto_read and (full := "".join(response_text).strip()):
                speak_streaming(full, voice=config.voice, speed=config.speed, engine=config.engine)
    except KeyboardInterrupt:
        pass
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
