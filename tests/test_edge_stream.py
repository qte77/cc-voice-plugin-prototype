"""Tests for cc_tts.edge_stream — streaming TTS playback."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestPipeToPlayer:
    """Tests for _pipe_to_player: pipes engine stdout to audio player."""

    def _make_popen(self, returncode: int = 0) -> MagicMock:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = MagicMock()
        proc.wait.return_value = returncode
        return proc

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_launches_engine_and_player(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        engine_proc = self._make_popen()
        player_proc = self._make_popen()
        mock_popen.side_effect = [engine_proc, player_proc]

        from cc_tts.edge_stream import _pipe_to_player

        _pipe_to_player(["espeak-ng", "--stdout", "hello"])

        assert mock_popen.call_count == 2
        # Engine: stdout piped
        engine_call = mock_popen.call_args_list[0]
        assert engine_call[0][0] == ["espeak-ng", "--stdout", "hello"]
        assert engine_call[1]["stdin"] == __import__("subprocess").DEVNULL
        assert engine_call[1]["stdout"] == __import__("subprocess").PIPE
        # Player: stdin = engine stdout
        player_call = mock_popen.call_args_list[1]
        assert player_call[1]["stdin"] == engine_proc.stdout

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_writes_stdin_data_to_engine(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        engine_proc = self._make_popen()
        player_proc = self._make_popen()
        mock_popen.side_effect = [engine_proc, player_proc]

        from cc_tts.edge_stream import _pipe_to_player

        _pipe_to_player(["piper", "--output-raw"], stdin_data=b"hello world")

        engine_proc.stdin.write.assert_called_once_with(b"hello world")
        engine_proc.stdin.close.assert_called_once()

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_uses_pipe_stdin_when_stdin_data_given(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        import subprocess

        mock_detect.return_value = ("mpv", ["mpv"])
        engine_proc = self._make_popen()
        player_proc = self._make_popen()
        mock_popen.side_effect = [engine_proc, player_proc]

        from cc_tts.edge_stream import _pipe_to_player

        _pipe_to_player(["piper"], stdin_data=b"data")
        engine_call = mock_popen.call_args_list[0]
        assert engine_call[1]["stdin"] == subprocess.PIPE

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_terminates_on_keyboard_interrupt(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        engine_proc = self._make_popen()
        player_proc = self._make_popen()
        engine_proc.wait.side_effect = KeyboardInterrupt
        mock_popen.side_effect = [engine_proc, player_proc]

        from cc_tts.edge_stream import _pipe_to_player

        _pipe_to_player(["espeak-ng", "--stdout", "hello"])

        engine_proc.terminate.assert_called_once()
        player_proc.terminate.assert_called_once()

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_player_cmd_gets_dash_appended(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        engine_proc = self._make_popen()
        player_proc = self._make_popen()
        mock_popen.side_effect = [engine_proc, player_proc]

        from cc_tts.edge_stream import _pipe_to_player

        _pipe_to_player(["espeak-ng", "--stdout", "hi"])

        player_call = mock_popen.call_args_list[1]
        assert player_call[0][0][-1] == "-"


class TestStreamEspeak:
    """Tests for _stream_espeak: espeak/espeak-ng → player."""

    @patch("cc_tts.edge_stream._pipe_to_player")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_uses_espeak_ng_when_available(
        self, mock_which: MagicMock, mock_pipe: MagicMock
    ) -> None:
        mock_which.return_value = "/usr/bin/espeak-ng"

        from cc_tts.edge_stream import _stream_espeak

        _stream_espeak("hello", voice="en-us", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert cmd[0] == "espeak-ng"

    @patch("cc_tts.edge_stream._pipe_to_player")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_falls_back_to_espeak_when_ng_missing(
        self, mock_which: MagicMock, mock_pipe: MagicMock
    ) -> None:
        mock_which.return_value = None  # espeak-ng not found

        from cc_tts.edge_stream import _stream_espeak

        _stream_espeak("hello", voice="en-us", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert cmd[0] == "espeak"

    @patch("cc_tts.edge_stream._pipe_to_player")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_converts_speed_to_wpm(self, mock_which: MagicMock, mock_pipe: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/espeak-ng"

        from cc_tts.edge_stream import _stream_espeak

        _stream_espeak("hello", voice="en-us", speed=2.0)

        cmd = mock_pipe.call_args[0][0]
        wpm_idx = cmd.index("-s") + 1
        assert cmd[wpm_idx] == "350"  # int(175 * 2.0)

    @patch("cc_tts.edge_stream._pipe_to_player")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_replaces_underscore_voice_with_default(
        self, mock_which: MagicMock, mock_pipe: MagicMock
    ) -> None:
        mock_which.return_value = "/usr/bin/espeak-ng"

        from cc_tts.edge_stream import _stream_espeak

        _stream_espeak("hello", voice="en_US-amy-medium", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        v_idx = cmd.index("-v") + 1
        assert cmd[v_idx] == "en-us"

    @patch("cc_tts.edge_stream._pipe_to_player")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_text_is_last_argument(self, mock_which: MagicMock, mock_pipe: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/espeak-ng"

        from cc_tts.edge_stream import _stream_espeak

        _stream_espeak("speak this", voice="en-us", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert cmd[-1] == "speak this"


class TestStreamPiper:
    """Tests for _stream_piper: piper --output-raw → player."""

    @patch("cc_tts.edge_stream._pipe_to_player")
    def test_passes_text_as_stdin_data(self, mock_pipe: MagicMock) -> None:
        from cc_tts.edge_stream import _stream_piper

        _stream_piper("hello world", voice="en_US-amy-medium", speed=1.0)

        kwargs = mock_pipe.call_args[1]
        assert kwargs["stdin_data"] == b"hello world"

    @patch("cc_tts.edge_stream._pipe_to_player")
    def test_includes_output_raw_flag(self, mock_pipe: MagicMock) -> None:
        from cc_tts.edge_stream import _stream_piper

        _stream_piper("hello", voice="en_US-amy-medium", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert "--output-raw" in cmd

    @patch("cc_tts.edge_stream._pipe_to_player")
    def test_includes_model_when_voice_given(self, mock_pipe: MagicMock) -> None:
        from cc_tts.edge_stream import _stream_piper

        _stream_piper("hello", voice="en_US-amy-medium", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert "--model" in cmd
        assert "en_US-amy-medium" in cmd

    @patch("cc_tts.edge_stream._pipe_to_player")
    def test_includes_length_scale_when_speed_not_1(self, mock_pipe: MagicMock) -> None:
        from cc_tts.edge_stream import _stream_piper

        _stream_piper("hello", voice="", speed=2.0)

        cmd = mock_pipe.call_args[0][0]
        assert "--length-scale" in cmd
        ls_idx = cmd.index("--length-scale") + 1
        assert cmd[ls_idx] == "0.5"  # 1.0 / 2.0

    @patch("cc_tts.edge_stream._pipe_to_player")
    def test_omits_length_scale_at_default_speed(self, mock_pipe: MagicMock) -> None:
        from cc_tts.edge_stream import _stream_piper

        _stream_piper("hello", voice="", speed=1.0)

        cmd = mock_pipe.call_args[0][0]
        assert "--length-scale" not in cmd


class TestStreamKokoro:
    """Tests for _stream_kokoro: kokoro-tts --stream."""

    @patch("cc_tts.edge_stream.subprocess.run")
    @patch("cc_tts.engine._KOKORO_MODEL_DIR", new=Path("/fake/kokoro-models"))
    def test_runs_kokoro_tts_subprocess(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        from cc_tts.edge_stream import _stream_kokoro

        _stream_kokoro("hello", voice="af_sarah", speed=1.0)

        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "kokoro-tts"
        assert "--stream" in cmd

    @patch("cc_tts.edge_stream.subprocess.run")
    @patch("cc_tts.engine._KOKORO_MODEL_DIR", new=Path("/fake/kokoro-models"))
    def test_passes_voice_and_speed(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        from cc_tts.edge_stream import _stream_kokoro

        _stream_kokoro("test text", voice="af_sarah", speed=1.5)

        cmd = mock_run.call_args[0][0]
        assert "--voice" in cmd
        assert "af_sarah" in cmd
        assert "--speed" in cmd
        assert "1.5" in cmd

    @patch("cc_tts.edge_stream.subprocess.run")
    @patch("cc_tts.engine._KOKORO_MODEL_DIR", new=Path("/fake/kokoro-models"))
    def test_falls_back_to_default_voice_when_empty(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        from cc_tts.edge_stream import _stream_kokoro

        _stream_kokoro("test", voice="", speed=1.0)

        cmd = mock_run.call_args[0][0]
        v_idx = cmd.index("--voice") + 1
        assert cmd[v_idx] == "af_sarah"

    @patch("cc_tts.edge_stream.subprocess.run")
    @patch("cc_tts.engine._KOKORO_MODEL_DIR", new=Path("/fake/kokoro-models"))
    def test_cleans_up_temp_file_after_run(self, mock_run: MagicMock) -> None:
        import os

        mock_run.return_value = MagicMock(returncode=0)
        created_paths: list[str] = []

        def capture_path(cmd: list[str], **_: object) -> MagicMock:
            created_paths.append(cmd[1])  # txt_path is second arg
            return MagicMock(returncode=0)

        mock_run.side_effect = capture_path

        from cc_tts.edge_stream import _stream_kokoro

        _stream_kokoro("hello", voice="af_sarah", speed=1.0)

        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])

    @patch("cc_tts.edge_stream.subprocess.run")
    @patch("cc_tts.engine._KOKORO_MODEL_DIR", new=Path("/fake/kokoro-models"))
    def test_swallows_keyboard_interrupt(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = KeyboardInterrupt

        from cc_tts.edge_stream import _stream_kokoro

        # Must not raise
        _stream_kokoro("hello", voice="af_sarah", speed=1.0)


class TestStreamEdge:
    """Tests for _stream_edge: edge-tts async → player."""

    def _make_communicate(self, chunks: list[dict]) -> MagicMock:  # type: ignore[type-arg]
        communicate = MagicMock()

        async def fake_stream():  # type: ignore[return]
            for chunk in chunks:
                yield chunk

        communicate.stream.return_value = fake_stream()
        return communicate

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    @patch("cc_tts.edge_stream.shutil")
    def test_streams_audio_chunks_to_player(
        self,
        _mock_shutil: MagicMock,
        mock_popen: MagicMock,
        mock_detect: MagicMock,
    ) -> None:
        import edge_tts

        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        proc = MagicMock()
        proc.stdin = MagicMock()
        mock_popen.return_value = proc

        communicate = self._make_communicate(
            [
                {"type": "audio", "data": b"chunk1"},
                {"type": "audio", "data": b"chunk2"},
                {"type": "WordBoundary", "text": "hello"},
            ]
        )

        with patch.object(edge_tts, "Communicate", return_value=communicate):
            from cc_tts.edge_stream import _stream_edge

            _stream_edge("hello", voice="en-US-AriaNeural", speed=1.0)

        proc.stdin.write.assert_any_call(b"chunk1")
        proc.stdin.write.assert_any_call(b"chunk2")
        proc.stdin.close.assert_called_once()

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_rate_string_format(self, mock_popen: MagicMock, mock_detect: MagicMock) -> None:
        import edge_tts

        mock_detect.return_value = ("mpv", ["mpv", "--no-video"])
        proc = MagicMock()
        proc.stdin = MagicMock()
        mock_popen.return_value = proc

        communicate = self._make_communicate([])
        captured_rate: list[str] = []

        def capture_communicate(text: str, voice: str, rate: str) -> MagicMock:
            captured_rate.append(rate)
            return communicate

        with patch.object(edge_tts, "Communicate", side_effect=capture_communicate):
            from cc_tts.edge_stream import _stream_edge

            _stream_edge("hello", voice="en-US-AriaNeural", speed=1.5)

        assert captured_rate == ["+50%"]

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_uses_default_voice_for_non_neural(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        import edge_tts

        mock_detect.return_value = ("mpv", ["mpv"])
        proc = MagicMock()
        proc.stdin = MagicMock()
        mock_popen.return_value = proc

        communicate = self._make_communicate([])
        captured_voice: list[str] = []

        def capture_communicate(text: str, voice: str, rate: str) -> MagicMock:
            captured_voice.append(voice)
            return communicate

        with patch.object(edge_tts, "Communicate", side_effect=capture_communicate):
            from cc_tts.edge_stream import _stream_edge

            _stream_edge("hello", voice="af_sarah", speed=1.0)

        assert captured_voice == ["en-US-AriaNeural"]

    @patch("cc_tts.edge_stream._detect_player")
    @patch("subprocess.Popen")
    def test_terminates_on_keyboard_interrupt(
        self, mock_popen: MagicMock, mock_detect: MagicMock
    ) -> None:
        import edge_tts

        mock_detect.return_value = ("mpv", ["mpv"])
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.wait.side_effect = KeyboardInterrupt
        mock_popen.return_value = proc

        communicate = self._make_communicate([])

        with patch.object(edge_tts, "Communicate", return_value=communicate):
            from cc_tts.edge_stream import _stream_edge

            _stream_edge("hello", voice="en-US-AriaNeural", speed=1.0)

        proc.terminate.assert_called_once()


class TestSpeakStreaming:
    """Tests for speak_streaming: main dispatch entry point."""

    @patch("cc_tts.edge_stream._stream_edge")
    @patch("cc_tts.edge_stream.shutil.which")
    @patch("cc_tts.edge_stream.preprocess", return_value="hello world", create=True)
    def test_dispatches_to_edge_when_explicit(
        self,
        _mock_preprocess: MagicMock,
        mock_which: MagicMock,
        mock_edge: MagicMock,
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello world"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello world", engine="edge")

        mock_edge.assert_called_once()

    @patch("cc_tts.edge_stream._stream_edge")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_dispatches_edge_tts_alias(self, mock_which: MagicMock, mock_edge: MagicMock) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="edge-tts")

        mock_edge.assert_called_once()

    @patch("cc_tts.edge_stream._stream_kokoro")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_dispatches_to_kokoro_when_explicit(
        self, mock_which: MagicMock, mock_kokoro: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="kokoro")

        mock_kokoro.assert_called_once()

    @patch("cc_tts.edge_stream._stream_espeak")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_dispatches_to_espeak_when_explicit(
        self, mock_which: MagicMock, mock_espeak: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="espeak")

        mock_espeak.assert_called_once()

    @patch("cc_tts.edge_stream._stream_espeak")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_dispatches_espeak_ng_alias(
        self, mock_which: MagicMock, mock_espeak: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="espeak-ng")

        mock_espeak.assert_called_once()

    @patch("cc_tts.edge_stream._stream_piper")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_dispatches_to_piper_when_explicit(
        self, mock_which: MagicMock, mock_piper: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="piper")

        mock_piper.assert_called_once()

    @patch("cc_tts.edge_stream._stream_kokoro")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_auto_picks_kokoro_when_available(
        self, mock_which: MagicMock, mock_kokoro: MagicMock
    ) -> None:
        mock_which.side_effect = lambda name: (
            "/usr/bin/kokoro-tts" if name == "kokoro-tts" else None
        )

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="auto")

        mock_kokoro.assert_called_once()

    @patch("cc_tts.edge_stream._stream_piper")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_auto_falls_back_to_piper(self, mock_which: MagicMock, mock_piper: MagicMock) -> None:
        mock_which.side_effect = lambda name: "/usr/bin/piper" if name == "piper" else None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="auto")

        mock_piper.assert_called_once()

    @patch("cc_tts.edge_stream._stream_espeak")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_auto_falls_back_to_espeak(self, mock_which: MagicMock, mock_espeak: MagicMock) -> None:
        mock_which.side_effect = lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", engine="auto")

        mock_espeak.assert_called_once()

    @patch("cc_tts.edge_stream._stream_edge")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_auto_falls_back_to_edge_when_no_local(
        self, mock_which: MagicMock, mock_edge: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            with patch.dict("sys.modules", {"edge_tts": MagicMock()}):
                from cc_tts.edge_stream import speak_streaming

                speak_streaming("hello", engine="auto")

        mock_edge.assert_called_once()

    @patch("cc_tts.edge_stream.shutil.which")
    def test_returns_early_on_empty_text(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value=""):
            with patch("cc_tts.edge_stream._stream_edge") as mock_edge:
                from cc_tts.edge_stream import speak_streaming

                speak_streaming("   ", engine="edge")

            mock_edge.assert_not_called()

    @patch("cc_tts.edge_stream.shutil.which")
    def test_calls_preprocess_to_strip_markdown(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="cleaned text") as mock_pre:
            with patch("cc_tts.edge_stream._stream_edge"):
                from cc_tts.edge_stream import speak_streaming

                speak_streaming("# Heading\n\nBody text", engine="edge")

            mock_pre.assert_called_once_with("# Heading\n\nBody text")

    @patch("cc_tts.edge_stream._stream_edge")
    @patch("cc_tts.edge_stream.shutil.which")
    def test_passes_voice_and_speed_through(
        self, mock_which: MagicMock, mock_edge: MagicMock
    ) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            from cc_tts.edge_stream import speak_streaming

            speak_streaming("hello", voice="en-US-GuyNeural", speed=1.75, engine="edge")

        mock_edge.assert_called_once_with("hello", voice="en-US-GuyNeural", speed=1.75)

    @patch("cc_tts.edge_stream.shutil.which")
    def test_unknown_engine_falls_back_to_synthesize_and_play(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None

        with patch("cc_tts.preprocess.preprocess", return_value="hello"):
            with patch("cc_tts.config.load_config"):
                with patch("cc_tts.speak.synthesize_and_play") as mock_sap:
                    from cc_tts.edge_stream import speak_streaming

                    speak_streaming("hello", engine="unknown-engine")

        mock_sap.assert_called_once()
