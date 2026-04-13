"""Tests for cc_tts.pty_proxy — PTY integration tests."""

from __future__ import annotations

from cc_tts.pty_proxy import run_pty_proxy


class TestPtyProxy:
    def test_captures_echo_output(self) -> None:
        spoken: list[str] = []
        exit_code = run_pty_proxy(
            ["echo", "Hello world."],
            on_speak=spoken.append,
        )
        assert exit_code == 0
        assert any("Hello world" in s for s in spoken)

    def test_returns_child_exit_code(self) -> None:
        exit_code = run_pty_proxy(["false"])
        assert exit_code != 0
