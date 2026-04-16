"""Tests for cc_tts.repl — bidirectional stream-json REPL."""

from __future__ import annotations

import json

from cc_tts.repl import format_user_message, parse_local_command


class TestParseLocalCommand:
    def test_exit_recognized(self) -> None:
        assert parse_local_command("/exit") == "exit"

    def test_stop_recognized(self) -> None:
        assert parse_local_command("/stop") == "stop"

    def test_toggle_recognized(self) -> None:
        assert parse_local_command("/toggle") == "toggle"

    def test_plain_text_returns_none(self) -> None:
        assert parse_local_command("hello world") is None

    def test_unknown_slash_returns_none(self) -> None:
        """Unknown /commands forwarded to claude, not intercepted."""
        assert parse_local_command("/commit") is None

    def test_whitespace_stripped(self) -> None:
        assert parse_local_command("  /exit  ") == "exit"


class TestFormatUserMessage:
    def test_formats_as_stream_json(self) -> None:
        msg = format_user_message("hello")
        parsed = json.loads(msg)
        assert parsed["type"] == "user"
        assert parsed["message"]["role"] == "user"
        assert parsed["message"]["content"] == "hello"

    def test_preserves_text(self) -> None:
        msg = format_user_message("tell me a joke with \"quotes\"")
        parsed = json.loads(msg)
        assert parsed["message"]["content"] == 'tell me a joke with "quotes"'
