from __future__ import annotations
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from .config_io import WindowInfo, GeneralConfig
except ImportError:
    from config_io import WindowInfo, GeneralConfig  # type: ignore[no-redef]

try:
    import mss
except ImportError:
    mss = None
try:
    import numpy as np
except ImportError:
    np = None
try:
    from PIL import Image
except ImportError:
    Image = None

def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def adjusted_rgb(rgb: tuple[int, int, int], gamma: float) -> list[int]:
    if abs(gamma - 1.0) < 0.01:
        return [int(rgb[0]), int(rgb[1]), int(rgb[2])]

    def fix(channel: int, power: float) -> int:
        corrected = ((channel / 255.0) ** power) * 255.0
        return clamp(int(round(corrected)), 0, 255)

    return [
        fix(int(rgb[0]), 1.9 * gamma - 0.9),
        fix(int(rgb[1]), 1.9 * gamma - 0.9),
        fix(int(rgb[2]), 1.75 * gamma - 0.75),
    ]


def arrays_equal(array_a, array_b, tolerance: int = 0) -> bool:
    if len(array_a) != len(array_b):
        return False
    return all(abs(int(a) - int(b)) <= tolerance for a, b in zip(array_a, array_b))


def pixels_to_adjusted_rgb(pixel, gamma: float) -> list[int]:
    return adjusted_rgb((int(pixel[2]), int(pixel[1]), int(pixel[0])), gamma)


def pixels_region_to_rgb(pixels, gamma: float, agg_func: str = ""):
    if pixels.size == 0:
        if agg_func:
            return [0, 0, 0]
        return [[], [], []]
    rgb = pixels[:, :, :3][:, :, ::-1]
    if agg_func:
        flat = rgb.reshape(-1, 3)
        if agg_func.lower() == "max":
            result = flat.max(axis=0)
        else:
            result = flat.mean(axis=0)
        return adjusted_rgb((int(result[0]), int(result[1]), int(result[2])), gamma)
    corrected = np.vectorize(int)(rgb)
    r = corrected[:, :, 0].reshape(-1).tolist()
    g = corrected[:, :, 1].reshape(-1).tolist()
    b = corrected[:, :, 2].reshape(-1).tolist()
    return [r, g, b]


def parse_resolution(text: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*", text or "", re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


class GameImage:
    def __init__(self, window: WindowInfo, pixels, gamma: float) -> None:
        self.window = window
        self.width = int(window.width)
        self.height = int(window.height)
        self._pixels = pixels
        self._gamma = gamma

    def get_pixel_rgb(self, point: tuple[int, int] | list[int]) -> list[int]:
        x = clamp(int(round(point[0])), 0, self.width - 1)
        y = clamp(int(round(point[1])), 0, self.height - 1)
        pixel = self._pixels[y, x]
        return pixels_to_adjusted_rgb(pixel, self._gamma)

    def get_pixels_rgb(
        self,
        point_x: int,
        point_y: int,
        width: int,
        height: int,
        agg_func: str = "",
    ):
        x1 = clamp(int(round(point_x)), 0, self.width - 1)
        y1 = clamp(int(round(point_y)), 0, self.height - 1)
        x2 = clamp(x1 + max(int(round(width)), 1), 1, self.width)
        y2 = clamp(y1 + max(int(round(height)), 1), 1, self.height)
        region = self._pixels[y1:y2, x1:x2]
        return pixels_region_to_rgb(region, self._gamma, agg_func)


class X11GameCapture:
    def __init__(self, matcher: Any, general: GeneralConfig) -> None:
        self.matcher = matcher
        self.general = general
        self._grabber = mss.mss()

    def get_active_window(self) -> WindowInfo | None:
        window = self.matcher.get_active_window()
        if window is None or window.width <= 0 or window.height <= 0:
            return None
        return window

    def capture(self) -> GameImage | None:
        window = self.get_active_window()
        if window is None:
            return None
        shot = self._grabber.grab(
            {"left": window.x, "top": window.y, "width": window.width, "height": window.height}
        )
        pixels = np.asarray(shot)
        return GameImage(window, pixels, self.general.game_gamma)

    def capture_region(self, point_x: int, point_y: int, width: int, height: int):
        window = self.get_active_window()
        if window is None:
            return None
        x = clamp(int(round(point_x)), 0, max(window.width - 1, 0))
        y = clamp(int(round(point_y)), 0, max(window.height - 1, 0))
        region_w = clamp(max(int(round(width)), 1), 1, max(window.width - x, 1))
        region_h = clamp(max(int(round(height)), 1), 1, max(window.height - y, 1))
        shot = self._grabber.grab(
            {"left": window.x + x, "top": window.y + y, "width": region_w, "height": region_h}
        )
        return window, np.asarray(shot)


class SpectacleGameCapture:
    def __init__(self, matcher, general: GeneralConfig) -> None:
        self.matcher = matcher
        self.general = general

    def get_active_window(self) -> WindowInfo | None:
        window = self.matcher.get_active_window()
        if window is None or window.width <= 0 or window.height <= 0:
            return None
        return window

    def capture(self) -> GameImage | None:
        if Image is None:
            return None
        window = self.get_active_window()
        if window is None:
            return None
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            tmp_path = handle.name
        try:
            completed = subprocess.run(
                ["spectacle", "--background", "--activewindow", "-o", tmp_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 or not Path(tmp_path).exists():
                return None
            with Image.open(tmp_path) as screenshot:
                pixels = np.array(screenshot.convert("RGBA"))
            if pixels.ndim != 3:
                return None
            if pixels.shape[1] != window.width or pixels.shape[0] != window.height:
                window = WindowInfo(
                    window_id=window.window_id,
                    title=window.title,
                    wm_class=window.wm_class,
                    x=window.x,
                    y=window.y,
                    width=int(pixels.shape[1]),
                    height=int(pixels.shape[0]),
                )
            return GameImage(window, pixels, self.general.game_gamma)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def capture_region(self, point_x: int, point_y: int, width: int, height: int):
        image = self.capture()
        if image is None:
            return None
        x1 = clamp(int(round(point_x)), 0, image.width - 1)
        y1 = clamp(int(round(point_y)), 0, image.height - 1)
        x2 = clamp(x1 + max(int(round(width)), 1), 1, image.width)
        y2 = clamp(y1 + max(int(round(height)), 1), 1, image.height)
        region = image._pixels[y1:y2, x1:x2].copy()
        return image.window, region


