"""Audio playback with auto-detected player and fallback chain."""

from __future__ import annotations

import platform
import shutil
import subprocess


_PLAYERS: list[tuple[str, list[str]]] = [
    ("mpv", ["mpv", "--no-video", "--no-terminal"]),
    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ("play", ["play", "-q"]),
]

if platform.system() == "Linux":
    _PLAYERS.append(("aplay", ["aplay", "-q"]))
elif platform.system() == "Darwin":
    _PLAYERS.append(("afplay", ["afplay"]))


def _detect_player(preference: str = "auto") -> tuple[str, list[str]]:
    """Find the best available audio player."""
    if preference != "auto":
        for name, cmd in _PLAYERS:
            if name == preference and shutil.which(cmd[0]) is not None:
                return name, cmd
        msg = f"Player '{preference}' not found"
        raise RuntimeError(msg)

    for name, cmd in _PLAYERS:
        if shutil.which(cmd[0]) is not None:
            return name, cmd

    msg = "No audio player found. Install mpv, ffplay, sox, aplay, or afplay."
    raise RuntimeError(msg)


def play_audio(
    path: str, *, player: str = "auto", blocking: bool = False
) -> subprocess.Popen[bytes] | None:
    """Play an audio file. Returns Popen handle if non-blocking, None if blocking."""
    _, cmd = _detect_player(player)
    full_cmd = [*cmd, path]

    if blocking:
        subprocess.run(full_cmd, check=True, capture_output=True)
        return None

    return subprocess.Popen(
        full_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
