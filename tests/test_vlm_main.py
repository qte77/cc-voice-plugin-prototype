"""Tests for cc_vlm.__main__ — CLI dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from cc_vlm.__main__ import main
from cc_vlm.config import VLMConfig


def _fake_image() -> Image.Image:
    return Image.new("RGB", (100, 100), color=(128, 128, 128))


class TestMainCaptureAndDescribe:
    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_default_invocation(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        engine = MagicMock()
        engine.describe.return_value = "default description"
        mock_resolve.return_value = engine

        exit_code = main([])

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "default description" in out

    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_template_override(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig(template="generic")
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        engine = MagicMock()
        engine.describe.return_value = "terminal output"
        mock_resolve.return_value = engine

        exit_code = main(["--template", "terminal"])

        assert exit_code == 0
        # Engine should have received the terminal prompt, not the generic one
        call_args = engine.describe.call_args
        assert "terminal" in call_args[0][1].lower()


class TestMainSaveOnly:
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_save_only_prints_path_and_skips_vlm(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()

        exit_code = main(["--save-only"])

        assert exit_code == 0
        out = capsys.readouterr().out.strip()
        assert out.endswith(".jpg")
        assert Path(out).exists()


class TestMainNoCacheFlag:
    @patch("cc_vlm.__main__.describe_with_cache")
    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_no_cache_calls_engine_directly(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        mock_describe_with_cache: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        engine = MagicMock()
        engine.describe.return_value = "direct call"
        mock_resolve.return_value = engine

        exit_code = main(["--no-cache"])

        assert exit_code == 0
        engine.describe.assert_called_once()
        mock_describe_with_cache.assert_not_called()

    @patch("cc_vlm.__main__.describe_with_cache")
    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_default_uses_cache(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        mock_describe_with_cache: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        engine = MagicMock()
        mock_resolve.return_value = engine
        mock_describe_with_cache.return_value = "cached result"

        exit_code = main([])

        assert exit_code == 0
        mock_describe_with_cache.assert_called_once()


class TestMainErrorHandling:
    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_engine_not_available_returns_1(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        mock_resolve.side_effect = RuntimeError("No VLM engine running")

        exit_code = main([])

        assert exit_code == 1
        err = capsys.readouterr().err
        assert "No VLM engine running" in err

    @patch("cc_vlm.__main__.resolve_vlm_engine")
    @patch("cc_vlm.__main__.load_vlm_config")
    @patch("cc_vlm.__main__.ScreenCapture")
    def test_engine_describe_error_returns_1(
        self,
        mock_capture_cls: MagicMock,
        mock_load_config: MagicMock,
        mock_resolve: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_load_config.return_value = VLMConfig()
        mock_capture_cls.return_value.grab.return_value = _fake_image()
        engine = MagicMock()
        engine.describe.side_effect = RuntimeError("model not loaded")
        mock_resolve.return_value = engine

        exit_code = main(["--no-cache"])

        assert exit_code == 1
        err = capsys.readouterr().err
        assert "model not loaded" in err
