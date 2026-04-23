"""Tests for cc_stt.preprocess — filler stripping and word capping."""

from __future__ import annotations

from cc_stt.preprocess import cap_words, strip_fillers


class TestStripFillers:
    def test_removes_um_uh(self) -> None:
        assert strip_fillers("um I think uh we should") == "I think we should"

    def test_removes_you_know(self) -> None:
        assert strip_fillers("you know the tests are failing") == "the tests are failing"

    def test_removes_basically_actually(self) -> None:
        assert strip_fillers("basically it actually works") == "it works"

    def test_removes_like(self) -> None:
        assert strip_fillers("it's like really broken") == "it's really broken"

    def test_case_insensitive(self) -> None:
        assert strip_fillers("UM I think BASICALLY it works") == "I think it works"

    def test_preserves_clean_text(self) -> None:
        text = "run the tests please"
        assert strip_fillers(text) == text

    def test_empty_input(self) -> None:
        assert strip_fillers("") == ""

    def test_only_fillers(self) -> None:
        assert strip_fillers("um uh like") == ""


class TestCapWords:
    def test_under_limit_unchanged(self) -> None:
        text = "hello world"
        assert cap_words(text, max_words=10) == text

    def test_at_limit_unchanged(self) -> None:
        text = "one two three"
        assert cap_words(text, max_words=3) == text

    def test_over_limit_truncates(self) -> None:
        text = "one two three four five"
        assert cap_words(text, max_words=3) == "one two three [truncated]"

    def test_default_limit_is_200(self) -> None:
        words = ["word"] * 250
        result = cap_words(" ".join(words))
        assert result.endswith("[truncated]")
        # 200 words + "[truncated]"
        assert len(result.split()) == 201

    def test_empty_input(self) -> None:
        assert cap_words("") == ""
