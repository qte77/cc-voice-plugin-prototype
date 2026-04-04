"""TTS engine abstraction and implementations."""

from __future__ import annotations

import shutil
import subprocess
from typing import Protocol


class TTSEngine(Protocol):
    """Protocol for text-to-speech engines."""

    def synthesize(
        self, text: str, output_path: str, *, voice: str | None = None, speed: float = 1.0
    ) -> None: ...

    def available(self) -> bool: ...

    @property
    def name(self) -> str: ...


_ESPEAK_DEFAULT_VOICE = "en-us"
_PIPER_VOICE_PREFIX = "en_"


class EspeakEngine:
    """espeak-ng engine — lightweight, zero-config fallback."""

    @property
    def name(self) -> str:
        return "espeak-ng"

    def available(self) -> bool:
        return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    def _cmd(self) -> str:
        if shutil.which("espeak-ng") is not None:
            return "espeak-ng"
        return "espeak"

    def synthesize(
        self, text: str, output_path: str, *, voice: str | None = None, speed: float = 1.0
    ) -> None:
        # Ignore Piper voice names (contain underscores like en_US-amy-medium)
        if voice is not None and "_" in voice:
            voice = _ESPEAK_DEFAULT_VOICE
        cmd = [self._cmd(), "-w", output_path, "-v", voice or _ESPEAK_DEFAULT_VOICE]
        wpm = int(175 * speed)
        cmd.extend(["-s", str(wpm)])
        cmd.append(text)
        subprocess.run(cmd, check=True, capture_output=True)


class PiperEngine:
    """Piper TTS engine — neural VITS, good quality, fast."""

    @property
    def name(self) -> str:
        return "piper"

    def available(self) -> bool:
        return shutil.which("piper") is not None

    def synthesize(
        self, text: str, output_path: str, *, voice: str | None = None, speed: float = 1.0
    ) -> None:
        voice = voice or "en_US-amy-medium"
        cmd = [
            "piper",
            "--model",
            voice,
            "--output_file",
            output_path,
            "--length_scale",
            str(1.0 / speed),
        ]
        subprocess.run(cmd, input=text.encode(), check=True, capture_output=True)


class KokoroEngine:
    """Kokoro TTS engine — best local quality, 82M params."""

    @property
    def name(self) -> str:
        return "kokoro"

    def available(self) -> bool:
        return shutil.which("kokoro-tts") is not None

    def synthesize(
        self, text: str, output_path: str, *, voice: str | None = None, speed: float = 1.0
    ) -> None:
        import tempfile

        voice = voice or "af_sarah"
        # kokoro-tts reads from a file, not stdin
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            txt_path = f.name
        cmd = [
            "kokoro-tts",
            txt_path,
            output_path,
            "--voice",
            voice,
            "--lang",
            "en-us",
            "--speed",
            str(speed),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        finally:
            import os

            os.unlink(txt_path)


_ENGINE_TYPES = [KokoroEngine, PiperEngine, EspeakEngine]


def resolve_engine(engine_name: str = "auto") -> TTSEngine:
    """Resolve a TTS engine by name or auto-detect best available (kokoro > piper > espeak)."""
    name_map: dict[str, type[KokoroEngine] | type[EspeakEngine] | type[PiperEngine]] = {
        "espeak": EspeakEngine,
        "espeak-ng": EspeakEngine,
        "piper": PiperEngine,
        "kokoro": KokoroEngine,
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

    msg = "No TTS engine found. Install kokoro-tts, piper, or espeak-ng."
    raise RuntimeError(msg)
