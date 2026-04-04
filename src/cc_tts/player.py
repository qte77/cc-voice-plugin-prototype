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


class NoAudioDeviceError(RuntimeError):
    """Raised when audio playback fails due to missing audio device."""


def play_audio(
    path: str, *, player: str = "auto", blocking: bool = False
) -> subprocess.Popen[bytes] | None:
    """Play an audio file. Returns Popen handle if non-blocking, None if blocking.

    Raises NoAudioDeviceError if playback fails due to missing audio device.
    """
    _, cmd = _detect_player(player)
    full_cmd = [*cmd, path]

    if blocking:
        result = subprocess.run(full_cmd, capture_output=True)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            if "cannot find card" in stderr or "Unknown PCM" in stderr or "No such file" in stderr:
                raise NoAudioDeviceError(f"No audio device available. WAV saved at: {path}")
            msg = f"Playback failed (exit {result.returncode}): {stderr[:200]}"
            raise RuntimeError(msg)
        return None

    return subprocess.Popen(
        full_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
