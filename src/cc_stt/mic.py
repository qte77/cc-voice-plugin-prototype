"""Microphone capture with sounddevice, graceful no-mic detection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class NoMicrophoneError(RuntimeError):
    """Raised when no microphone input device is available."""


def _check_sounddevice() -> Any:
    """Import and return sounddevice module. Raises ImportError if missing."""
    import sounddevice  # noqa: F811

    return sounddevice


def _query_devices(device: str = "default") -> str:
    """Query for input device availability. Raises NoMicrophoneError if none found."""
    sd = _check_sounddevice()
    try:
        sd.query_devices(device, "input")
    except (sd.PortAudioError, ValueError) as exc:
        msg = f"no input device: {exc}"
        raise NoMicrophoneError(msg) from exc
    return device


def _open_stream(
    device: str,
    sample_rate: int,
    channels: int,
    callback: Callable[..., None],
) -> Any:
    """Open a sounddevice InputStream."""
    sd = _check_sounddevice()
    stream = sd.InputStream(
        device=device if device != "default" else None,
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        callback=callback,
    )
    stream.start()
    return stream


class MicCapture:
    """Streaming microphone capture with callback-based audio delivery."""

    def __init__(
        self,
        *,
        device: str = "default",
        sample_rate: int = 16000,
        channels: int = 1,
        on_audio: Callable[[bytes], None] | None = None,
    ) -> None:
        _check_sounddevice()
        self.device = _query_devices(device)
        self.sample_rate = sample_rate
        self.channels = channels
        self._on_audio = on_audio
        self._stream: Any = None

    @property
    def is_active(self) -> bool:
        return self._stream is not None

    def _callback(
        self, indata: Any, frames: int, time: Any, status: Any
    ) -> None:
        """Sounddevice callback — converts numpy array to bytes and delivers."""
        if self._on_audio is not None:
            self._on_audio(indata.tobytes())

    def start(self) -> None:
        """Start capturing audio from microphone."""
        if self._stream is not None:
            return
        self._stream = _open_stream(
            self.device, self.sample_rate, self.channels, self._callback
        )

    def stop(self) -> None:
        """Stop capturing audio."""
        if self._stream is None:
            return
        self._stream.stop()
        self._stream.close()
        self._stream = None
