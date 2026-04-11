"""Screen capture via python-mss, returning a PIL Image."""

from __future__ import annotations

import mss
from PIL import Image


class ScreenCapture:
    """Cross-platform screen capture wrapping python-mss."""

    def grab(self, monitor: int = 0) -> Image.Image:
        """Grab a screenshot and return as a PIL RGB Image.

        Args:
            monitor: 0 = all monitors combined, 1+ = specific monitor index.
                     Default 0, but mss treats 0 as a composite — for practical
                     single-display use we fall back to monitor 1 when 0 is
                     passed so users get a single screen rather than a spanning
                     image.

        Returns:
            PIL Image in RGB mode.
        """
        with mss.mss() as sct:
            mon_index = monitor if monitor > 0 else 1
            if mon_index >= len(sct.monitors):
                mon_index = 1
            mon = sct.monitors[mon_index]
            shot = sct.grab(mon)
            return Image.frombytes(
                "RGB",
                shot.size,
                shot.bgra,
                "raw",
                "BGRX",
            )
