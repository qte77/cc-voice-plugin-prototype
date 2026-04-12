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


    def test_worker_survives_callback_error(self) -> None:
        spoken: list[str] = []
        call_count = 0

        def flaky_speak(sentence: str) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("engine exploded")
            spoken.append(sentence)

        q: queue.Queue[str | None] = queue.Queue()
        q.put("Boom.")
        q.put("Survives.")
        q.put(None)

        _tts_worker(q, on_speak=flaky_speak)
        assert spoken == ["Survives."]

    def test_worker_handles_sigint_in_subprocess(self) -> None:
        import subprocess

        def sigint_speak(sentence: str) -> None:
            raise subprocess.CalledProcessError(-2, "kokoro-tts")

        q: queue.Queue[str | None] = queue.Queue()
        q.put("Interrupted.")
        q.put(None)

        _tts_worker(q, on_speak=sigint_speak)  # must not raise


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
