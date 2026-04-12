"""Configuration loading from .cc-voice.toml [stt] section and environment variables."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAMES = [".cc-voice.toml"]


@dataclass
class STTConfig:
    """STT plugin configuration."""

    engine: str = "auto"
    language: str = "en"
    wake_word: str = "hey_claude"
    mic_device: str = "default"
    auto_listen: bool = False


def _find_config_file() -> Path | None:
    """Walk up from cwd to find .cc-voice.toml."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        for filename in CONFIG_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    return None


def _apply_env_overrides(config: STTConfig) -> None:
    """Override config fields from CC_STT_* environment variables."""
    env_map: dict[str, str] = {
        "CC_STT_ENGINE": "engine",
        "CC_STT_LANGUAGE": "language",
        "CC_STT_WAKE_WORD": "wake_word",
        "CC_STT_MIC_DEVICE": "mic_device",
        "CC_STT_AUTO_LISTEN": "auto_listen",
    }
    type_map: dict[str, type[bool]] = {
        "auto_listen": bool,
    }
    for env_var, attr in env_map.items():
        value = os.environ.get(env_var)
        if value is None:
            continue
        target_type = type_map.get(attr)
        if target_type is bool:
            setattr(config, attr, value.lower() in ("1", "true", "yes"))
        else:
            setattr(config, attr, value)


def load_stt_config() -> STTConfig:
    """Load STT config from [stt] section of .cc-voice.toml with env var overrides."""
    config = STTConfig()
    config_file = _find_config_file()
    if config_file is not None:
        with config_file.open("rb") as f:
            data = tomllib.load(f)
        stt_data = data.get("stt", {})
        for key, value in stt_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    _apply_env_overrides(config)
    return config
