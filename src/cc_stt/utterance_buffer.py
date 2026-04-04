"""VAD-based audio chunking — accumulates PCM frames, fires on silence boundary."""

from __future__ import annotations

import struct
from collections.abc import Callable


class UtteranceBuffer:
    """Accumulates 16-bit PCM audio and fires callback on silence boundaries."""

    def __init__(
        self,
        on_utterance: Callable[[bytes], None],
        *,
        silence_threshold: float = 0.01,
        silence_duration_ms: int = 300,
        max_duration_ms: int = 30000,
        sample_rate: int = 16000,
    ) -> None:
        self._on_utterance = on_utterance
        self._silence_threshold = silence_threshold
        self._silence_samples = int(sample_rate * silence_duration_ms / 1000)
        self._max_samples = int(sample_rate * max_duration_ms / 1000)
        self._sample_rate = sample_rate
        self._buf = bytearray()
        self._silence_count = 0
        self._has_speech = False

    def feed(self, pcm_bytes: bytes) -> None:
        """Add 16-bit PCM audio. Fires callback when silence boundary detected."""
        self._buf.extend(pcm_bytes)
        n_samples = len(pcm_bytes) // 2

        # Check energy level of this chunk
        samples = struct.unpack(f"<{n_samples}h", pcm_bytes)
        rms = (sum(s * s for s in samples) / n_samples) ** 0.5 / 32768.0

        if rms < self._silence_threshold:
            self._silence_count += n_samples
        else:
            self._silence_count = 0
            self._has_speech = True

        total_samples = len(self._buf) // 2

        # Flush on max duration
        if total_samples >= self._max_samples:
            self._flush_buf()
            return

        # Flush on silence boundary (only if we had speech)
        if self._has_speech and self._silence_count >= self._silence_samples:
            self._flush_buf()

    def flush(self) -> None:
        """Deliver any remaining buffered audio."""
        self._flush_buf()

    def reset(self) -> None:
        """Clear buffer without delivering."""
        self._buf.clear()
        self._silence_count = 0
        self._has_speech = False

    def _flush_buf(self) -> None:
        if not self._buf:
            return
        data = bytes(self._buf)
        self._buf.clear()
        self._silence_count = 0
        self._has_speech = False
        self._on_utterance(data)
