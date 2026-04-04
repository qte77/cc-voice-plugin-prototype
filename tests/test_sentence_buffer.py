"""Tests for cc_tts.sentence_buffer — TDD RED phase."""

from __future__ import annotations

from cc_tts.sentence_buffer import SentenceBuffer


class TestSentenceBuffer:
    def test_fires_callback_on_period(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("Hello world. ")
        assert sentences == ["Hello world."]

    def test_fires_on_question_mark(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("How are you? ")
        assert sentences == ["How are you?"]

    def test_fires_on_exclamation(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("Great! ")
        assert sentences == ["Great!"]

    def test_accumulates_across_feeds(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("Hello ")
        buf.feed("world. ")
        assert sentences == ["Hello world."]

    def test_multiple_sentences(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("First. Second. ")
        assert sentences == ["First.", "Second."]

    def test_flush_speaks_remainder(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("Trailing text")
        assert sentences == []
        buf.flush()
        assert sentences == ["Trailing text"]

    def test_flush_empty_is_noop(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.flush()
        assert sentences == []

    def test_reset_clears_without_speaking(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append)
        buf.feed("Some text")
        buf.reset()
        buf.flush()
        assert sentences == []

    def test_max_chars_forces_flush(self) -> None:
        sentences: list[str] = []
        buf = SentenceBuffer(on_sentence=sentences.append, max_chars=20)
        buf.feed("a" * 25)
        assert len(sentences) == 1
        assert len(sentences[0]) <= 25
