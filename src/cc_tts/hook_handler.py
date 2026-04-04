"""Stop hook handler for auto-read mode."""

from __future__ import annotations

import json
import sys

from cc_tts.config import load_config
from cc_tts.speak import synthesize_and_play


def extract_assistant_text(stdin_data: str) -> str:
    """Extract the last assistant message from hook JSON payload."""
    try:
        payload = json.loads(stdin_data)
    except (json.JSONDecodeError, TypeError):
        return ""

    transcript = payload.get("transcript", [])
    if not transcript:
        return ""

    for msg in reversed(transcript):
        if msg.get("role") == "assistant":
            return str(msg.get("content", ""))

    return ""


def main() -> None:
    """Entry point for the Stop hook. Reads stdin, speaks if auto_read enabled."""
    config = load_config()
    if not config.auto_read:
        return

    stdin_data = sys.stdin.read()
    text = extract_assistant_text(stdin_data)
    if text:
        synthesize_and_play(text, config=config)


if __name__ == "__main__":
    main()
