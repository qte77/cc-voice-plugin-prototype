"""Tests for cc_vlm.templates — prompt template dict + accessor."""

from __future__ import annotations

import pytest

from cc_vlm.templates import PROMPT_TEMPLATES, get_template


class TestPromptTemplates:
    def test_five_templates_shipped(self) -> None:
        """MVP ships terminal, editor, browser, gui, generic."""
        expected = {"terminal", "editor", "browser", "gui", "generic"}
        assert set(PROMPT_TEMPLATES.keys()) == expected

    def test_each_template_has_max_word_cap(self) -> None:
        """Every template constrains output length at the VLM source."""
        for name, prompt in PROMPT_TEMPLATES.items():
            assert "Max" in prompt and "words" in prompt, (
                f"Template {name!r} missing word cap instruction"
            )

    def test_templates_are_non_empty(self) -> None:
        for name, prompt in PROMPT_TEMPLATES.items():
            assert prompt.strip(), f"Template {name!r} is empty"


class TestGetTemplate:
    def test_returns_template_for_known_name(self) -> None:
        assert get_template("terminal") == PROMPT_TEMPLATES["terminal"]
        assert get_template("generic") == PROMPT_TEMPLATES["generic"]

    def test_raises_value_error_for_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown template"):
            get_template("nonexistent")

    def test_error_lists_available_templates(self) -> None:
        with pytest.raises(ValueError, match="browser"):
            get_template("bad")
