"""Tests for cc_stt.hook_handler — TDD RED phase."""

from __future__ import annotations

from unittest.mock import patch

from cc_stt.hook_handler import should_auto_listen


class TestShouldAutoListen:
    @patch("cc_stt.hook_handler.load_stt_config")
    def test_returns_true_when_auto_listen_enabled(self, mock_config: object) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig(auto_listen=True)  # type: ignore[attr-defined]
        assert should_auto_listen() is True

    @patch("cc_stt.hook_handler.load_stt_config")
    def test_returns_false_when_auto_listen_disabled(self, mock_config: object) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig(auto_listen=False)  # type: ignore[attr-defined]
        assert should_auto_listen() is False

    @patch("cc_stt.hook_handler.load_stt_config")
    def test_returns_false_on_config_error(self, mock_config: object) -> None:
        mock_config.side_effect = Exception("config broken")  # type: ignore[attr-defined]
        assert should_auto_listen() is False
