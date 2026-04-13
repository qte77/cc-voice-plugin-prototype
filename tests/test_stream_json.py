"""Tests for cc_tts.stream_json — stream-json TTS consumer."""

from __future__ import annotations

from cc_tts.stream_json import consume_stream, parse_stream_event


class TestParseStreamEvent:
    def test_extracts_text_delta(self) -> None:
        line = '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello "}}}'
        assert parse_stream_event(line) == "Hello "

    def test_skips_assistant_message(self) -> None:
        line = '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello there."}]}}'
        assert parse_stream_event(line) is None

    def test_skips_result_event(self) -> None:
        line = '{"type":"result","result":"Hello there."}'
        assert parse_stream_event(line) is None

    def test_returns_none_for_system_event(self) -> None:
        line = '{"type":"system","subtype":"init"}'
        assert parse_stream_event(line) is None

    def test_returns_none_for_tool_use(self) -> None:
        line = '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"input_json_delta","partial_json":"{}"}}}'
        assert parse_stream_event(line) is None

    def test_returns_none_for_invalid_json(self) -> None:
        assert parse_stream_event("not json") is None

    def test_returns_none_for_empty_line(self) -> None:
        assert parse_stream_event("") is None


class TestConsumeStream:
    def test_speaks_from_deltas(self) -> None:
        lines = [
            '{"type":"system","subtype":"init"}',
            '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello. "}}}',
            '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"How are you?"}}}',
            '{"type":"stream_event","event":{"type":"message_stop"}}',
            '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello. How are you?"}]}}',
            '{"type":"result","result":"Hello. How are you?"}',
        ]
        spoken: list[str] = []
        consume_stream(iter(lines), on_sentence=spoken.append)
        assert spoken == ["Hello.", "How are you?"]

    def test_speaks_streaming_deltas(self) -> None:
        lines = [
            '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello. How are you?"}}}',
            '{"type":"stream_event","event":{"type":"message_stop"}}',
        ]
        spoken: list[str] = []
        consume_stream(iter(lines), on_sentence=spoken.append)
        assert "Hello." in spoken
        assert "How are you?" in spoken

    def test_ignores_system_events(self) -> None:
        lines = [
            '{"type":"system","subtype":"hook_started"}',
            '{"type":"system","subtype":"init"}',
            '{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello."}}}',
            '{"type":"stream_event","event":{"type":"message_stop"}}',
        ]
        spoken: list[str] = []
        consume_stream(iter(lines), on_sentence=spoken.append)
        assert spoken == ["Hello."]

    def test_handles_empty_stream(self) -> None:
        spoken: list[str] = []
        consume_stream(iter([]), on_sentence=spoken.append)
        assert spoken == []
