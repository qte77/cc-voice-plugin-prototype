"""ANSI stripping and content classification for PTY output."""

from __future__ import annotations

import re

from cc_tts.sentence_buffer import SentenceBuffer

_CURSOR_RIGHT = re.compile(r"\x1b\[(\d*)C")
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\].*?\x07")
_PRINTABLE_ASCII = re.compile(r"[^\x20-\x7e]")


def _is_nonalpha_line(line: str) -> bool:
    """Return True if line is >80% non-alphabetic characters."""
    if len(line) < 4:
        return False
    alpha = sum(1 for c in line if c.isalpha())
    return alpha / len(line) < 0.2


class StreamFilter:
    """Filters PTY output for TTS: strips ANSI, skips code/tool/spinner content."""

    # CC UI markers (after ANSI strip + printable ASCII filter):
    # ● (\xe2\x97\x8f) = assistant response start
    # ❯ (\xe2\x9d\xaf) = user prompt (end of response)
    _RESPONSE_MARKER = "\u25cf"  # ●
    _PROMPT_MARKER = "\u276f"  # ❯

    def __init__(self, buffer: SentenceBuffer, *, wait_for_prompt: bool = False) -> None:
        self.buffer = buffer
        self._in_code_block = False
        self._byte_remainder = b""
        self._in_response = not wait_for_prompt

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

        # Ink uses \x1b[1C (cursor right) as spacing — replace with spaces first.
        clean = _CURSOR_RIGHT.sub(lambda m: " " * max(int(m.group(1) or "1"), 1), text)
        clean = _ANSI_ESCAPE.sub("", clean)

        # Detect state markers BEFORE CR normalization — Ink renders ● and ❯
        # on overwrite lines (\r...\r) that CR normalization would wipe.
        # A single chunk can contain both markers; use last occurrence to
        # determine final state.
        last_bullet = clean.rfind(self._RESPONSE_MARKER)
        last_prompt = clean.rfind(self._PROMPT_MARKER)
        if last_bullet > last_prompt:
            self._in_response = True
        elif last_prompt > last_bullet:
            self._in_response = False
            self.buffer.flush()

        # Normalize PTY line endings (PTY emits \r\r\n or \r\n), then
        # emulate terminal \r semantics: keep only text after last \r.
        clean = re.sub(r"\r+\n", "\n", clean)
        clean = re.sub(r"[^\n]*\r", "", clean)

        for line in clean.split("\n"):
            if not self._in_response:
                continue

            # Code block toggle
            stripped = line.strip()
            if stripped.startswith("```"):
                self._in_code_block = not self._in_code_block
                continue

            if self._in_code_block:
                continue

            # Keep only printable ASCII (drops box-drawing, emoji, etc.)
            stripped = _PRINTABLE_ASCII.sub("", stripped).strip()

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
