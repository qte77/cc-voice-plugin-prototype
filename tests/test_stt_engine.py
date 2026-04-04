"""Tests for cc_stt.engine — TDD RED phase."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cc_stt.engine import (
    MoonshineEngine,
    STTEngine,
    VoskEngine,
    resolve_stt_engine,
)


class TestSTTEngineProtocol:
    def test_protocol_has_required_methods(self, tmp_path: Path) -> None:
        """STTEngine protocol requires transcribe, available, and name."""

        class FakeEngine:
            @property
            def name(self) -> str:
                return "fake"

            def available(self) -> bool:
                return True

            def transcribe(self, audio_path: str) -> str:
                return "hello"

        engine: STTEngine = FakeEngine()
        assert engine.name == "fake"
        assert engine.available() is True
        assert engine.transcribe(str(tmp_path / "test.wav")) == "hello"


class TestMoonshineEngine:
    def test_name(self) -> None:
        assert MoonshineEngine().name == "moonshine"

    @patch("shutil.which", return_value="/usr/bin/moonshine")
    def test_available_when_installed(self, mock_which: object) -> None:
        assert MoonshineEngine().available() is True

    @patch("shutil.which", return_value=None)
    def test_unavailable_when_missing(self, mock_which: object) -> None:
        assert MoonshineEngine().available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/moonshine")
    def test_transcribe_returns_text(
        self, mock_which: object, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(stdout=b"hello world\n", returncode=0)
        wav = str(tmp_path / "test.wav")
        engine = MoonshineEngine()
        result = engine.transcribe(wav)
        assert result == "hello world"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "moonshine"
        assert wav in cmd


class TestVoskEngine:
    def test_name(self) -> None:
        assert VoskEngine().name == "vosk"

    @patch("shutil.which", return_value="/usr/bin/vosk-transcriber")
    def test_available_when_installed(self, mock_which: object) -> None:
        assert VoskEngine().available() is True

    @patch("shutil.which", return_value=None)
    def test_unavailable_when_missing(self, mock_which: object) -> None:
        assert VoskEngine().available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/vosk-transcriber")
    def test_transcribe_returns_text(
        self, mock_which: object, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(stdout=b"test output\n", returncode=0)
        wav = str(tmp_path / "test.wav")
        engine = VoskEngine()
        result = engine.transcribe(wav)
        assert result == "test output"
        mock_run.assert_called_once()


class TestResolveSTTEngine:
    @patch("shutil.which", return_value=None)
    def test_raises_when_no_engine(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="No STT engine found"):
            resolve_stt_engine("auto")

    @patch("shutil.which", return_value=None)
    def test_raises_for_unknown_engine(self, mock_which: object) -> None:
        with pytest.raises(ValueError, match="Unknown engine"):
            resolve_stt_engine("nonexistent")

    @patch(
        "shutil.which",
        side_effect=lambda x: "/usr/bin/moonshine" if x == "moonshine" else None,
    )
    def test_auto_prefers_moonshine(self, mock_which: object) -> None:
        engine = resolve_stt_engine("auto")
        assert engine.name == "moonshine"

    @patch(
        "shutil.which",
        side_effect=lambda x: "/usr/bin/vosk-transcriber"
        if x == "vosk-transcriber"
        else None,
    )
    def test_auto_falls_back_to_vosk(self, mock_which: object) -> None:
        engine = resolve_stt_engine("auto")
        assert engine.name == "vosk"

    @patch("shutil.which", return_value=None)
    def test_explicit_unavailable_raises(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="not installed"):
            resolve_stt_engine("moonshine")
