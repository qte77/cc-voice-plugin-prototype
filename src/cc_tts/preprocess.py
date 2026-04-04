"""Text preprocessing for clean TTS output."""

from __future__ import annotations

import re


def preprocess(text: str, *, max_chars: int = 2000) -> str:
    """Strip markdown, code blocks, URLs for natural speech output."""
    # Fenced code blocks → placeholder
    text = re.sub(r"```[\s\S]*?```", " code block omitted ", text)

    # Inline code
    text = re.sub(r"`[^`]+`", lambda m: m.group(0).strip("`"), text)

    # URLs
    text = re.sub(r"https?://\S+", "link", text)

    # Markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Bold and italic
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"  +", " ", text)

    text = text.strip()

    if len(text) > max_chars:
        text = text[:max_chars]

    return text
