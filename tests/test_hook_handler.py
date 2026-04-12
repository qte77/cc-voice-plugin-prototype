"""Tests for cc_tts.hook_handler — extracts assistant text from CC Stop hook payload."""

from __future__ import annotations

import json

from cc_tts.hook_handler import extract_assistant_text


class TestExtractAssistantText:
    def test_extracts_last_assistant_message(self) -> None:
        """CC Stop hook sends last_assistant_message as a top-level field."""
        payload = {
            "session_id": "abc",
            "hook_event_name": "Stop",
            "last_assistant_message": "Hello from Claude.",
        }
        result = extract_assistant_text(json.dumps(payload))
        assert result == "Hello from Claude."

    def test_returns_empty_when_field_missing(self) -> None:
        payload = {"session_id": "abc", "hook_event_name": "Stop"}
        result = extract_assistant_text(json.dumps(payload))
        assert result == ""

    def test_returns_empty_for_empty_message(self) -> None:
        payload = {"last_assistant_message": ""}
        result = extract_assistant_text(json.dumps(payload))
        assert result == ""

    def test_handles_invalid_json(self) -> None:
        result = extract_assistant_text("not json")
        assert result == ""

    def test_handles_empty_input(self) -> None:
        result = extract_assistant_text("")
        assert result == ""
