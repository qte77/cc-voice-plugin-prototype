"""Sentence accumulator with boundary detection and flush callback."""

from __future__ import annotations

import re
from collections.abc import Callable

_SENTENCE_END = re.compile(r"([.!?])(\s+)")


class SentenceBuffer:
    """Accumulates text fragments and fires callback on sentence boundaries."""

    def __init__(self, on_sentence: Callable[[str], None], *, max_chars: int = 2000) -> None:
        self._on_sentence = on_sentence
        self._max_chars = max_chars
        self._buf: list[str] = []
        self._buf_len = 0

    def feed(self, text: str) -> None:
        """Add text fragment. Fires callback for each complete sentence found."""
        self._buf.append(text)
        self._buf_len += len(text)

        if self._buf_len >= self._max_chars:
            self._flush_buf()
            return

        joined = "".join(self._buf)
        parts = _SENTENCE_END.split(joined)

        if len(parts) < 4:
            return

        # parts = [sentence, punct, space, sentence, punct, space, ..., remainder]
        sentences: list[str] = []
        i = 0
        while i + 2 < len(parts):
            sentences.append(parts[i] + parts[i + 1])
            i += 3
        remainder = parts[i] if i < len(parts) else ""

        for s in sentences:
            s = s.strip()
            if s:
                self._on_sentence(s)

        self._buf = [remainder] if remainder else []
        self._buf_len = len(remainder)

    def flush(self) -> None:
        """Speak any remaining buffered text."""
        self._flush_buf()

    def reset(self) -> None:
        """Clear buffer without speaking."""
        self._buf.clear()
        self._buf_len = 0

    def _flush_buf(self) -> None:
        if not self._buf:
            return
        text = "".join(self._buf).strip()
        self._buf.clear()
        self._buf_len = 0
        if text:
            self._on_sentence(text)
