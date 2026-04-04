"""Tests for cc_tts.speak — TDD RED phase."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from cc_tts.speak import synthesize_and_play


class TestSynthesizeAndPlay:
    @patch("cc_tts.speak.play_audio")
    @patch("cc_tts.speak.resolve_engine")
    @patch("cc_tts.speak.preprocess", side_effect=lambda t, **kw: t)
    @patch("cc_tts.speak.load_config")
    def test_calls_engine_and_player(
        self,
        mock_config: MagicMock,
        mock_preprocess: MagicMock,
        mock_resolve: MagicMock,
        mock_play: MagicMock,
    ) -> None:
        from cc_tts.config import TTSConfig

        mock_config.return_value = TTSConfig()
        mock_engine = MagicMock()
        mock_resolve.return_value = mock_engine

        synthesize_and_play("Hello world")

        mock_engine.synthesize.assert_called_once()
        mock_play.assert_called_once()

    @patch("cc_tts.speak.play_audio")
    @patch("cc_tts.speak.resolve_engine")
    @patch("cc_tts.speak.preprocess", side_effect=lambda t, **kw: t)
    @patch("cc_tts.speak.load_config")
    def test_passes_voice_and_speed(
        self,
        mock_config: MagicMock,
        mock_preprocess: MagicMock,
        mock_resolve: MagicMock,
        mock_play: MagicMock,
    ) -> None:
        from cc_tts.config import TTSConfig

        mock_config.return_value = TTSConfig(voice="en_GB-alan", speed=1.5)
        mock_engine = MagicMock()
        mock_resolve.return_value = mock_engine

        synthesize_and_play("test")

        call_kwargs = mock_engine.synthesize.call_args
        assert call_kwargs.kwargs["voice"] == "en_GB-alan"
        assert call_kwargs.kwargs["speed"] == 1.5

    @patch("cc_tts.speak.play_audio")
    @patch("cc_tts.speak.resolve_engine")
    @patch("cc_tts.speak.preprocess", return_value="cleaned")
    @patch("cc_tts.speak.load_config")
    def test_preprocesses_text(
        self,
        mock_config: MagicMock,
        mock_preprocess: MagicMock,
        mock_resolve: MagicMock,
        mock_play: MagicMock,
    ) -> None:
        from cc_tts.config import TTSConfig

        mock_config.return_value = TTSConfig()
        mock_engine = MagicMock()
        mock_resolve.return_value = mock_engine

        synthesize_and_play("raw **markdown** text")

        mock_preprocess.assert_called_once()
        assert mock_engine.synthesize.call_args[0][0] == "cleaned"
