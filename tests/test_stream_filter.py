"""Tests for cc_tts.stream_filter — TDD RED phase."""

from __future__ import annotations

from cc_tts.sentence_buffer import SentenceBuffer
from cc_tts.stream_filter import StreamFilter


def _make_filter() -> tuple[StreamFilter, list[str]]:
    sentences: list[str] = []
    buf = SentenceBuffer(on_sentence=sentences.append)
    return StreamFilter(buf), sentences


class TestAnsiStripping:
    def test_strips_sgr_sequences(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"\x1b[1mBold text.\x1b[0m ")
        assert sentences == ["Bold text."]

    def test_strips_cursor_movement(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"\x1b[2KHello. ")
        assert sentences == ["Hello."]

    def test_passes_through_raw_bytes(self) -> None:
        sf, _ = _make_filter()
        raw = b"\x1b[1mBold\x1b[0m"
        result = sf.feed(raw)
        assert result == raw  # terminal gets original


class TestCodeBlockSkip:
    def test_skips_inside_code_block(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"Before. ```\ncode here\n``` After. ")
        assert "code here" not in " ".join(sentences)
        assert "Before." in sentences

    def test_toggle_code_block_state(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"Start. ")
        sf.feed(b"```\n")
        sf.feed(b"skipped\n")
        sf.feed(b"```\n")
        sf.feed(b"End. ")
        sf.buffer.flush()
        spoken = " ".join(sentences)
        assert "skipped" not in spoken
        assert "Start." in spoken


class TestToolOutputSkip:
    def test_skips_box_drawing_lines(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"Answer. \n\xe2\x94\x82 tool output\n")
        sf.buffer.flush()
        assert "tool output" not in " ".join(sentences)

    def test_skips_high_nonalpha_lines(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"Hello. \n----====----\n")
        sf.buffer.flush()
        assert "----" not in " ".join(sentences)


class TestSpinnerSkip:
    def test_skips_carriage_return_lines(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"\rSpinning...")
        sf.feed(b"\rDone.\n")
        sf.buffer.flush()
        # Spinner lines with CR but no preceding NL should be skipped
        assert "Spinning" not in " ".join(sentences)


class TestFinish:
    def test_finish_flushes_buffer(self) -> None:
        sf, sentences = _make_filter()
        sf.feed(b"Trailing text")
        sf.finish()
        assert sentences == ["Trailing text"]
