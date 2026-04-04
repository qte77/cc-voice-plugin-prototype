"""Tests for cc_stt.utterance_buffer — TDD RED phase."""

from __future__ import annotations

import struct

from cc_stt.utterance_buffer import UtteranceBuffer


def _silence_bytes(n_samples: int, sample_rate: int = 16000) -> bytes:
    """Generate n_samples of silence as 16-bit PCM bytes."""
    return b"\x00\x00" * n_samples


def _tone_bytes(n_samples: int) -> bytes:
    """Generate n_samples of non-silent audio as 16-bit PCM bytes."""
    return struct.pack(f"<{n_samples}h", *([16000] * n_samples))


class TestUtteranceBufferSilenceBoundary:
    def test_fires_on_silence_boundary(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=100,
            sample_rate=16000,
        )
        # Feed speech then silence
        buf.feed(_tone_bytes(4800))  # 300ms of speech
        buf.feed(_silence_bytes(3200))  # 200ms of silence (> 100ms threshold)
        assert len(results) == 1
        assert len(results[0]) > 0

    def test_does_not_fire_on_short_silence(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=500,
            sample_rate=16000,
        )
        buf.feed(_tone_bytes(4800))  # 300ms speech
        buf.feed(_silence_bytes(1600))  # 100ms silence (< 500ms threshold)
        assert len(results) == 0

    def test_accumulates_across_feeds(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=100,
            sample_rate=16000,
        )
        buf.feed(_tone_bytes(1600))
        buf.feed(_tone_bytes(1600))
        buf.feed(_tone_bytes(1600))
        # No silence yet — no callback
        assert len(results) == 0


class TestUtteranceBufferTimeout:
    def test_flushes_on_max_duration(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=200,
            max_duration_ms=500,
            sample_rate=16000,
        )
        # Feed 600ms of speech (exceeds 500ms max)
        buf.feed(_tone_bytes(9600))
        assert len(results) == 1


class TestUtteranceBufferFlushReset:
    def test_flush_delivers_remainder(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=500,
            sample_rate=16000,
        )
        buf.feed(_tone_bytes(4800))
        assert len(results) == 0
        buf.flush()
        assert len(results) == 1

    def test_flush_empty_is_noop(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=500,
            sample_rate=16000,
        )
        buf.flush()
        assert len(results) == 0

    def test_reset_clears_without_callback(self) -> None:
        results: list[bytes] = []
        buf = UtteranceBuffer(
            on_utterance=results.append,
            silence_threshold=0.01,
            silence_duration_ms=500,
            sample_rate=16000,
        )
        buf.feed(_tone_bytes(4800))
        buf.reset()
        buf.flush()
        assert len(results) == 0
