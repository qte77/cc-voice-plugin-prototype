"""STT text preprocessing — filler stripping and word capping."""

from __future__ import annotations

import re

# Filler words/phrases to strip (word-boundary anchored, case-insensitive)
_FILLER_PATTERNS = [
    r"\b(?:um|uh|erm|hmm)\b",
    r"\b(?:you know|i mean|like)\b",
    r"\b(?:basically|actually|literally)\b",
    r"\b(?:so|well|right|okay)\b",
]
_FILLER_RE = re.compile("|".join(_FILLER_PATTERNS), re.IGNORECASE)


def strip_fillers(text: str) -> str:
    """Remove common speech disfluencies and filler words."""
    text = _FILLER_RE.sub("", text)
    # Collapse multiple spaces left by removals
    text = re.sub(r"  +", " ", text)
    return text.strip()


def cap_words(text: str, max_words: int = 200) -> str:
    """Truncate text to max_words, appending [truncated] if capped."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " [truncated]"
