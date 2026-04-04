"""Tests for cc_stt.mic — TDD RED phase."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cc_stt.mic import MicCapture, NoMicrophoneError


class TestNoMicrophoneError:
    def test_is_runtime_error(self) -> None:
        assert issubclass(NoMicrophoneError, RuntimeError)

    def test_message(self) -> None:
        err = NoMicrophoneError("no mic found")
        assert str(err) == "no mic found"


class TestMicCaptureInit:
    @patch("cc_stt.mic._check_sounddevice", side_effect=ImportError("no sounddevice"))
    def test_raises_when_sounddevice_missing(self, mock_check: object) -> None:
        with pytest.raises(ImportError, match="no sounddevice"):
            MicCapture()

    @patch("cc_stt.mic._check_sounddevice")
    @patch("cc_stt.mic._query_devices", side_effect=NoMicrophoneError("no input device"))
    def test_raises_when_no_input_device(
        self, mock_query: object, mock_check: object
    ) -> None:
        with pytest.raises(NoMicrophoneError, match="no input device"):
            MicCapture()

    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_creates_with_default_device(
        self, mock_check: object, mock_query: object
    ) -> None:
        mic = MicCapture()
        assert mic.device == "default"
        assert mic.sample_rate == 16000


class TestMicCaptureCallback:
    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_on_audio_receives_frames(
        self, mock_check: object, mock_query: object
    ) -> None:
        received: list[bytes] = []
        mic = MicCapture(on_audio=received.append)

        import numpy as np

        fake_audio = np.zeros((1600, 1), dtype="float32")
        mic._callback(fake_audio, 1600, None, None)
        assert len(received) == 1
        assert received[0] == fake_audio.tobytes()

    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_default_callback_is_noop(
        self, mock_check: object, mock_query: object
    ) -> None:
        mic = MicCapture()
        import numpy as np

        fake_audio = np.zeros((1600, 1), dtype="float32")
        # Should not raise
        mic._callback(fake_audio, 1600, None, None)


class TestMicCaptureStartStop:
    @patch("cc_stt.mic._open_stream")
    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_start_opens_stream(
        self, mock_check: object, mock_query: object, mock_open: MagicMock
    ) -> None:
        mic = MicCapture()
        mic.start()
        mock_open.assert_called_once()
        assert mic.is_active is True

    @patch("cc_stt.mic._open_stream")
    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_stop_closes_stream(
        self, mock_check: object, mock_query: object, mock_open: MagicMock
    ) -> None:
        mock_stream = MagicMock()
        mock_open.return_value = mock_stream
        mic = MicCapture()
        mic.start()
        mic.stop()
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
        assert mic.is_active is False

    @patch("cc_stt.mic._query_devices", return_value="default")
    @patch("cc_stt.mic._check_sounddevice")
    def test_stop_without_start_is_noop(
        self, mock_check: object, mock_query: object
    ) -> None:
        mic = MicCapture()
        mic.stop()  # Should not raise
        assert mic.is_active is False
