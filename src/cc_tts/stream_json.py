"""Stream-json TTS consumer — reads Claude Code streaming JSON, speaks responses."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable

from cc_tts.config import load_config
from cc_tts.edge_stream import speak_streaming
from cc_tts.sentence_buffer import SentenceBuffer


def parse_stream_event(line: str) -> str | None:
    """Extract assistant text from a stream-json event line.

    Handles two formats:
    - Streaming deltas: content_block_delta with text_delta
    - Complete messages: assistant with message.content[].text

    Returns extracted text or None for non-text events.
    """
    if not line.strip():
        return None
    try:
        event = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return None

    # Streaming delta format (--include-partial-messages)
    delta = event.get("event", {}).get("delta", {})
    if delta.get("type") == "text_delta":
        return delta.get("text")

    # Result event — skip, duplicates the assistant message text
    return None


def consume_stream(
    lines: Iterable[str],
    *,
    on_sentence: Callable[[str], None],
    on_text: Callable[[str], None] | None = None,
) -> None:
    """Consume stream-json lines and speak complete sentences.

    Feeds text_delta chunks to a SentenceBuffer. Calls on_text for each
    raw chunk (for immediate display) and on_sentence for complete sentences.
    """
    buf = SentenceBuffer(on_sentence=on_sentence)

    for line in lines:
        text = parse_stream_event(line)
        if text is not None:
            if on_text is not None:
                on_text(text)
            buf.feed(text)
            continue

        # Flush on message_stop (response complete)
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if event.get("event", {}).get("type") == "message_stop":
            buf.flush()


def main() -> None:
    """CLI entry point: cc-tts-stream <prompt>.

    Sends prompt to Claude via stream-json, speaks response sentences as they arrive.
    """
    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: cc-tts-stream <prompt>")
        print("  Sends prompt to Claude, speaks the response via TTS.")
        sys.exit(0 if "--help" in sys.argv or "-h" in sys.argv else 1)

    if shutil.which("claude") is None:
        print("Error: 'claude' CLI not found on PATH.", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    proc = subprocess.Popen(
        [
            "claude",
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            prompt,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    full_text: list[str] = []

    def _on_text(text: str) -> None:
        full_text.append(text)
        sys.stdout.write(text)
        sys.stdout.flush()

    try:
        assert proc.stdout is not None
        consume_stream(
            proc.stdout,
            on_sentence=lambda _: None,
            on_text=_on_text,
        )
        sys.stdout.write("\n")
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        proc.wait()

    response = "".join(full_text).strip()
    if response:
        config = load_config()
        speak_streaming(
            response, voice=config.voice, speed=config.speed, engine=config.engine,
        )


if __name__ == "__main__":
    main()
