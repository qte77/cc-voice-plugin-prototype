"""Tests for cc_tts.repl — bidirectional stream-json REPL."""

from __future__ import annotations

import json
import threading

from cc_tts.repl import format_user_message, parse_local_command, read_stream_events


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
        msg = format_user_message('tell me a joke with "quotes"')
        parsed = json.loads(msg)
        assert parsed["message"]["content"] == 'tell me a joke with "quotes"'


def _text_delta_line(text: str) -> str:
    """Build a stream-json text_delta event line."""
    return json.dumps(
        {
            "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": text}},
        }
    )


def _event_line(etype: str) -> str:
    """Build a stream-json event line with just a type."""
    return json.dumps({"event": {"type": etype}})


def _result_line() -> str:
    """Build a stream-json result event line (top-level type)."""
    return json.dumps({"type": "result"})


class TestReadStreamEvents:
    def test_text_delta_calls_on_text(self) -> None:
        """text_delta events call on_text with the delta text."""
        received: list[str] = []
        turn_done = threading.Event()
        stdout = iter([_text_delta_line("hello"), _text_delta_line(" world")])
        read_stream_events(stdout, on_text=received.append, turn_done=turn_done)
        assert received == ["hello", " world"]

    def test_message_stop_sets_turn_done(self) -> None:
        """message_stop event sets turn_done."""
        received: list[str] = []
        turn_done = threading.Event()
        stdout = iter([_text_delta_line("hi"), _event_line("message_stop")])
        read_stream_events(stdout, on_text=received.append, turn_done=turn_done)
        assert turn_done.is_set()

    def test_result_event_sets_turn_done(self) -> None:
        """result event (top-level type) sets turn_done."""
        received: list[str] = []
        turn_done = threading.Event()
        stdout = iter([_result_line()])
        read_stream_events(stdout, on_text=received.append, turn_done=turn_done)
        assert turn_done.is_set()

    def test_non_text_events_ignored(self) -> None:
        """Non-text, non-stop events do not call on_text or set turn_done."""
        received: list[str] = []
        turn_done = threading.Event()
        stdout = iter(
            [
                json.dumps({"event": {"type": "content_block_start"}}),
                json.dumps({"event": {"type": "content_block_stop"}}),
            ]
        )
        read_stream_events(stdout, on_text=received.append, turn_done=turn_done)
        assert received == []
        assert not turn_done.is_set()

    def test_invalid_json_skipped(self) -> None:
        """Invalid JSON lines are silently skipped without raising."""
        received: list[str] = []
        turn_done = threading.Event()
        stdout = iter(["not json at all", "{broken", _text_delta_line("ok")])
        read_stream_events(stdout, on_text=received.append, turn_done=turn_done)
        assert received == ["ok"]
        assert not turn_done.is_set()
