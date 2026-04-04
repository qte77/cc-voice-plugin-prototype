"""ANSI stripping and content classification for PTY output."""

from __future__ import annotations

import re

from cc_tts.sentence_buffer import SentenceBuffer

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\].*?\x07")
_BOX_DRAWING = re.compile(r"[│─┌┐└┘├┤┬┴┼]")


def _is_nonalpha_line(line: str) -> bool:
    """Return True if line is >80% non-alphabetic characters."""
    if len(line) < 4:
        return False
    alpha = sum(1 for c in line if c.isalpha())
    return alpha / len(line) < 0.2


class StreamFilter:
    """Filters PTY output for TTS: strips ANSI, skips code/tool/spinner content."""

    def __init__(self, buffer: SentenceBuffer) -> None:
        self.buffer = buffer
        self._in_code_block = False
        self._byte_remainder = b""

    def feed(self, raw: bytes) -> bytes:
        """Process raw PTY bytes. Returns original bytes for terminal passthrough.

        Side effect: feeds cleaned text to the SentenceBuffer.
        """
        data = self._byte_remainder + raw
        self._byte_remainder = b""

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            # Partial UTF-8 at boundary — stash trailing bytes
            for i in range(1, 4):
                try:
                    text = data[:-i].decode("utf-8")
                    self._byte_remainder = data[-i:]
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = data.decode("utf-8", errors="replace")

        clean = _ANSI_ESCAPE.sub("", text)

        # Normalize PTY line endings (\r\n → \n) before splitting
        clean = clean.replace("\r\n", "\n")

        for line in clean.split("\n"):
            # Spinner detection: lines with remaining CR are overwrites — skip entirely
            if "\r" in line:
                continue

            # Code block toggle
            stripped = line.strip()
            if stripped.startswith("```"):
                self._in_code_block = not self._in_code_block
                continue

            if self._in_code_block:
                continue

            # Tool output: box-drawing characters
            if _BOX_DRAWING.search(line):
                continue

            # High non-alpha lines (diffs, separators)
            if _is_nonalpha_line(stripped):
                continue

            # Feed clean text to sentence buffer
            if stripped:
                self.buffer.feed(stripped + " ")

        return raw

    def finish(self) -> None:
        """Flush remaining content to the buffer."""
        self.buffer.flush()
