"""Main entry point: text → speech synthesis and playback."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from cc_tts.config import TTSConfig, load_config
from cc_tts.engine import resolve_engine
from cc_tts.player import NoAudioDeviceError, play_audio
from cc_tts.preprocess import preprocess

_output_counter = 0


def _next_output_path(output_dir: Path) -> str:
    """Return next sequential WAV path in the output directory."""
    global _output_counter  # noqa: PLW0603
    _output_counter += 1
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / f"{_output_counter:03d}.wav")


def synthesize_and_play(text: str, config: TTSConfig | None = None) -> None:
    """Preprocess text, synthesize speech, and play audio.

    Set CC_TTS_OUTPUT_DIR to save WAVs to a directory instead of playing.
    """
    config = config or load_config()
    text = preprocess(text, max_chars=config.max_chars)

    if not text:
        return

    engine = resolve_engine(config.engine)
    output_dir = os.environ.get("CC_TTS_OUTPUT_DIR")

    if output_dir:
        wav_path = _next_output_path(Path(output_dir))
        engine.synthesize(text, wav_path, voice=config.voice, speed=config.speed)
        print(f"WAV saved: {wav_path}", file=sys.stderr)
        return

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        engine.synthesize(text, f.name, voice=config.voice, speed=config.speed)
        try:
            play_audio(f.name, player=config.player, blocking=True)
        except NoAudioDeviceError:
            print(f"No audio device. WAV saved: {f.name}", file=sys.stderr)


def main() -> None:
    """CLI entry point for cc-tts."""
    if len(sys.argv) < 2:
        print("Usage: cc-tts <text>", file=sys.stderr)
        sys.exit(1)
    text = " ".join(sys.argv[1:])
    synthesize_and_play(text)


if __name__ == "__main__":
    main()
