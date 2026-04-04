"""Tests for cc_tts.hook_handler — TDD RED phase."""

from __future__ import annotations

import json

from cc_tts.hook_handler import extract_assistant_text


class TestExtractAssistantText:
    def test_extracts_text_from_stop_event(self) -> None:
        payload = {
            "session_id": "abc",
            "stop_hook_active": True,
            "transcript": [
                {"role": "assistant", "content": "Hello from Claude."},
            ],
        }
        result = extract_assistant_text(json.dumps(payload))
        assert result == "Hello from Claude."

    def test_returns_empty_for_no_transcript(self) -> None:
        payload = {"session_id": "abc"}
        result = extract_assistant_text(json.dumps(payload))
        assert result == ""

    def test_returns_empty_for_empty_transcript(self) -> None:
        payload = {"session_id": "abc", "transcript": []}
        result = extract_assistant_text(json.dumps(payload))
        assert result == ""

    def test_returns_last_assistant_message(self) -> None:
        payload = {
            "transcript": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "first"},
                {"role": "assistant", "content": "second"},
            ],
        }
        result = extract_assistant_text(json.dumps(payload))
        assert result == "second"

    def test_handles_invalid_json(self) -> None:
        result = extract_assistant_text("not json")
        assert result == ""
