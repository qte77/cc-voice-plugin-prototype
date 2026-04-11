"""VLM engine abstraction and implementations.

Mirrors cc_stt.engine's Protocol + resolver pattern. MVP ships only
OllamaVLMEngine; LlamaCppServerVLMEngine and ClaudeVisionEngine are
deferred to follow-up PRs.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Protocol

import httpx


class VLMEngine(Protocol):
    """Protocol for vision-language model backends.

    describe() returns a text string suitable for injection into Claude's
    prompt context. For local VLMs the string is the actual image
    description; for the deferred ClaudeVisionEngine it would be a file
    path reference for Claude's built-in vision to pick up.
    """

    def describe(self, image_path: Path, prompt: str) -> str: ...

    def available(self) -> bool: ...

    @property
    def name(self) -> str: ...


class OllamaVLMEngine:
    """Ollama-backed VLM engine.

    POSTs base64-encoded screenshots to a user-managed Ollama daemon at
    the configured endpoint (default http://localhost:11434). The daemon
    runs any pulled vision model (qwen2.5vl:3b, moondream, llava, etc.).

    Run `ollama serve` + `ollama pull <model>` before invoking.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "qwen2.5vl:3b",
        timeout: float = 60.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    def available(self) -> bool:
        """Check whether the Ollama daemon is reachable."""
        try:
            response = httpx.get(f"{self.endpoint}/api/tags", timeout=2.0)
        except (httpx.HTTPError, OSError):
            return False
        return response.status_code == 200

    def describe(self, image_path: Path, prompt: str) -> str:
        """Send image + prompt to Ollama, return the text response.

        Raises httpx.HTTPError on transport failure and raises
        RuntimeError if the response is missing the expected `response`
        field.
        """
        image_bytes = image_path.read_bytes()
        b64 = base64.b64encode(image_bytes).decode("ascii")
        response = httpx.post(
            f"{self.endpoint}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("response")
        if not isinstance(text, str):
            msg = f"Ollama response missing 'response' field: {payload}"
            raise RuntimeError(msg)
        return text.strip()


_ENGINE_TYPES: list[type[OllamaVLMEngine]] = [OllamaVLMEngine]


def resolve_vlm_engine(engine_name: str = "auto") -> VLMEngine:
    """Resolve a VLM engine by name or auto-detect first available.

    Auto-detect order: Ollama (only MVP engine). Future: llamacpp-server,
    claude-vision fallback.
    """
    name_map: dict[str, type[OllamaVLMEngine]] = {"ollama": OllamaVLMEngine}

    if engine_name != "auto":
        cls = name_map.get(engine_name)
        if cls is None:
            msg = f"Unknown engine: {engine_name}. Available: {', '.join(name_map)}"
            raise ValueError(msg)
        engine = cls()
        if not engine.available():
            msg = (
                f"Engine '{engine_name}' is not running at {engine.endpoint}. "
                "Start Ollama: `ollama serve` then `ollama pull qwen2.5vl:3b`."
            )
            raise RuntimeError(msg)
        return engine

    for cls in _ENGINE_TYPES:
        engine = cls()
        if engine.available():
            return engine

    msg = (
        "No VLM engine running. Start Ollama: `ollama serve` then "
        "`ollama pull qwen2.5vl:3b`, or set CC_VLM_ENDPOINT to an alternative host."
    )
    raise RuntimeError(msg)
