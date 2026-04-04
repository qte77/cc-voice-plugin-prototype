"""Tests for cc_tts.player — TDD RED phase."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cc_tts.player import NoAudioDeviceError, play_audio


class TestPlayAudio:
    @patch("shutil.which", return_value=None)
    def test_raises_when_no_player(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="No audio player found"):
            play_audio("/tmp/test.wav")

    @patch("subprocess.Popen")
    @patch("shutil.which", side_effect=lambda x: "/usr/bin/mpv" if x == "mpv" else None)
    def test_nonblocking_returns_popen(self, mock_which: object, mock_popen: object) -> None:
        result = play_audio("/tmp/test.wav")
        assert result is not None
        mock_popen.assert_called_once()  # type: ignore[union-attr]

    @patch("subprocess.run")
    @patch("shutil.which", side_effect=lambda x: "/usr/bin/mpv" if x == "mpv" else None)
    def test_blocking_returns_none(self, mock_which: object, mock_run: MagicMock) -> None:
        mock_run.return_value.returncode = 0
        result = play_audio("/tmp/test.wav", blocking=True)
        assert result is None
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("shutil.which", side_effect=lambda x: "/usr/bin/mpv" if x == "mpv" else None)
    def test_raises_no_audio_device(self, mock_which: object, mock_run: MagicMock) -> None:
        mock_run.return_value.returncode = 2
        mock_run.return_value.stderr = b"ALSA lib: cannot find card"
        with pytest.raises(NoAudioDeviceError, match="No audio device"):
            play_audio("/tmp/test.wav", blocking=True)

    @patch("shutil.which", side_effect=lambda x: "/usr/bin/mpv" if x == "mpv" else None)
    def test_raises_for_unknown_player(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="not found"):
            play_audio("/tmp/test.wav", player="nonexistent")
