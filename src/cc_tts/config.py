"""Configuration loading from .cc-voice.toml [tts] section and environment variables."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAMES = [".cc-voice.toml"]


@dataclass
class TTSConfig:
    """TTS plugin configuration."""

    engine: str = "auto"
    voice: str = "en_US-amy-medium"
    speed: float = 1.0
    auto_read: bool = False
    max_chars: int = 2000
    player: str = "auto"


def _find_config_file() -> Path | None:
    """Walk up from cwd to find .cc-voice.toml."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        for filename in CONFIG_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    return None


def _apply_env_overrides(config: TTSConfig) -> None:
    """Override config fields from CC_TTS_* environment variables."""
    env_map: dict[str, str] = {
        "CC_TTS_ENGINE": "engine",
        "CC_TTS_VOICE": "voice",
        "CC_TTS_SPEED": "speed",
        "CC_TTS_AUTO_READ": "auto_read",
        "CC_TTS_MAX_CHARS": "max_chars",
        "CC_TTS_PLAYER": "player",
    }
    type_map: dict[str, type[int] | type[float] | type[bool] | type[str]] = {
        "speed": float,
        "max_chars": int,
        "auto_read": bool,
    }
    for env_var, attr in env_map.items():
        value = os.environ.get(env_var)
        if value is None:
            continue
        target_type = type_map.get(attr)
        if target_type is bool:
            setattr(config, attr, value.lower() in ("1", "true", "yes"))
        elif target_type is not None:
            setattr(config, attr, target_type(value))
        else:
            setattr(config, attr, value)


def load_config() -> TTSConfig:
    """Load config from .cc-voice.toml [tts] section with env var overrides."""
    config = TTSConfig()
    config_file = _find_config_file()
    if config_file is not None:
        with config_file.open("rb") as f:
            data = tomllib.load(f)
        tts_data = data.get("tts", {})
        for key, value in tts_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    _apply_env_overrides(config)
    return config
