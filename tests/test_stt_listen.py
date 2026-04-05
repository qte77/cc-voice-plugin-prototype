"""Tests for cc_stt.listen — TDD RED phase."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from cc_stt.listen import listen_live, transcribe_file


class TestListenLive:
    @patch("cc_stt.listen.inject_text")
    @patch("cc_stt.listen.UtteranceBuffer")
    @patch("cc_stt.listen.MicCapture")
    @patch("cc_stt.listen.resolve_stt_engine")
    @patch("cc_stt.listen.load_stt_config")
    def test_listen_live_starts_mic_and_resolves_engine(
        self,
        mock_config: MagicMock,
        mock_resolve: MagicMock,
        mock_mic_cls: MagicMock,
        mock_buffer_cls: MagicMock,
        mock_inject: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()
        mock_engine = MagicMock(spec=True)
        mock_resolve.return_value = mock_engine

        mock_mic = MagicMock()
        mock_mic_cls.return_value = mock_mic

        stop = threading.Event()
        stop.set()  # Stop immediately

        listen_live(stop_event=stop)

        mock_resolve.assert_called_once()
        mock_mic_cls.assert_called_once()
        mock_mic.start.assert_called_once()

    @patch("cc_stt.listen.inject_text")
    @patch("cc_stt.listen.UtteranceBuffer")
    @patch("cc_stt.listen.MicCapture")
    @patch("cc_stt.listen.resolve_stt_engine")
    @patch("cc_stt.listen.load_stt_config")
    def test_listen_live_stop_event_stops_mic(
        self,
        mock_config: MagicMock,
        mock_resolve: MagicMock,
        mock_mic_cls: MagicMock,
        mock_buffer_cls: MagicMock,
        mock_inject: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()
        mock_resolve.return_value = MagicMock()

        mock_mic = MagicMock()
        mock_mic_cls.return_value = mock_mic

        stop = threading.Event()
        stop.set()

        listen_live(stop_event=stop)

        mock_mic.stop.assert_called_once()

    @patch("cc_stt.listen.inject_text")
    @patch("cc_stt.listen.UtteranceBuffer")
    @patch("cc_stt.listen.MicCapture")
    @patch("cc_stt.listen.resolve_stt_engine")
    @patch("cc_stt.listen.load_stt_config")
    def test_listen_live_injects_transcript_to_pty(
        self,
        mock_config: MagicMock,
        mock_resolve: MagicMock,
        mock_mic_cls: MagicMock,
        mock_buffer_cls: MagicMock,
        mock_inject: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = "hello world"
        mock_resolve.return_value = mock_engine

        mock_mic = MagicMock()
        mock_mic_cls.return_value = mock_mic

        # Capture the on_utterance callback from UtteranceBuffer
        captured_on_utterance = None

        def capture_buffer(*args: object, **kwargs: object) -> MagicMock:
            nonlocal captured_on_utterance
            captured_on_utterance = args[0] if args else kwargs.get("on_utterance")
            return MagicMock()

        mock_buffer_cls.side_effect = capture_buffer

        stop = threading.Event()
        stop.set()

        listen_live(pty_fd=42, stop_event=stop)

        # Simulate an utterance arriving
        assert captured_on_utterance is not None
        captured_on_utterance(b"\x00" * 100)

        mock_engine.transcribe.assert_called_once()
        mock_inject.assert_called_once_with(42, "hello world")

    @patch("cc_stt.listen.MicCapture")
    @patch("cc_stt.listen.resolve_stt_engine", side_effect=RuntimeError("No STT engine found"))
    @patch("cc_stt.listen.load_stt_config")
    def test_listen_live_handles_no_engine(
        self,
        mock_config: MagicMock,
        mock_resolve: MagicMock,
        mock_mic_cls: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()

        with pytest.raises(RuntimeError, match="No STT engine found"):
            listen_live()

    @patch("cc_stt.listen.resolve_stt_engine")
    @patch("cc_stt.listen.MicCapture", side_effect=RuntimeError("no input device"))
    @patch("cc_stt.listen.load_stt_config")
    def test_listen_live_handles_no_mic(
        self,
        mock_config: MagicMock,
        mock_mic_cls: MagicMock,
        mock_resolve: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()
        mock_resolve.return_value = MagicMock()

        with pytest.raises(RuntimeError, match="no input device"):
            listen_live()


class TestTranscribeFile:
    @patch("cc_stt.listen.resolve_stt_engine")
    @patch("cc_stt.listen.load_stt_config")
    def test_transcribe_file_returns_text(
        self,
        mock_config: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()
        mock_engine = MagicMock()
        mock_engine.transcribe.return_value = "transcribed text"
        mock_resolve.return_value = mock_engine

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 100)

        result = transcribe_file(str(audio_file))

        assert result == "transcribed text"
        mock_engine.transcribe.assert_called_once_with(str(audio_file))

    @patch("cc_stt.listen.load_stt_config")
    def test_transcribe_file_nonexistent_raises(
        self,
        mock_config: MagicMock,
    ) -> None:
        from cc_stt.config import STTConfig

        mock_config.return_value = STTConfig()

        with pytest.raises(FileNotFoundError):
            transcribe_file("/nonexistent/audio.wav")


class TestMainDispatch:
    @patch("cc_stt.listen.listen_live")
    def test_main_dispatches_listen(
        self,
        mock_listen: MagicMock,
    ) -> None:
        from cc_stt.__main__ import main

        with patch("sys.argv", ["cc-stt"]):
            main()

        mock_listen.assert_called_once()

    @patch("cc_stt.listen.transcribe_file", return_value="hello")
    def test_main_dispatches_file_transcription(
        self,
        mock_transcribe: MagicMock,
        tmp_path: Path,
    ) -> None:
        from cc_stt.__main__ import main

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 100)

        with patch("sys.argv", ["cc-stt", str(audio_file)]):
            main()

        mock_transcribe.assert_called_once_with(str(audio_file))
