"""Main entry point: text → speech synthesis and playback."""

from __future__ import annotations

import sys
import tempfile

from cc_tts.config import TTSConfig, load_config
from cc_tts.engine import resolve_engine
from cc_tts.player import NoAudioDeviceError, play_audio
from cc_tts.preprocess import preprocess


def synthesize_and_play(text: str, config: TTSConfig | None = None) -> None:
    """Preprocess text, synthesize speech, and play audio."""
    config = config or load_config()
    text = preprocess(text, max_chars=config.max_chars)

    if not text:
        return

    engine = resolve_engine(config.engine)

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
