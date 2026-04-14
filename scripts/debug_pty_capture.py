"""Capture raw PTY bytes from cc-tts-wrap for filter debugging.

Usage:
    uv run python scripts/debug_pty_capture.py

Output:
    ~/.cache/cc-voice/pty-raw.bin  — raw bytes
    ~/.cache/cc-voice/pty-seen.log — what StreamFilter received

Send a short message in the Claude session, then /exit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.argv = ["cc-tts-wrap", "claude"]

_OUT_DIR = Path.home() / ".cache" / "cc-voice"
_OUT_DIR.mkdir(parents=True, exist_ok=True)
_RAW = _OUT_DIR / "pty-raw.bin"
_LOG = _OUT_DIR / "pty-seen.log"

# Clear previous captures
_RAW.write_bytes(b"")
_LOG.write_text("")

from cc_tts import stream_filter  # noqa: E402

_orig_feed = stream_filter.StreamFilter.feed


def _debug_feed(self: stream_filter.StreamFilter, raw: bytes) -> bytes:
    with _RAW.open("ab") as f:
        f.write(raw)
    with _LOG.open("a") as f:
        f.write(f"--- feed({len(raw)}B) ---\n{raw[:500]!r}\n")
    return _orig_feed(self, raw)


stream_filter.StreamFilter.feed = _debug_feed  # type: ignore[method-assign]

from cc_tts.pty_proxy import run_pty_proxy  # noqa: E402

sys.exit(run_pty_proxy(["claude"]))
