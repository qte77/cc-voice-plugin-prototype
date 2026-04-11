"""Tests for cc_vlm.capture — ScreenCapture using mocked mss."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from PIL import Image

from cc_vlm.capture import ScreenCapture


class TestScreenCapture:
    def _fake_mss_shot(self, width: int, height: int) -> MagicMock:
        shot = MagicMock()
        shot.size = (width, height)
        # BGRX format: 4 bytes per pixel
        shot.bgra = b"\x00\x00\x00\xff" * (width * height)
        return shot

    @patch("cc_vlm.capture.mss.mss")
    def test_grab_returns_pil_image(self, mock_mss_class: MagicMock) -> None:
        fake_sct = MagicMock()
        fake_sct.monitors = [
            {"left": 0, "top": 0, "width": 100, "height": 50},  # [0] composite
            {"left": 0, "top": 0, "width": 100, "height": 50},  # [1] monitor 1
        ]
        fake_sct.grab.return_value = self._fake_mss_shot(100, 50)
        mock_mss_class.return_value.__enter__.return_value = fake_sct

        capture = ScreenCapture()
        img = capture.grab()

        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
        assert img.size == (100, 50)

    @patch("cc_vlm.capture.mss.mss")
    def test_grab_defaults_to_monitor_1_when_monitor_0(self, mock_mss_class: MagicMock) -> None:
        """monitor=0 is the mss composite — we prefer single-monitor 1."""
        fake_sct = MagicMock()
        fake_sct.monitors = [
            {"left": 0, "top": 0, "width": 999, "height": 999},  # composite
            {"left": 0, "top": 0, "width": 100, "height": 50},  # monitor 1
        ]
        fake_sct.grab.return_value = self._fake_mss_shot(100, 50)
        mock_mss_class.return_value.__enter__.return_value = fake_sct

        ScreenCapture().grab(monitor=0)
        # The grab call should use monitor index 1, not 0
        called_with = fake_sct.grab.call_args[0][0]
        assert called_with["width"] == 100

    @patch("cc_vlm.capture.mss.mss")
    def test_grab_clamps_out_of_range_monitor(self, mock_mss_class: MagicMock) -> None:
        fake_sct = MagicMock()
        fake_sct.monitors = [
            {"left": 0, "top": 0, "width": 999, "height": 999},
            {"left": 0, "top": 0, "width": 100, "height": 50},
        ]
        fake_sct.grab.return_value = self._fake_mss_shot(100, 50)
        mock_mss_class.return_value.__enter__.return_value = fake_sct

        ScreenCapture().grab(monitor=99)
        called_with = fake_sct.grab.call_args[0][0]
        assert called_with["width"] == 100  # fell back to monitor 1
