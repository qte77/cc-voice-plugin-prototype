"""Task-constrained prompt templates for /see VLM calls.

Each template caps output length at the VLM source rather than at the
Claude side, minimizing tokens injected into the parent conversation.
"""

from __future__ import annotations

PROMPT_TEMPLATES: dict[str, str] = {
    "terminal": (
        "Read the terminal text. Report only: "
        "(1) the most recent command, "
        "(2) its exit status, "
        "(3) any error or warning text. "
        "Max 80 words. Fragments ok."
    ),
    "editor": (
        "Read the visible code. Report: "
        "(1) filename and language, "
        "(2) cursor line, "
        "(3) any red underlines or diagnostic messages. "
        "Max 100 words."
    ),
    "browser": (
        "Describe the page. Report: "
        "(1) page title, "
        "(2) main heading, "
        "(3) any error or success banner. "
        "Max 60 words."
    ),
    "gui": (
        "List visible UI state: "
        "(1) active window title, "
        "(2) focused element, "
        "(3) any modal or dialog text. "
        "Max 80 words."
    ),
    "generic": (
        "Describe what is shown on screen. Be specific and concise. Max 100 words. Fragments ok."
    ),
}


def get_template(name: str) -> str:
    """Return the prompt template by name.

    Raises ValueError for unknown template names, listing available names
    for helpful diagnostics.
    """
    if name not in PROMPT_TEMPLATES:
        available = ", ".join(sorted(PROMPT_TEMPLATES))
        msg = f"Unknown template: {name!r}. Available: {available}"
        raise ValueError(msg)
    return PROMPT_TEMPLATES[name]
