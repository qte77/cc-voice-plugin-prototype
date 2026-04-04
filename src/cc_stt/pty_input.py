"""PTY text injection — writes transcribed text to master PTY fd."""

from __future__ import annotations

import os


def inject_text(master_fd: int, text: str, *, newline: bool = False) -> None:
    """Write text to master PTY fd so the child process receives it as stdin.

    Args:
        master_fd: File descriptor of the master side of a PTY pair.
        text: Text to inject. Stripped; empty text is a no-op.
        newline: If True, append a newline after the text.
    """
    text = text.strip()
    if not text:
        return
    payload = text.encode()
    if newline:
        payload += b"\n"
    os.write(master_fd, payload)
