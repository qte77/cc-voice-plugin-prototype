"""Tests for cc_tts.tts_worker — shared TTS queue worker."""

from __future__ import annotations

import queue
import threading
import time

from cc_tts.tts_worker import tts_worker


class TestTtsWorker:
    def test_processes_sentences_from_queue(self) -> None:
        spoken: list[str] = []
        q: queue.Queue[str | None] = queue.Queue()
        q.put("Hello.")
        q.put(None)

        tts_worker(q, on_speak=spoken.append)
        assert spoken == ["Hello."]

    def test_stops_on_none_sentinel(self) -> None:
        q: queue.Queue[str | None] = queue.Queue()
        q.put("First.")
        q.put("Second.")
        q.put(None)

        spoken: list[str] = []
        tts_worker(q, on_speak=spoken.append)
        # Both sentences queued before worker starts → batched into one call
        assert spoken == ["First. Second."]

    def test_worker_survives_callback_error(self) -> None:
        spoken: list[str] = []

        def flaky_speak(sentence: str) -> None:
            if "Boom" in sentence:
                raise RuntimeError("engine exploded")
            spoken.append(sentence)

        q: queue.Queue[str | None] = queue.Queue()
        q.put("OK.")
        q.put(None)

        tts_worker(q, on_speak=flaky_speak)
        assert spoken == ["OK."]

    def test_worker_survives_batch_error(self) -> None:
        """Error in one batch doesn't prevent next batch from speaking."""
        spoken: list[str] = []
        q: queue.Queue[str | None] = queue.Queue()

        def delayed_feed() -> None:
            time.sleep(0.05)
            q.put("After.")
            q.put(None)

        def flaky_speak(sentence: str) -> None:
            if "Boom" in sentence:
                raise RuntimeError("engine exploded")
            spoken.append(sentence)

        q.put("Boom.")
        t = threading.Thread(target=delayed_feed)
        t.start()
        tts_worker(q, on_speak=flaky_speak)
        t.join()
        assert spoken == ["After."]

    def test_worker_handles_sigint_in_subprocess(self) -> None:
        import subprocess

        def sigint_speak(sentence: str) -> None:
            raise subprocess.CalledProcessError(-2, "kokoro-tts")

        q: queue.Queue[str | None] = queue.Queue()
        q.put("Interrupted.")
        q.put(None)

        tts_worker(q, on_speak=sigint_speak)  # must not raise
