"""Live listen pipeline: mic -> buffer -> engine -> PTY injection."""

from __future__ import annotations

import tempfile
import threading
import wave
from pathlib import Path

from cc_stt.config import load_stt_config
from cc_stt.engine import resolve_stt_engine
from cc_stt.mic import MicCapture
from cc_stt.pty_input import inject_text
from cc_stt.utterance_buffer import UtteranceBuffer


def _write_wav(pcm_bytes: bytes, path: str, *, sample_rate: int = 16000) -> None:
    """Write raw 16-bit PCM bytes to a WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def listen_live(
    config: object = None,
    *,
    pty_fd: int | None = None,
    stop_event: threading.Event | None = None,
) -> None:
    """Mic -> buffer -> engine -> PTY injection.

    Blocks until stop_event is set.
    """
    stt_config = load_stt_config() if config is None else config
    engine = resolve_stt_engine(stt_config.engine)

    def on_utterance(pcm_bytes: bytes) -> None:
        """Transcribe utterance and inject text to PTY."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            _write_wav(pcm_bytes, tmp.name, sample_rate=16000)
            text = engine.transcribe(tmp.name)
        if text and pty_fd is not None:
            inject_text(pty_fd, text)

    buffer = UtteranceBuffer(on_utterance)

    mic = MicCapture(
        device=stt_config.mic_device,
        on_audio=buffer.feed,
    )
    mic.start()

    try:
        if stop_event is not None:
            stop_event.wait()
    finally:
        mic.stop()
        buffer.flush()


def transcribe_file(path: str, config: object = None) -> str:
    """File -> engine -> text."""
    if not Path(path).is_file():
        msg = f"Audio file not found: {path}"
        raise FileNotFoundError(msg)

    stt_config = load_stt_config() if config is None else config
    engine = resolve_stt_engine(stt_config.engine)
    return engine.transcribe(path)
