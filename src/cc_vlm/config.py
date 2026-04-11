"""Configuration loading from .cc-voice.toml [vlm] section and environment variables.

Mirrors cc_stt.config exactly — same file-walk search, same env override
mechanism, same dataclass defaults pattern.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILENAMES = [".cc-voice.toml", ".cc-tts.toml"]


@dataclass
class VLMConfig:
    """VLM plugin configuration."""

    engine: str = "auto"
    endpoint: str = "http://localhost:11434"
    model: str = "qwen2.5vl:3b"
    max_dimension: int = 768
    jpeg_quality: int = 85
    template: str = "generic"
    cache_size: int = 32


def _find_config_file() -> Path | None:
    """Walk up from cwd to find .cc-voice.toml (or legacy .cc-tts.toml)."""
    current = Path.cwd()
    for directory in [current, *current.parents]:
        for filename in CONFIG_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    return None


def _apply_env_overrides(config: VLMConfig) -> None:
    """Override config fields from CC_VLM_* environment variables."""
    env_map: dict[str, str] = {
        "CC_VLM_ENGINE": "engine",
        "CC_VLM_ENDPOINT": "endpoint",
        "CC_VLM_MODEL": "model",
        "CC_VLM_MAX_DIMENSION": "max_dimension",
        "CC_VLM_JPEG_QUALITY": "jpeg_quality",
        "CC_VLM_TEMPLATE": "template",
        "CC_VLM_CACHE_SIZE": "cache_size",
    }
    int_fields = {"max_dimension", "jpeg_quality", "cache_size"}
    for env_var, attr in env_map.items():
        value = os.environ.get(env_var)
        if value is None:
            continue
        if attr in int_fields:
            try:
                setattr(config, attr, int(value))
            except ValueError:
                # Reason: bad env input falls back to current default rather than crash
                continue
        else:
            setattr(config, attr, value)


def load_vlm_config() -> VLMConfig:
    """Load VLM config from [vlm] section of .cc-voice.toml with env var overrides."""
    config = VLMConfig()
    config_file = _find_config_file()
    if config_file is not None:
        with config_file.open("rb") as f:
            data = tomllib.load(f)
        vlm_data = data.get("vlm", {})
        for key, value in vlm_data.items():
            if hasattr(config, key):
                setattr(config, key, value)
    _apply_env_overrides(config)
    return config
