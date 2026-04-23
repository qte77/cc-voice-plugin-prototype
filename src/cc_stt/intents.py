"""Local intent matching — skip LLM for common dev commands."""

from __future__ import annotations

import re

# (compiled regex, action string or None to abort)
_INTENT_TABLE: list[tuple[re.Pattern[str], str | None]] = [
    (re.compile(r"run (?:the )?tests?", re.IGNORECASE), "make test"),
    (
        re.compile(r"show (?:me )?(?:the )?(?:last|recent) commit", re.IGNORECASE),
        "git log -1 --oneline",
    ),
    (re.compile(r"(?:what'?s|show) (?:the )?(?:git )?status", re.IGNORECASE), "git status -s"),
    (re.compile(r"^(?:cancel|stop|never ?mind)$", re.IGNORECASE), None),
]


def match_intent(text: str) -> tuple[bool, str | None]:
    """Match transcription against known dev command patterns.

    Returns:
        (matched, action) — matched=True if a pattern hit.
        action is the command string, or None for abort intents.
    """
    stripped = text.strip()
    for pattern, action in _INTENT_TABLE:
        if pattern.search(stripped):
            return (True, action)
    return (False, None)
