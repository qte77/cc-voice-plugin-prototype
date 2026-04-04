"""Tests for cc_tts.pty_proxy — TDD RED phase."""

from __future__ import annotations

import queue

from cc_tts.pty_proxy import _tts_worker, run_pty_proxy


class TestTtsWorker:
    def test_processes_sentences_from_queue(self) -> None:
        spoken: list[str] = []
        q: queue.Queue[str | None] = queue.Queue()
        q.put("Hello.")
        q.put(None)  # sentinel to stop

        _tts_worker(q, on_speak=spoken.append)
        assert spoken == ["Hello."]

    def test_stops_on_none_sentinel(self) -> None:
        q: queue.Queue[str | None] = queue.Queue()
        q.put("First.")
        q.put("Second.")
        q.put(None)

        spoken: list[str] = []
        _tts_worker(q, on_speak=spoken.append)
        assert spoken == ["First.", "Second."]


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
