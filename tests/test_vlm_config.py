"""Tests for cc_vlm.config — VLMConfig dataclass + TOML + env overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from cc_vlm.config import VLMConfig, _apply_env_overrides, load_vlm_config


class TestVLMConfigDefaults:
    def test_defaults(self) -> None:
        config = VLMConfig()
        assert config.engine == "auto"
        assert config.endpoint == "http://localhost:11434"
        assert config.model == "qwen2.5vl:3b"
        assert config.max_dimension == 768
        assert config.jpeg_quality == 85
        assert config.template == "generic"
        assert config.cache_size == 32


class TestEnvOverrides:
    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in [
            "CC_VLM_ENGINE",
            "CC_VLM_ENDPOINT",
            "CC_VLM_MODEL",
            "CC_VLM_MAX_DIMENSION",
            "CC_VLM_JPEG_QUALITY",
            "CC_VLM_TEMPLATE",
            "CC_VLM_CACHE_SIZE",
        ]:
            monkeypatch.delenv(var, raising=False)

    def test_string_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CC_VLM_ENGINE", "ollama")
        monkeypatch.setenv("CC_VLM_ENDPOINT", "http://192.168.1.10:11434")
        monkeypatch.setenv("CC_VLM_MODEL", "qwen3-vl:2b")
        monkeypatch.setenv("CC_VLM_TEMPLATE", "terminal")
        config = VLMConfig()
        _apply_env_overrides(config)
        assert config.engine == "ollama"
        assert config.endpoint == "http://192.168.1.10:11434"
        assert config.model == "qwen3-vl:2b"
        assert config.template == "terminal"

    def test_int_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CC_VLM_MAX_DIMENSION", "1024")
        monkeypatch.setenv("CC_VLM_JPEG_QUALITY", "75")
        monkeypatch.setenv("CC_VLM_CACHE_SIZE", "64")
        config = VLMConfig()
        _apply_env_overrides(config)
        assert config.max_dimension == 1024
        assert config.jpeg_quality == 75
        assert config.cache_size == 64

    def test_invalid_int_env_falls_back_to_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CC_VLM_MAX_DIMENSION", "not-a-number")
        config = VLMConfig()
        _apply_env_overrides(config)
        assert config.max_dimension == 768  # unchanged

    def test_env_missing_leaves_defaults(self) -> None:
        config = VLMConfig()
        _apply_env_overrides(config)
        assert config.engine == "auto"


class TestLoadVLMConfig:
    def test_no_config_file_returns_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        config = load_vlm_config()
        assert config.engine == "auto"
        assert config.model == "qwen2.5vl:3b"

    def test_loads_from_vlm_toml_section(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".cc-voice.toml").write_text(
            '[vlm]\nengine = "ollama"\nmodel = "qwen3-vl:2b"\nmax_dimension = 512\n'
        )
        monkeypatch.chdir(tmp_path)
        config = load_vlm_config()
        assert config.engine == "ollama"
        assert config.model == "qwen3-vl:2b"
        assert config.max_dimension == 512

    def test_env_overrides_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / ".cc-voice.toml").write_text('[vlm]\nengine = "ollama"\n')
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("CC_VLM_ENGINE", "llamacpp")
        config = load_vlm_config()
        assert config.engine == "llamacpp"

    def test_ignores_unknown_vlm_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".cc-voice.toml").write_text(
            '[vlm]\nengine = "ollama"\nunknown_field = "should_be_dropped"\n'
        )
        monkeypatch.chdir(tmp_path)
        config = load_vlm_config()
        assert config.engine == "ollama"
        assert not hasattr(config, "unknown_field")

    def test_legacy_cc_tts_toml_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".cc-tts.toml").write_text('[vlm]\nmodel = "from_legacy"\n')
        monkeypatch.chdir(tmp_path)
        config = load_vlm_config()
        assert config.model == "from_legacy"
