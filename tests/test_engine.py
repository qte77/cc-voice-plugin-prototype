"""Tests for cc_tts.engine — TDD RED phase."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cc_tts.engine import EspeakEngine, KokoroEngine, PiperEngine, resolve_engine


class TestEspeakEngine:
    def test_name(self) -> None:
        assert EspeakEngine().name == "espeak-ng"

    @patch("shutil.which", return_value="/usr/bin/espeak-ng")
    def test_available_when_installed(self, mock_which: object) -> None:
        assert EspeakEngine().available() is True

    @patch("shutil.which", return_value=None)
    def test_unavailable_when_missing(self, mock_which: object) -> None:
        assert EspeakEngine().available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/espeak-ng")
    def test_synthesize_calls_espeak(self, mock_which: object, mock_run: object) -> None:
        engine = EspeakEngine()
        engine.synthesize("hello", "/tmp/out.wav", voice="en", speed=1.0)
        mock_run.assert_called_once()  # type: ignore[union-attr]
        cmd = mock_run.call_args[0][0]  # type: ignore[union-attr]
        assert cmd[0] == "espeak-ng"
        assert "-w" in cmd
        assert "hello" in cmd

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/espeak-ng")
    def test_synthesize_ignores_piper_voice(self, mock_which: object, mock_run: object) -> None:
        engine = EspeakEngine()
        engine.synthesize("hello", "/tmp/out.wav", voice="en_US-amy-medium")
        cmd = mock_run.call_args[0][0]  # type: ignore[union-attr]
        assert "en_US-amy-medium" not in cmd
        assert "en-us" in cmd


class TestPiperEngine:
    def test_name(self) -> None:
        assert PiperEngine().name == "piper"

    @patch("shutil.which", return_value="/usr/bin/piper")
    def test_available_when_installed(self, mock_which: object) -> None:
        assert PiperEngine().available() is True

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/piper")
    def test_synthesize_pipes_text(self, mock_which: object, mock_run: object) -> None:
        engine = PiperEngine()
        engine.synthesize("hello", "/tmp/out.wav")
        mock_run.assert_called_once()  # type: ignore[union-attr]
        assert mock_run.call_args.kwargs.get("input") == b"hello"  # type: ignore[union-attr]


class TestKokoroEngine:
    def test_name(self) -> None:
        assert KokoroEngine().name == "kokoro"

    @patch("shutil.which", return_value="/usr/bin/kokoro-tts")
    def test_available_when_installed(self, mock_which: object) -> None:
        assert KokoroEngine().available() is True

    @patch("shutil.which", return_value=None)
    def test_unavailable_when_missing(self, mock_which: object) -> None:
        assert KokoroEngine().available() is False

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/kokoro-tts")
    def test_synthesize_writes_to_file(self, mock_which: object, mock_run: object) -> None:
        engine = KokoroEngine()
        engine.synthesize("hello", "/tmp/out.wav", voice="af_sarah")
        mock_run.assert_called_once()  # type: ignore[union-attr]
        cmd = mock_run.call_args[0][0]  # type: ignore[union-attr]
        assert cmd[0] == "kokoro-tts"
        assert "/tmp/out.wav" in cmd


class TestResolveEngine:
    @patch("shutil.which", return_value=None)
    def test_raises_when_no_engine(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="No TTS engine found"):
            resolve_engine("auto")

    @patch("shutil.which", return_value=None)
    def test_raises_for_unknown_engine(self, mock_which: object) -> None:
        with pytest.raises(ValueError, match="Unknown engine"):
            resolve_engine("nonexistent")

    @patch(
        "shutil.which", side_effect=lambda x: "/usr/bin/kokoro-tts" if x == "kokoro-tts" else None
    )
    def test_auto_prefers_kokoro(self, mock_which: object) -> None:
        engine = resolve_engine("auto")
        assert engine.name == "kokoro"

    @patch("shutil.which", side_effect=lambda x: "/usr/bin/espeak-ng" if x == "espeak-ng" else None)
    def test_auto_falls_back_to_espeak(self, mock_which: object) -> None:
        engine = resolve_engine("auto")
        assert engine.name == "espeak-ng"

    @patch("shutil.which", return_value=None)
    def test_explicit_unavailable_raises(self, mock_which: object) -> None:
        with pytest.raises(RuntimeError, match="not installed"):
            resolve_engine("espeak")
