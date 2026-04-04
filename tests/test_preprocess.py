"""Tests for cc_tts.preprocess — TDD RED phase."""

from __future__ import annotations

from cc_tts.preprocess import preprocess


class TestPreprocess:
    def test_strips_fenced_code_blocks(self) -> None:
        text = "Here is code:\n```python\nprint('hi')\n```\nEnd."
        result = preprocess(text)
        assert "print" not in result
        assert "code block omitted" in result

    def test_strips_inline_code(self) -> None:
        text = "Run `pip install foo` to install."
        result = preprocess(text)
        assert "`" not in result

    def test_shortens_urls(self) -> None:
        text = "See https://example.com/very/long/path for details."
        result = preprocess(text)
        assert "https://example.com" not in result
        assert "link" in result

    def test_strips_markdown_headers(self) -> None:
        text = "## Section Title\nContent here."
        result = preprocess(text)
        assert "##" not in result
        assert "Section Title" in result

    def test_strips_bold_and_italic(self) -> None:
        text = "This is **bold** and *italic* text."
        result = preprocess(text)
        assert "**" not in result
        assert "*" not in result
        assert "bold" in result

    def test_preserves_plain_text(self) -> None:
        text = "Hello, this is a normal sentence."
        assert preprocess(text) == text

    def test_truncates_long_text(self) -> None:
        text = "a" * 3000
        result = preprocess(text, max_chars=2000)
        assert len(result) <= 2000
