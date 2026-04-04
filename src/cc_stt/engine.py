"""STT engine abstraction and implementations."""

from __future__ import annotations

import shutil
import subprocess
from typing import Protocol


class STTEngine(Protocol):
    """Protocol for speech-to-text engines."""

    def transcribe(self, audio_path: str) -> str: ...

    def available(self) -> bool: ...

    @property
    def name(self) -> str: ...


class MoonshineEngine:
    """Moonshine STT engine — 27M params, ~400ms latency, on-device."""

    @property
    def name(self) -> str:
        return "moonshine"

    def available(self) -> bool:
        return shutil.which("moonshine") is not None

    def transcribe(self, audio_path: str) -> str:
        result = subprocess.run(
            ["moonshine", audio_path],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode().strip()


class VoskEngine:
    """Vosk STT engine — lightweight offline, ~50MB model."""

    @property
    def name(self) -> str:
        return "vosk"

    def available(self) -> bool:
        return shutil.which("vosk-transcriber") is not None

    def transcribe(self, audio_path: str) -> str:
        result = subprocess.run(
            ["vosk-transcriber", "-i", audio_path],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode().strip()


_ENGINE_TYPES = [MoonshineEngine, VoskEngine]


def resolve_stt_engine(engine_name: str = "auto") -> STTEngine:
    """Resolve an STT engine by name or auto-detect best available (moonshine > vosk)."""
    name_map: dict[str, type[MoonshineEngine] | type[VoskEngine]] = {
        "moonshine": MoonshineEngine,
        "vosk": VoskEngine,
    }
    if engine_name != "auto":
        cls = name_map.get(engine_name)
        if cls is None:
            msg = f"Unknown engine: {engine_name}. Available: {', '.join(name_map)}"
            raise ValueError(msg)
        engine = cls()
        if not engine.available():
            msg = f"Engine '{engine_name}' is not installed"
            raise RuntimeError(msg)
        return engine

    for cls in _ENGINE_TYPES:
        engine = cls()
        if engine.available():
            return engine

    msg = "No STT engine found. Install moonshine or vosk."
    raise RuntimeError(msg)
