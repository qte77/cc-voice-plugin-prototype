"""Tests for cc_vlm.engine — VLMEngine Protocol + OllamaVLMEngine + resolver."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cc_vlm.engine import OllamaVLMEngine, VLMEngine, resolve_vlm_engine


class TestVLMEngineProtocol:
    def test_protocol_shape(self, tmp_path: Path) -> None:
        """VLMEngine protocol requires describe, available, and name."""

        class FakeEngine:
            @property
            def name(self) -> str:
                return "fake"

            def available(self) -> bool:
                return True

            def describe(self, image_path: Path, prompt: str) -> str:
                return f"fake description of {image_path.name}"

        engine: VLMEngine = FakeEngine()
        img = tmp_path / "x.jpg"
        img.write_bytes(b"fake")
        assert engine.name == "fake"
        assert engine.available() is True
        assert engine.describe(img, "describe") == "fake description of x.jpg"


class TestOllamaVLMEngine:
    def test_name(self) -> None:
        assert OllamaVLMEngine().name == "ollama"

    def test_defaults(self) -> None:
        engine = OllamaVLMEngine()
        assert engine.endpoint == "http://localhost:11434"
        assert engine.model == "qwen2.5vl:3b"
        assert engine.timeout == 60.0

    def test_strips_trailing_slash_from_endpoint(self) -> None:
        engine = OllamaVLMEngine(endpoint="http://localhost:11434/")
        assert engine.endpoint == "http://localhost:11434"

    @patch("cc_vlm.engine.httpx.get")
    def test_available_when_daemon_responds(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(status_code=200)
        assert OllamaVLMEngine().available() is True
        mock_get.assert_called_once()
        assert "/api/tags" in mock_get.call_args[0][0]

    @patch("cc_vlm.engine.httpx.get")
    def test_unavailable_when_daemon_down(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = httpx.ConnectError("refused")
        assert OllamaVLMEngine().available() is False

    @patch("cc_vlm.engine.httpx.get")
    def test_unavailable_when_non_200(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(status_code=500)
        assert OllamaVLMEngine().available() is False

    @patch("cc_vlm.engine.httpx.post")
    def test_describe_sends_base64_image(self, mock_post: MagicMock, tmp_path: Path) -> None:
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-bytes")
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "A terminal window."}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        engine = OllamaVLMEngine()
        result = engine.describe(img_path, "Describe the screen.")

        assert result == "A terminal window."
        mock_post.assert_called_once()
        # Verify payload structure
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["model"] == "qwen2.5vl:3b"
        assert payload["prompt"] == "Describe the screen."
        assert payload["stream"] is False
        assert isinstance(payload["images"], list)
        assert len(payload["images"]) == 1
        # Should be base64 of the file bytes
        import base64

        expected_b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        assert payload["images"][0] == expected_b64

    @patch("cc_vlm.engine.httpx.post")
    def test_describe_strips_whitespace(self, mock_post: MagicMock, tmp_path: Path) -> None:
        img_path = tmp_path / "x.jpg"
        img_path.write_bytes(b"x")
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "  trimmed.  \n"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = OllamaVLMEngine().describe(img_path, "prompt")
        assert result == "trimmed."

    @patch("cc_vlm.engine.httpx.post")
    def test_describe_raises_on_missing_response_field(
        self, mock_post: MagicMock, tmp_path: Path
    ) -> None:
        img_path = tmp_path / "x.jpg"
        img_path.write_bytes(b"x")
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "model not loaded"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="missing 'response' field"):
            OllamaVLMEngine().describe(img_path, "prompt")


class TestResolveVLMEngine:
    @patch.object(OllamaVLMEngine, "available", return_value=True)
    def test_auto_returns_ollama_when_available(self, mock_available: MagicMock) -> None:
        engine = resolve_vlm_engine("auto")
        assert isinstance(engine, OllamaVLMEngine)

    @patch.object(OllamaVLMEngine, "available", return_value=False)
    def test_auto_raises_when_nothing_available(self, mock_available: MagicMock) -> None:
        with pytest.raises(RuntimeError, match="No VLM engine running"):
            resolve_vlm_engine("auto")

    @patch.object(OllamaVLMEngine, "available", return_value=True)
    def test_explicit_name(self, mock_available: MagicMock) -> None:
        engine = resolve_vlm_engine("ollama")
        assert isinstance(engine, OllamaVLMEngine)

    def test_unknown_engine_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown engine"):
            resolve_vlm_engine("nonexistent")

    @patch.object(OllamaVLMEngine, "available", return_value=False)
    def test_explicit_engine_not_running_raises(self, mock_available: MagicMock) -> None:
        with pytest.raises(RuntimeError, match="not running"):
            resolve_vlm_engine("ollama")
