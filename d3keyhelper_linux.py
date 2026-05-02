#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import math
import os
import queue
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from config_schema import (
    build_general_section,
    gd,
    pd,
    sd,
    skill_hotkey_default,
    default_profile_dict as _schema_default_profile_dict,
)
from enums import MovingMethod, PotionMethod, QuickPauseAction, QuickPauseMode, QueueReason, ReforgeMethod, SalvageMethod, SkillAction, StartMode

try:
    from pynput import keyboard, mouse
except ImportError:
    keyboard = None
    mouse = None

try:
    from Xlib import X, display as xdisplay
except ImportError:
    X = None
    xdisplay = None

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


DEFAULT_VERSION = "260403"
CONFIG_DIR_NAME = "d3helperforlinux"
CONFIG_FILE_NAME = "d3oldsand.ini"
DEFAULT_PROFILE_NAMES = ["配置1"]
START_METHOD_MOUSE = {
    1: "mouse:right",
    2: "mouse:middle",
    3: "wheel_up",
    4: "wheel_down",
    5: "mouse:x1",
    6: "mouse:x2",
}
COMMON_METHOD_MOUSE = {
    2: "mouse:middle",
    3: "wheel_up",
    4: "wheel_down",
    5: "mouse:x1",
    6: "mouse:x2",
}
QUICK_PAUSE_MOUSE = {
    1: "mouse:left",
    2: "mouse:right",
    3: "mouse:middle",
    4: "mouse:x1",
    5: "mouse:x2",
}
HOTKEY_MODIFIER_PREFIX = {"^": "ctrl", "!": "alt", "+": "shift", "#": "cmd"}
HOTKEY_MODIFIER_NAMES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "lctrl": "ctrl",
    "rctrl": "ctrl",
    "alt": "alt",
    "lalt": "alt",
    "ralt": "alt",
    "altgr": "alt",
    "shift": "shift",
    "lshift": "shift",
    "rshift": "shift",
    "win": "cmd",
    "lwin": "cmd",
    "rwin": "cmd",
    "cmd": "cmd",
    "super": "cmd",
}
SPECIAL_KEY_ALIASES = {
    "esc": "esc",
    "escape": "esc",
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "bs": "backspace",
    "delete": "delete",
    "del": "delete",
    "insert": "insert",
    "ins": "insert",
    "home": "home",
    "end": "end",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "pgup": "page_up",
    "pgdn": "page_down",
    "pageup": "page_up",
    "pagedown": "page_down",
    "capslock": "caps_lock",
    "numlock": "num_lock",
    "scrolllock": "scroll_lock",
    "printscreen": "print_screen",
    "appskey": "menu",
    "browser_back": "browser_back",
    "browser_forward": "browser_forward",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "alt_l": "alt",
    "alt_r": "alt",
    "alt_gr": "alt",
    "shift_l": "shift",
    "shift_r": "shift",
    "cmd_l": "cmd",
    "cmd_r": "cmd",
    "super_l": "cmd",
    "super_r": "cmd",
}
MOUSE_EVENT_ALIASES = {
    "lbutton": "mouse:left",
    "rbutton": "mouse:right",
    "mbutton": "mouse:middle",
    "xbutton1": "mouse:x1",
    "xbutton2": "mouse:x2",
    "wheelup": "wheel_up",
    "wheeldown": "wheel_down",
}
MOUSE_BUTTONS = {
    "mouse:left": lambda: mouse.Button.left,
    "mouse:right": lambda: mouse.Button.right,
    "mouse:middle": lambda: mouse.Button.middle,
    "mouse:x1": lambda: getattr(mouse.Button, "x1"),
    "mouse:x2": lambda: getattr(mouse.Button, "x2"),
}
SYNTHETIC_PHASE_PRESS = "press"
SYNTHETIC_PHASE_RELEASE = "release"


@dataclass(frozen=True)
class HotkeySpec:
    base: str
    modifiers: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SendSpec:
    base: str


@dataclass
class SkillConfig:
    hotkey: SendSpec | None
    action: int
    interval_ms: int
    delay_ms: int
    randomize_delay: bool
    priority: int
    repeat: int
    repeat_interval_ms: int
    trigger: HotkeySpec | None


@dataclass
class QuickPauseConfig:
    enabled: bool
    mode: int
    trigger: HotkeySpec | None
    action: int
    delay_ms: int


@dataclass
class ProfileConfig:
    name: str
    skills: list[SkillConfig]
    profile_hotkey: HotkeySpec | None
    autostart_macro: bool
    start_mode: int
    moving_method: int
    moving_interval_ms: int
    potion_method: int
    potion_interval_ms: int
    use_skill_queue: bool
    use_skill_queue_interval_ms: int
    quick_pause: QuickPauseConfig


@dataclass
class HelperConfig:
    hotkey: HotkeySpec | None
    gamble_enabled: bool
    gamble_times: int
    loot_enabled: bool
    loot_times: int
    salvage_enabled: bool
    salvage_method: int
    reforge_enabled: bool
    reforge_method: int
    upgrade_enabled: bool
    convert_enabled: bool
    abandon_enabled: bool
    mouse_speed: int
    animation_delay_ms: int
    max_reforge: int
    safezone: set[int]


@dataclass
class GeneralConfig:
    activated_profile: int
    start_hotkey: HotkeySpec | None
    run_on_start: bool
    d3only: bool
    smart_pause: bool
    sound_on_profile_switch: bool
    custom_standing_enabled: bool
    custom_standing_key: SendSpec
    custom_moving_enabled: bool
    custom_moving_key: SendSpec
    custom_potion_enabled: bool
    custom_potion_key: SendSpec
    game_gamma: float
    buff_percent: float
    game_resolution: str
    helper: HelperConfig


@dataclass
class WindowInfo:
    window_id: int
    title: str
    wm_class: str
    x: int
    y: int
    width: int
    height: int
    pid: int = 0
    commandline: str = ""


class ConfigError(RuntimeError):
    pass


def read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()


def looks_like_proton_diablo_window(window: WindowInfo) -> bool:
    commandline = window.commandline.lower()
    if re.search(r"diablo iii(?:64)?\.exe", commandline, re.IGNORECASE):
        return True
    if "steam_app_" in window.wm_class.lower() and "diablo" in commandline:
        return True
    return False


def format_window_debug(window: WindowInfo | None) -> str:
    if window is None:
        return "无活动窗口"
    parts = [f"title={window.title!r}", f"class={window.wm_class!r}"]
    if window.pid:
        parts.append(f"pid={window.pid}")
    if window.commandline:
        parts.append(f"cmd={window.commandline}")
    return ", ".join(parts)


def play_notification_sound() -> None:
    for command in (
        ["canberra-gtk-play", "-i", "complete"],
        ["canberra-gtk-play", "-i", "message"],
    ):
        if shutil.which(command[0]):
            try:
                subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except OSError:
                continue
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


class SyntheticEventFilter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], int] = defaultdict(int)
        self._lock = threading.Lock()

    def mark(self, base: str, phase: str, count: int = 1) -> None:
        with self._lock:
            self._counts[(base, phase)] += count

    def consume(self, base: str, phase: str) -> bool:
        with self._lock:
            key = (base, phase)
            if self._counts.get(key, 0) <= 0:
                return False
            self._counts[key] -= 1
            if self._counts[key] <= 0:
                self._counts.pop(key, None)
            return True


class InputSender:
    def __init__(self, event_filter: SyntheticEventFilter) -> None:
        if keyboard is None or mouse is None:
            raise ConfigError("缺少 Linux 运行依赖，请先安装 requirements.txt 中的依赖。")
        self._filter = event_filter
        self._keyboard = keyboard.Controller()
        self._mouse = mouse.Controller()
        self._lock = threading.Lock()

    def tap(self, send_spec: SendSpec) -> None:
        self.press(send_spec)
        self.release(send_spec)

    def mouse_position(self) -> tuple[int, int]:
        x, y = self._mouse.position
        return int(x), int(y)

    def move_mouse(self, x: int, y: int) -> None:
        with self._lock:
            self._mouse.position = (int(x), int(y))

    def click_mouse(self, send_spec: SendSpec, hold_ms: int = 0) -> None:
        self.press(send_spec)
        if hold_ms > 0:
            time.sleep(hold_ms / 1000.0)
        self.release(send_spec)

    def press(self, send_spec: SendSpec) -> None:
        with self._lock:
            if send_spec.base.startswith("mouse:"):
                button = self._resolve_mouse_button(send_spec.base)
                self._filter.mark(send_spec.base, SYNTHETIC_PHASE_PRESS)
                self._mouse.press(button)
                return
            resolved = self._resolve_keyboard_key(send_spec.base)
            self._filter.mark(send_spec.base, SYNTHETIC_PHASE_PRESS)
            self._keyboard.press(resolved)

    def release(self, send_spec: SendSpec) -> None:
        with self._lock:
            if send_spec.base.startswith("mouse:"):
                button = self._resolve_mouse_button(send_spec.base)
                self._filter.mark(send_spec.base, SYNTHETIC_PHASE_RELEASE)
                self._mouse.release(button)
                return
            resolved = self._resolve_keyboard_key(send_spec.base)
            self._filter.mark(send_spec.base, SYNTHETIC_PHASE_RELEASE)
            self._keyboard.release(resolved)

    def _resolve_mouse_button(self, base: str):
        resolver = MOUSE_BUTTONS.get(base)
        if resolver is None:
            raise ConfigError(f"不支持的鼠标按键：{base}")
        return resolver()

    def _resolve_keyboard_key(self, base: str):
        if len(base) == 1:
            return base
        function_match = re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", base)
        if function_match:
            return getattr(keyboard.Key, base)
        if base in {"ctrl", "alt", "shift", "cmd"}:
            return getattr(keyboard.Key, base)
        key_name = {
            "page_up": "page_up",
            "page_down": "page_down",
            "caps_lock": "caps_lock",
            "num_lock": "num_lock",
            "scroll_lock": "scroll_lock",
            "print_screen": "print_screen",
            "browser_back": "browser_back",
            "browser_forward": "browser_forward",
            "menu": "menu",
        }.get(base, base)
        if not hasattr(keyboard.Key, key_name):
            raise ConfigError(f"不支持的键盘按键：{base}")
        return getattr(keyboard.Key, key_name)


class ActiveWindowMatcher:
    def __init__(self, title_regex: str | None, class_regex: str | None) -> None:
        if xdisplay is None or X is None:
            raise ConfigError("缺少 python-xlib，无法在 Linux 上检测当前活动窗口。")
        self._display = xdisplay.Display()
        self._root = self._display.screen().root
        self._atom_active = self._display.intern_atom("_NET_ACTIVE_WINDOW")
        self._atom_pid = self._display.intern_atom("_NET_WM_PID")
        self._title_pattern = re.compile(title_regex, re.IGNORECASE) if title_regex else None
        self._class_pattern = re.compile(class_regex, re.IGNORECASE) if class_regex else None
        self._use_proton_fallback = not class_regex and title_regex == "Diablo III"

    def matches_active_window(self) -> bool:
        window = self.get_active_window()
        if window is None:
            return False
        return self.matches_window(window)

    def matches_window(self, window: WindowInfo) -> bool:
        title_matches = bool(self._title_pattern and self._title_pattern.search(window.title))
        class_matches = bool(self._class_pattern and self._class_pattern.search(window.wm_class))
        proton_matches = self._use_proton_fallback and looks_like_proton_diablo_window(window)
        if self._title_pattern and not title_matches:
            if not proton_matches:
                return False
        if self._class_pattern and not class_matches:
            return False
        return bool(title_matches or class_matches or proton_matches)

    def get_active_window(self) -> WindowInfo | None:
        try:
            prop = self._root.get_full_property(self._atom_active, X.AnyPropertyType)
            if not prop or not getattr(prop, "value", None):
                return None
            window_id = int(prop.value[0])
            window = self._display.create_resource_object("window", window_id)
            title = window.get_wm_name() or ""
            wm_class = " ".join(filter(None, window.get_wm_class() or ()))
            pid_prop = window.get_full_property(self._atom_pid, X.AnyPropertyType)
            pid = int(pid_prop.value[0]) if pid_prop and getattr(pid_prop, "value", None) else 0
            geometry = window.get_geometry()
            translated = window.translate_coords(self._root, 0, 0)
            return WindowInfo(
                window_id=window_id,
                title=title,
                wm_class=wm_class,
                x=int(translated.x),
                y=int(translated.y),
                width=int(geometry.width),
                height=int(geometry.height),
                pid=pid,
                commandline=read_process_commandline(pid),
            )
        except Exception:
            return None

    def _get_active_window_metadata(self) -> tuple[str, str]:
        window = self.get_active_window()
        if window is None:
            return "", ""
        return window.title, window.wm_class


class KWinWindowMatcher:
    def __init__(self, title_regex: str | None, class_regex: str | None) -> None:
        self._title_pattern = re.compile(title_regex, re.IGNORECASE) if title_regex else None
        self._class_pattern = re.compile(class_regex, re.IGNORECASE) if class_regex else None

    def get_active_window(self) -> WindowInfo | None:
        try:
            completed = subprocess.run(
                [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    "org.kde.KWin",
                    "--object-path",
                    "/KWin",
                    "--method",
                    "org.kde.KWin.queryWindowInfo",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        output = completed.stdout.strip()
        pairs = dict(re.findall(r"'([^']+)': <([^>]+)>", output))
        if not pairs:
            return None
        title = pairs.get("caption", "").strip("'")
        wm_class = pairs.get("resourceClass", "").strip("'") or pairs.get("desktopFile", "").strip("'")
        return WindowInfo(
            window_id=0,
            title=title,
            wm_class=wm_class,
            x=int(float(pairs.get("x", "0.0"))),
            y=int(float(pairs.get("y", "0.0"))),
            width=int(float(pairs.get("width", "0.0"))),
            height=int(float(pairs.get("height", "0.0"))),
        )

    def matches_active_window(self) -> bool:
        window = self.get_active_window()
        if window is None:
            return False
        if self._title_pattern and not self._title_pattern.search(window.title):
            return False
        if self._class_pattern and not self._class_pattern.search(window.wm_class):
            return False
        return bool(self._title_pattern or self._class_pattern)


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
    def __init__(self, matcher: ActiveWindowMatcher, general: GeneralConfig) -> None:
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


def get_skill_button_buff_pos(width: int, height: int, button_id: int, percent: float) -> list[int]:
    xs = [1288, 1377, 1465, 1554, 1647, 1734]
    bar_width = 63
    y = 1328 * height / 1440.0
    x = width / 2.0 - (3440 / 2.0 - xs[button_id - 1] - percent * bar_width) * height / 1440.0
    return [round(x), round(y)]


def get_inventory_space_xy(width: int, height: int, slot_id: int, zone: str) -> list[int]:
    space_size_inner_w = 64
    space_size_inner_h = 63
    bag_x = [2753, 2820, 2887, 2954, 3021, 3089, 3156, 3223, 3290, 3357]
    bag_y = [747, 813, 880, 946, 1013, 1079]
    kanai_x = [242, 318, 394]
    kanai_y = [503, 579, 655]
    if zone == "bag":
        column = 10 if slot_id % 10 == 0 else slot_id % 10
        row = math.floor((slot_id - 1) / 10) + 1
        return [
            round(width - ((3440 - bag_x[column - 1] - space_size_inner_w / 2) * height / 1440.0)),
            round((bag_y[row - 1] + space_size_inner_h / 2) * height / 1440.0),
            round(width - ((3440 - bag_x[column - 1]) * height / 1440.0)),
            round(bag_y[row - 1] * height / 1440.0),
        ]
    column = 3 if slot_id % 3 == 0 else slot_id % 3
    row = math.floor((slot_id - 1) / 3) + 1
    return [
        round((kanai_x[column - 1] + space_size_inner_w / 2) * height / 1440.0),
        round((kanai_y[row - 1] + space_size_inner_h / 2) * height / 1440.0),
        round(kanai_x[column - 1] * height / 1440.0),
        round(kanai_y[row - 1] * height / 1440.0),
    ]


def get_kanai_cube_button_pos(height: int) -> list[list[int]]:
    return [
        [round(320 * height / 1440.0), round(1105 * height / 1440.0)],
        [round(955 * height / 1440.0), round(1115 * height / 1440.0)],
        [round(777 * height / 1440.0), round(1117 * height / 1440.0)],
        [round(1135 * height / 1440.0), round(1117 * height / 1440.0)],
    ]


def get_salvage_icon_xy(height: int, mode: str) -> list[list[int]]:
    if mode == "center":
        return [
            [round(221 * height / 1440.0), round(388 * height / 1440.0)],
            [round(335 * height / 1440.0), round(388 * height / 1440.0)],
            [round(424 * height / 1440.0), round(388 * height / 1440.0)],
            [round(514 * height / 1440.0), round(388 * height / 1440.0)],
        ]
    return [
        [round(203 * height / 1440.0), round(337 * height / 1440.0)],
        [round(335 * height / 1440.0), round(371 * height / 1440.0)],
        [round(424 * height / 1440.0), round(371 * height / 1440.0)],
        [round(514 * height / 1440.0), round(371 * height / 1440.0)],
    ]


def is_dialog_box_on_screen(image: GameImage, width: int, height: int) -> bool:
    point1 = [width / 2 - (3440 / 2 - 1655) * height / 1440.0, 500 * height / 1440.0]
    point2 = [width / 2 + (3440 / 2 - 1800) * height / 1440.0, 500 * height / 1440.0]
    c1 = image.get_pixel_rgb(point1)
    c2 = image.get_pixel_rgb(point2)
    return bool(
        c1[0] > c1[1] > c1[2]
        and c1[2] < 5
        and c1[1] < 15
        and c1[0] > 25
        and c2[0] > c2[1] > c2[2]
        and c2[2] < 5
        and c2[1] < 15
        and c2[0] > 25
    )


def is_salvage_page_open(image: GameImage, width: int, height: int):
    c1 = image.get_pixel_rgb([round(339 * height / 1440.0), round(80 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(351 * height / 1440.0), round(107 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(388 * height / 1440.0), round(86 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(673 * height / 1440.0), round(1040 * height / 1440.0)])
    if not (
        c1[2] > c1[1] > c1[0]
        and c1[2] > 170
        and c1[2] - c1[0] > 80
        and c3[2] > c3[1] > c3[0]
        and c3[2] > 110
        and c2[0] + c2[1] > 350
        and c4[0] > 50
        and c4[1] < 15
        and c4[2] < 15
    ):
        return [0]
    edges = get_salvage_icon_xy(height, "edge")
    c_leg = image.get_pixel_rgb(edges[0])
    c_white = image.get_pixel_rgb(edges[1])
    c_blue = image.get_pixel_rgb(edges[2])
    c_rare = image.get_pixel_rgb(edges[3])
    if c_blue[2] > c_blue[1] > c_blue[0] and c_rare[2] < 20 and c_rare[0] > c_rare[1] > c_rare[2]:
        return [2, c_leg, c_white, c_blue, c_rare]
    return [1]


def salvage_mode_is_armed(salvage_state) -> bool:
    return bool(
        len(salvage_state) > 1
        and len(salvage_state[1]) >= 3
        and salvage_state[1][2] < 10
        and salvage_state[1][0] + salvage_state[1][1] > 400
    )


def salvage_bulk_buttons_from_state(salvage_state) -> list[int]:
    if len(salvage_state) < 5:
        return []
    buttons: list[int] = []
    if salvage_state[4][0] > 50:
        buttons.append(3)
    if salvage_state[3][2] > 65:
        buttons.append(2)
    if salvage_state[2][0] > 65:
        buttons.append(1)
    return buttons


def _is_kanai_cube_shell_visible(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(353 * height / 1440.0), round(85 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(278 * height / 1440.0), round(147 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(330 * height / 1440.0), round(140 * height / 1440.0)])
    return bool(
        c1[0] < 50
        and c1[1] < 40
        and c1[2] < 35
        and c2[0] > 100
        and c2[1] < 30
        and c2[2] < 30
        and abs(c3[2] - c3[1]) <= 8
        and c3[0] <= 55
        and c3[0] < c3[1]
        and c3[0] < c3[2]
    )


def _is_kanai_reforge_page(image: GameImage, height: int) -> bool:
    cc1 = image.get_pixel_rgb([round(788 * height / 1440.0), round(428 * height / 1440.0)])
    cc2 = image.get_pixel_rgb([round(810 * height / 1440.0), round(429 * height / 1440.0)])
    return bool(cc1[2] > 230 and cc2[2] > 230 and cc1[2] > cc1[1] > cc1[0] and cc2[2] > cc2[1] > cc2[0])


def _is_kanai_upgrade_page(image: GameImage, height: int) -> bool:
    for offset in (0, -22):
        cc1 = image.get_pixel_rgb([round(799 * height / 1440.0), round((406 + offset) * height / 1440.0)])
        cc2 = image.get_pixel_rgb([round(795 * height / 1440.0), round((592 + offset) * height / 1440.0)])
        if cc1[0] + cc1[1] + cc1[2] > 550 and cc1[0] > cc1[2] and cc2[0] + cc2[1] > 400 and cc2[0] > cc2[2]:
            return True
    return False


def _is_kanai_convert_page(image: GameImage, height: int) -> bool:
    for offset in (0, -43):
        cc3 = image.get_pixel_rgb([round(799 * height / 1440.0), round((365 + offset) * height / 1440.0)])
        if cc3[0] + cc3[1] + cc3[2] > 600 and cc3[0] > cc3[1] > cc3[2] and 110 < cc3[2] < 200:
            return True
    return False


def is_kanai_cube_open(image: GameImage, width: int, height: int, title: str):
    if _is_kanai_reforge_page(image, height):
        return 2
    if _is_kanai_upgrade_page(image, height):
        return 3
    if _is_kanai_convert_page(image, height):
        return 4
    if _is_kanai_cube_shell_visible(image, height):
        return 1
    return 0


def is_gamble_open(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(320 * height / 1440.0), round(96 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(351 * height / 1440.0), round(100 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(194 * height / 1440.0), round(67 * height / 1440.0)])
    c5 = image.get_pixel_rgb([round(147 * height / 1440.0), round(94 * height / 1440.0)])
    return bool(c1[2] > c1[0] > c1[1] and c1[2] > 130 and c2[0] + c2[1] > 330 and sum(c4) + sum(c5) < 10)


def is_inventory_open(image: GameImage, width: int, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(width - (3440 - 3086) * height / 1440.0), round(108 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(width - (3440 - 3010) * height / 1440.0), round(147 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(width - (3440 - 3425) * height / 1440.0), round(142 * height / 1440.0)])
    c4 = image.get_pixel_rgb([round(width - (3440 - 3117) * height / 1440.0), round(84 * height / 1440.0)])
    return bool(
        c1[0] + c1[1] > 240
        and c2[0] > 115
        and c2[1] < 30
        and c2[2] < 30
        and abs(c3[0] - c3[1]) <= 10
        and c3[2] < 40
        and c4[2] > c4[1] + 60
        and c4[1] > c4[0]
    )


def is_stash_open(image: GameImage, height: int) -> bool:
    c1 = image.get_pixel_rgb([round(282 * height / 1440.0), round(147 * height / 1440.0)])
    c2 = image.get_pixel_rgb([round(382 * height / 1440.0), round(77 * height / 1440.0)])
    c3 = image.get_pixel_rgb([round(299 * height / 1440.0), round(82 * height / 1440.0)])
    return bool(
        c1[0] > 100
        and c1[0] > c1[1] + 80
        and abs(c1[1] - c1[2]) < 10
        and c2[1] > c2[2] > c2[0]
        and c2[1] - c2[0] > 80
        and c3[0] > c3[1] > c3[2]
        and c3[2] < 40
    )


def is_inventory_space_empty(image: GameImage, width: int, height: int, slot_id: int, zone: str, checkpoints=None) -> bool:
    space_w = 64
    space_h = 63
    x_center, y_center, x0, y0 = get_inventory_space_xy(width, height, slot_id, zone)
    if not checkpoints:
        c = image.get_pixels_rgb(
            round(x0 + 0.2 * space_w),
            round(y0 + 0.2 * space_h),
            round(0.6 * space_w),
            round(0.6 * space_h),
            "max",
        )
        return bool(c[0] <= 50 and c[1] <= 50 and c[2] <= 50)
    for check in checkpoints:
        xy = [round(x0 + space_w * check[0] * height / 1440.0), round(y0 + space_h * check[1] * height / 1440.0)]
        c = image.get_pixel_rgb(xy)
        if not (c[0] < 22 and c[1] < 20 and c[2] < 15 and c[0] > c[2] and c[1] > c[2]):
            return False
    return True


def scan_inventory_space(image: GameImage, width: int, height: int, safezone: set[int]):
    helper_bag_zone = [-1] * 61
    inventory_colors: dict[int, list[int]] = {}
    points = [(0.65625, 0.71429), (0.375, 0.36508), (0.725, 0.251)]
    for index in range(1, 61):
        x_center, y_center, x0, y0 = get_inventory_space_xy(width, height, index, "bag")
        inventory_colors[index] = image.get_pixel_rgb(
            [round(x0 + 64 * 0.08 * height / 1440.0), round(y0 + 63 * 0.7 * height / 1440.0)]
        )
        if index in safezone:
            helper_bag_zone[index] = 0
            continue
        slot_value = 1
        for px, py in points:
            c = image.get_pixel_rgb([round(x0 + 64 * px * height / 1440.0), round(y0 + 63 * py * height / 1440.0)])
            if not (c[0] < 22 and c[1] < 20 and c[2] < 15 and c[0] > c[2] and c[1] > c[2]):
                slot_value = 10
                break
        helper_bag_zone[index] = slot_value
    return helper_bag_zone, inventory_colors


class MacroApp:
    def __init__(
        self,
        general: GeneralConfig,
        profiles: list[ProfileConfig],
        start_profile_index: int,
        sender: InputSender,
        matcher,
        capture_backend: str,
    ) -> None:
        self.general = general
        self.profiles = profiles
        self.current_profile_index = start_profile_index
        self.sender = sender
        self.matcher = matcher
        self.synthetic_filter = sender._filter
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._running = False
        self._paused = False
        self._workers: list[threading.Thread] = []
        self._held_keys: list[SendSpec] = []
        self._pressed_bases: set[str] = set()
        self._pressed_modifiers: set[str] = set()
        self._focus_thread: threading.Thread | None = None
        if matcher is not None and mss is not None and np is not None:
            self._capture = SpectacleGameCapture(matcher, general) if capture_backend == "kde-wayland" else X11GameCapture(matcher, general)
        else:
            self._capture = None
        self._skill_queue: queue.Queue[tuple[SendSpec, int]] = queue.Queue()
        self._helper_running = False
        self._helper_break = False
        self._helper_thread: threading.Thread | None = None
        self._quick_pause_last_pressed_at: dict[str, float] = {}
        self._watched_press_bases: set[str] = set()
        self._watched_release_bases: set[str] = set()
        self._refresh_input_watch()

    def start(self) -> None:
        if self.general.d3only and self.matcher is None:
            raise ConfigError("当前配置启用了 d3only，但 Linux 运行器没有可用的窗口检测器。")
        self._start_focus_monitor()
        self._print_profile_notes(self.current_profile)
        self._print_helper_notes()

    @property
    def current_profile(self) -> ProfileConfig:
        return self.profiles[self.current_profile_index]

    def shutdown(self) -> None:
        self.stop_macro(reason=None)
        self._helper_break = True
        self._shutdown_event.set()
        if self._helper_thread and self._helper_thread.is_alive():
            self._helper_thread.join(timeout=1.0)
        if self._focus_thread and self._focus_thread.is_alive():
            self._focus_thread.join(timeout=1.0)

    def _add_hotkey_watch(self, press_bases: set[str], release_bases: set[str], spec: HotkeySpec | None) -> None:
        if spec is None:
            return
        press_bases.add(spec.base)
        release_bases.add(spec.base)
        press_bases.update(spec.modifiers)
        release_bases.update(spec.modifiers)

    def _refresh_input_watch(self) -> None:
        press_bases: set[str] = set()
        release_bases: set[str] = set()
        self._add_hotkey_watch(press_bases, release_bases, self.general.start_hotkey)
        self._add_hotkey_watch(press_bases, release_bases, self.general.helper.hotkey)
        if self.general.smart_pause:
            press_bases.update({"tab", "enter", "t", "m"})
        for profile in self.profiles:
            self._add_hotkey_watch(press_bases, release_bases, profile.profile_hotkey)
            if profile.start_mode == StartMode.HOLD_WHILE:
                self._add_hotkey_watch(press_bases, release_bases, self.general.start_hotkey)
            if profile.quick_pause.enabled:
                self._add_hotkey_watch(press_bases, release_bases, profile.quick_pause.trigger)
            for skill in profile.skills:
                if skill.action == SkillAction.KEY_TRIGGER:
                    self._add_hotkey_watch(press_bases, release_bases, skill.trigger)
        self._watched_press_bases = press_bases
        self._watched_release_bases = release_bases

    def needs_keyboard_listener(self) -> bool:
        watched = self._watched_press_bases | self._watched_release_bases
        return any(not base.startswith("mouse:") and not base.startswith("wheel_") for base in watched)

    def needs_mouse_listener(self) -> bool:
        watched = self._watched_press_bases | self._watched_release_bases
        return any(base.startswith("mouse:") or base.startswith("wheel_") for base in watched)

    def _wait_until(self, stop_event: threading.Event, deadline: float) -> bool:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        return stop_event.wait(remaining)

    def on_key_press(self, base: str) -> None:
        if base not in self._watched_press_bases:
            return
        with self._lock:
            if self.synthetic_filter.consume(base, SYNTHETIC_PHASE_PRESS):
                return
            if base in {"ctrl", "alt", "shift", "cmd"}:
                self._pressed_modifiers.add(base)
            if base in self._pressed_bases:
                return
            self._pressed_bases.add(base)
        self._dispatch_press(base)

    def on_key_release(self, base: str) -> None:
        if base not in self._watched_release_bases:
            return
        with self._lock:
            if self.synthetic_filter.consume(base, SYNTHETIC_PHASE_RELEASE):
                return
            self._pressed_bases.discard(base)
            if base in {"ctrl", "alt", "shift", "cmd"}:
                self._pressed_modifiers.discard(base)
        self._dispatch_release(base)

    def on_scroll(self, direction: str) -> None:
        if direction not in self._watched_press_bases:
            return
        self._dispatch_press(direction)

    def _dispatch_press(self, base: str) -> None:
        if self.general.smart_pause:
            if base == "tab":
                self.toggle_pause()
                return
            if base in {"enter", "t", "m"}:
                self.stop_macro(reason="收到智能暂停停止键")
                return

        start_hotkey = self.general.start_hotkey
        if self._matches_hotkey(start_hotkey, base):
            self._handle_start_hotkey_press()
            return

        for index, profile in enumerate(self.profiles):
            if self._matches_hotkey(profile.profile_hotkey, base):
                self.switch_profile(index)
                return

        if self._matches_hotkey(self.general.helper.hotkey, base):
            self.trigger_helper()
            return

        if self._running and self.current_profile.quick_pause.enabled:
            quick_pause = self.current_profile.quick_pause
            if self._matches_hotkey(quick_pause.trigger, base):
                now = time.monotonic()
                should_fire = False
                if quick_pause.mode == QuickPauseMode.DOUBLE_CLICK:
                    previous = self._quick_pause_last_pressed_at.get(base, 0.0)
                    should_fire = now - previous <= 0.5
                else:
                    should_fire = True
                self._quick_pause_last_pressed_at[base] = now
                if should_fire:
                    self.handle_quick_pause(quick_pause)
                    return

        with self._lock:
            if not self._running or self._paused:
                return
            skills = list(self.current_profile.skills)
        for skill in skills:
            if skill.action == SkillAction.KEY_TRIGGER and self._matches_hotkey(skill.trigger, base):
                self._execute_skill(skill)

    def _dispatch_release(self, base: str) -> None:
        start_hotkey = self.general.start_hotkey
        profile = self.current_profile
        if profile.start_mode == StartMode.HOLD_WHILE and start_hotkey and start_hotkey.base == base:
            self.stop_macro(reason=None)
        if self._running and profile.quick_pause.enabled and profile.quick_pause.mode == QuickPauseMode.HOLD:
            trigger = profile.quick_pause.trigger
            if trigger and trigger.base == base:
                self.run_macro()

    def _matches_hotkey(self, spec: HotkeySpec | None, base: str) -> bool:
        if spec is None or spec.base != base:
            return False
        with self._lock:
            active_modifiers = set(self._pressed_modifiers)
        return set(spec.modifiers).issubset(active_modifiers)

    def _handle_start_hotkey_press(self) -> None:
        profile = self.current_profile
        if profile.start_mode == StartMode.TOGGLE:
            if self._running:
                self.stop_macro(reason=None)
            else:
                self.run_macro()
            return
        if profile.start_mode == StartMode.HOLD_WHILE:
            if self.general.start_hotkey and self.general.start_hotkey.base in {"wheel_up", "wheel_down"}:
                print("当前配置使用滚轮作为启动键，但 Linux 首版不支持“仅按下时”滚轮保持模式。", flush=True)
                return
            if not self._running:
                self.run_macro()
            return
        if profile.start_mode == StartMode.ONCE:
            self.send_once_actions()

    def run_macro(self) -> None:
        with self._lock:
            if self._running:
                return
        if self.general.d3only and self.matcher and not self.matcher.matches_active_window():
            active_window = self.matcher.get_active_window() if hasattr(self.matcher, "get_active_window") else None
            print(f"未检测到目标游戏窗口，当前不会启动宏。前台窗口：{format_window_debug(active_window)}", flush=True)
            return

        standing_key = self.general.custom_standing_key if self.general.custom_standing_enabled else parse_send_spec("LShift")
        moving_key = self.general.custom_moving_key if self.general.custom_moving_enabled else parse_send_spec("e")
        potion_key = self.general.custom_potion_key if self.general.custom_potion_enabled else parse_send_spec("q")
        if standing_key is None or moving_key is None or potion_key is None:
            raise ConfigError("配置中的自定义按键无效。")

        with self._lock:
            self._stop_event = threading.Event()
            self._workers = []
            self._held_keys = []
            while not self._skill_queue.empty():
                self._skill_queue.get_nowait()
            self._running = True
            self._paused = False
            profile = self.current_profile

        for skill in profile.skills:
            if skill.hotkey is None:
                continue
            if skill.action == SkillAction.HOLD:
                self._hold_key(skill.hotkey)
            elif skill.action == SkillAction.SPAM:
                self._spawn_periodic_worker(self._make_skill_worker(skill))
            elif skill.action == SkillAction.KEEP_BUFF:
                self._spawn_periodic_worker(self._make_skill_worker(skill))
            elif skill.action == SkillAction.KEY_TRIGGER and skill.trigger is None:
                print(f"[{profile.name}] 检测到按键触发策略，但触发键无效，已跳过。", flush=True)

        if profile.moving_method == MovingMethod.FORCE_STAND:
            self._hold_key(standing_key)
        elif profile.moving_method == MovingMethod.FORCE_MOVE_HOLD:
            self._hold_key(moving_key)
        elif profile.moving_method == MovingMethod.FORCE_MOVE_SPAM:
            self._spawn_periodic_worker(
                self._make_send_worker(
                    label="强制移动",
                    send_spec=moving_key,
                    interval_ms=max(profile.moving_interval_ms, 20),
                    delay_ms=0,
                    randomize_delay=False,
                    repeat=1,
                    repeat_interval_ms=0,
                )
            )

        if profile.potion_method == PotionMethod.TIMED:
            self._spawn_periodic_worker(
                self._make_send_worker(
                    label="自动喝药",
                    send_spec=potion_key,
                    interval_ms=max(profile.potion_interval_ms, 200),
                    delay_ms=0,
                    randomize_delay=False,
                    repeat=1,
                    repeat_interval_ms=0,
                )
            )
        elif profile.potion_method == PotionMethod.KEEP_CD:
            self._spawn_periodic_worker(self._make_potion_cooldown_worker(potion_key))

        if profile.use_skill_queue:
            self._spawn_periodic_worker(self._make_skill_queue_worker(profile.use_skill_queue_interval_ms))

        print(f"EVENT:macro_started:{profile.name}", flush=True)
        print(f"已启动 Linux 战斗宏：{profile.name}", flush=True)

    def stop_macro(self, reason: str | None) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._paused = False
            stop_event = self._stop_event
            workers = list(self._workers)
            held_keys = list(self._held_keys)
            self._workers = []
            self._held_keys = []
            while not self._skill_queue.empty():
                self._skill_queue.get_nowait()
        stop_event.set()
        for worker in workers:
            if worker.is_alive():
                worker.join(timeout=0.2)
        for send_spec in reversed(held_keys):
            try:
                self.sender.release(send_spec)
            except Exception:
                pass
        if reason:
            print(f"EVENT:macro_stopped:{reason}", flush=True)
            print(f"已停止战斗宏：{reason}", flush=True)
        else:
            print("EVENT:macro_stopped", flush=True)
            print("已停止战斗宏", flush=True)

    def toggle_pause(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._paused = not self._paused
            paused = self._paused
            held_keys = list(self._held_keys)
        if paused:
            for send_spec in reversed(held_keys):
                self.sender.release(send_spec)
            print("EVENT:macro_paused", flush=True)
            print("战斗宏已暂停", flush=True)
        else:
            for send_spec in held_keys:
                self.sender.press(send_spec)
            print("EVENT:macro_resumed", flush=True)
            print("战斗宏已恢复", flush=True)

    def send_once_actions(self) -> None:
        profile = self.current_profile
        for skill in profile.skills:
            if skill.action == SkillAction.HOLD and skill.hotkey is not None:
                self.sender.tap(skill.hotkey)
        print(f"已执行一次性按键：{profile.name}", flush=True)

    def switch_profile(self, index: int) -> None:
        with self._lock:
            if index == self.current_profile_index:
                return
            was_running = self._running
            was_paused = self._paused
        self.stop_macro(reason=None)
        self.current_profile_index = index
        profile = self.current_profile
        print(f"EVENT:profile_switched:{profile.name}", flush=True)
        print(f"已切换配置：{profile.name}", flush=True)
        if self.general.sound_on_profile_switch:
            play_notification_sound()
        self._print_profile_notes(profile)
        if was_running and not was_paused and profile.autostart_macro and profile.start_mode == StartMode.TOGGLE:
            self.run_macro()

    def _hold_key(self, send_spec: SendSpec) -> None:
        self.sender.press(send_spec)
        with self._lock:
            self._held_keys.append(send_spec)

    def _spawn_periodic_worker(self, target) -> None:
        worker = threading.Thread(target=target, daemon=True)
        with self._lock:
            self._workers.append(worker)
        worker.start()

    def _make_skill_worker(self, skill: SkillConfig):
        def worker() -> None:
            stop_event = self._stop_event
            interval_s = max(skill.interval_ms, 20) / 1000.0
            cycle_start = time.monotonic()
            if not self.general.run_on_start:
                cycle_start += interval_s
            while not stop_event.is_set():
                phase_s = self._compute_phase_seconds(skill.interval_ms, skill.delay_ms, skill.randomize_delay)
                due = cycle_start + phase_s
                if self._wait_until(stop_event, due):
                    break
                self._execute_skill(skill)
                cycle_start += interval_s
                while cycle_start < time.monotonic() - interval_s:
                    cycle_start += interval_s

        return worker

    def _execute_skill(self, skill: SkillConfig) -> None:
        if skill.hotkey is None:
            return
        with self._lock:
            if not self._running or self._paused:
                return
            use_queue = self.current_profile.use_skill_queue
        if skill.action in {SkillAction.SPAM, SkillAction.KEY_TRIGGER}:
            for repeat_index in range(max(skill.repeat, 1)):
                if use_queue:
                    self._skill_queue.put((skill.hotkey, QueueReason.SPAM))
                else:
                    self.sender.tap(skill.hotkey)
                if repeat_index + 1 < skill.repeat and skill.repeat_interval_ms > 0:
                    time.sleep(skill.repeat_interval_ms / 1000.0)
            return
        if skill.action != SkillAction.KEEP_BUFF:
            return
        active_window = self._active_window()
        if active_window is None:
            return
        resolution = parse_resolution(self.general.game_resolution)
        if resolution is not None:
            width, height = resolution
        else:
            width, height = active_window.width, active_window.height
        current_profile = self.current_profile
        for other in current_profile.skills:
            if other is skill:
                continue
            if other.action == SkillAction.KEEP_BUFF and other.priority > skill.priority and other.hotkey is not None:
                other_active = self._is_buff_active_live(width, height, current_profile.skills.index(other) + 1)
                if other_active is None:
                    return
                if other_active:
                    return
        skill_index = current_profile.skills.index(skill) + 1
        current_active = self._is_buff_active_live(width, height, skill_index)
        if current_active is None:
            return
        if current_active:
            return
        if use_queue:
            self._skill_queue.put((skill.hotkey, QueueReason.KEEP_BUFF))
        elif skill.hotkey.base == "mouse:left":
            self._send_with_force_standing(skill.hotkey)
        else:
            self.sender.tap(skill.hotkey)

    def _is_buff_active(self, image: GameImage, width: int, height: int, button_id: int) -> bool:
        point = get_skill_button_buff_pos(width, height, button_id, self.general.buff_percent)
        rgb = image.get_pixel_rgb(point)
        return rgb[1] >= 95

    def _capture_region_rgb(self, point_x: int, point_y: int, width: int, height: int, agg_func: str = ""):
        if self._capture is None or not hasattr(self._capture, "capture_region"):
            return None
        captured = self._capture.capture_region(point_x, point_y, width, height)
        if captured is None:
            return None
        _window, pixels = captured
        return pixels_region_to_rgb(pixels, self.general.game_gamma, agg_func)

    def _is_buff_active_live(self, width: int, height: int, button_id: int) -> bool | None:
        point = get_skill_button_buff_pos(width, height, button_id, self.general.buff_percent)
        rgb = self._capture_region_rgb(point[0], point[1], 1, 1, "max")
        if rgb is None:
            return None
        return rgb[1] >= 95

    def _make_send_worker(
        self,
        label: str,
        send_spec: SendSpec | None,
        interval_ms: int,
        delay_ms: int,
        randomize_delay: bool,
        repeat: int,
        repeat_interval_ms: int,
    ):
        if send_spec is None:
            return lambda: None

        def worker() -> None:
            stop_event = self._stop_event
            interval_s = interval_ms / 1000.0
            cycle_start = time.monotonic()
            if not self.general.run_on_start:
                cycle_start += interval_s

            while not stop_event.is_set():
                phase_s = self._compute_phase_seconds(interval_ms, delay_ms, randomize_delay)
                due = cycle_start + phase_s
                if self._wait_until(stop_event, due):
                    break
                with self._lock:
                    paused = self._paused
                    running = self._running
                if running and not paused:
                    for repeat_index in range(repeat):
                        if stop_event.is_set():
                            break
                        self.sender.tap(send_spec)
                        if repeat_index + 1 < repeat and repeat_interval_ms > 0:
                            time.sleep(repeat_interval_ms / 1000.0)
                cycle_start += interval_s
                while cycle_start < time.monotonic() - interval_s:
                    cycle_start += interval_s

        return worker

    def _compute_phase_seconds(self, interval_ms: int, delay_ms: int, randomize_delay: bool) -> float:
        if delay_ms == 0:
            return 0.0
        absolute = min(abs(delay_ms), interval_ms)
        sampled = random.randint(0, absolute) if randomize_delay and absolute > 0 else absolute
        if delay_ms < 0:
            return max(interval_ms - sampled, 0) / 1000.0
        return sampled / 1000.0

    def _make_potion_cooldown_worker(self, potion_key: SendSpec):
        last_region = None

        def worker() -> None:
            nonlocal last_region
            stop_event = self._stop_event
            interval_s = max(self.current_profile.potion_interval_ms, 200) / 1000.0
            cycle_start = time.monotonic()
            while not stop_event.is_set():
                if self._wait_until(stop_event, cycle_start):
                    break
                active_window = self._active_window()
                if active_window is not None:
                    resolution = parse_resolution(self.general.game_resolution)
                    if resolution is not None:
                        width, height = resolution
                    else:
                        width, height = active_window.width, active_window.height
                    region = self._capture_region_rgb(
                        round(width / 2 - (3440 / 2 - 1822) * height / 1440.0),
                        round(1340 * height / 1440.0),
                        round(66 * height / 1440.0),
                        round(66 * height / 1440.0),
                    )
                    if region is None:
                        cycle_start += interval_s
                        continue
                    current_flat = region[0] + region[1] + region[2]
                    if last_region is not None and arrays_equal(last_region, current_flat, 0):
                        self.sender.tap(potion_key)
                    last_region = current_flat
                cycle_start += interval_s

        return worker

    def _make_skill_queue_worker(self, interval_ms: int):
        def worker() -> None:
            stop_event = self._stop_event
            delay_s = max(interval_ms, 50) / 1000.0
            while not stop_event.is_set():
                if not self._skill_queue.empty():
                    self._process_skill_queue_once(max(interval_ms, 50))
                if stop_event.wait(delay_s):
                    break

        return worker

    def _process_skill_queue_once(self, interval_ms: int) -> None:
        if self._skill_queue.empty():
            return
        try:
            send_spec, reason = self._skill_queue.get_nowait()
        except queue.Empty:
            return
        held_keys = list(self._held_keys)
        if reason == QueueReason.SPAM:
            for held in reversed(held_keys):
                self.sender.release(held)
            time.sleep(interval_ms / 4000.0)

        if send_spec.base == "mouse:left" or reason == QueueReason.SPAM:
            self._send_with_force_standing(send_spec, hold_ms=interval_ms // 4 if reason == QueueReason.SPAM else 0)
        else:
            self.sender.tap(send_spec)

        if reason == QueueReason.SPAM:
            time.sleep(interval_ms / 4000.0)
            for held in held_keys:
                self.sender.press(held)

    def _send_with_force_standing(self, send_spec: SendSpec, hold_ms: int = 0) -> None:
        standing_key = self.general.custom_standing_key if self.general.custom_standing_enabled else parse_send_spec("LShift")
        if standing_key is None:
            self.sender.tap(send_spec)
            return
        self.sender.press(standing_key)
        try:
            self.sender.click_mouse(send_spec, hold_ms) if send_spec.base.startswith("mouse:") else self.sender.tap(send_spec)
        finally:
            self.sender.release(standing_key)

    def _capture_game_image(self) -> tuple[GameImage, int, int] | None:
        if self._capture is None:
            return None
        image = self._capture.capture()
        if image is None:
            return None
        resolution = parse_resolution(self.general.game_resolution)
        if resolution is not None:
            width, height = resolution
        else:
            width, height = image.width, image.height
        return image, width, height

    def _active_window(self) -> WindowInfo | None:
        if self._capture is None:
            return None
        return self._capture.get_active_window()

    def handle_quick_pause(self, quick_pause: QuickPauseConfig) -> None:
        if not self._running:
            return
        self.stop_macro(reason=None)
        if quick_pause.mode == QuickPauseMode.HOLD:
            if quick_pause.action == QuickPauseAction.PAUSE_AND_SPAM_LEFT:
                threading.Thread(
                    target=self._quick_pause_click_loop,
                    args=(quick_pause.trigger.base if quick_pause.trigger else "",),
                    daemon=True,
                ).start()
            return
        if quick_pause.action == QuickPauseAction.PAUSE_AND_SPAM_LEFT:
            self._quick_pause_click_until(time.monotonic() + quick_pause.delay_ms / 1000.0)
        threading.Thread(target=self._resume_macro_after_delay, args=(quick_pause.delay_ms,), daemon=True).start()

    def _quick_pause_click_loop(self, trigger_base: str) -> None:
        while trigger_base and trigger_base in self._pressed_bases:
            self._quick_pause_left_click()
            time.sleep(0.05)

    def _quick_pause_click_until(self, end_time: float) -> None:
        while time.monotonic() < end_time:
            self._quick_pause_left_click()
            time.sleep(0.05)

    def _quick_pause_left_click(self) -> None:
        left = parse_send_spec("LButton")
        if left is None:
            return
        self._send_with_force_standing(left)

    def _resume_macro_after_delay(self, delay_ms: int) -> None:
        time.sleep(max(delay_ms, 50) / 1000.0)
        self.run_macro()

    def trigger_helper(self) -> None:
        with self._lock:
            if self._helper_running:
                self._helper_break = True
                print("已请求停止当前助手流程。", flush=True)
                return
            if self._running:
                print("战斗宏运行中，当前不会启动助手。", flush=True)
                return
            self._helper_running = True
            self._helper_break = False
        print("已收到助手热键，正在识别当前界面...", flush=True)
        self._helper_thread = threading.Thread(target=self._run_helper, daemon=True)
        self._helper_thread.start()

    def _run_helper(self) -> None:
        try:
            capture = self._capture_game_image()
            if capture is None:
                print("助手未执行：无法截取当前游戏画面。", flush=True)
                return
            image, width, height = capture
            window = image.window
            mouse_x, mouse_y = self.sender.mouse_position()
            rel_x = mouse_x - window.x
            rel_y = mouse_y - window.y
            mouse_position = -1
            if rel_x > width - (3440 - 2740) * height / 1440.0 and 730 * height / 1440.0 < rel_y < 1150 * height / 1440.0:
                mouse_position = 1
            elif 65 * height / 1440.0 < rel_x < 640 * height / 1440.0 and 275 * height / 1440.0 < rel_y < 1150 * height / 1440.0:
                mouse_position = 2

            if rel_x < 680 * height / 1440.0 and self.general.helper.gamble_enabled and is_gamble_open(image, height):
                print(f"助手已启动：识别到赌博界面，连续右键 {self.general.helper.gamble_times} 次。", flush=True)
                self._gamble_helper()
                return

            if self.general.helper.salvage_enabled:
                salvage_state = is_salvage_page_open(image, width, height)
                if salvage_state[0] == 2:
                    if self.general.helper.salvage_method == SalvageMethod.QUICK and mouse_position == 1:
                        print("助手已启动：识别到分解页，执行快速分解。", flush=True)
                        self._quick_salvage_helper(width, height)
                        return
                    if not self._prepare_salvage_helper_mode(width, height, salvage_state):
                        if not self._helper_should_break():
                            print("助手未执行：无法进入可分解状态。", flush=True)
                        return
                    print("助手已启动：识别到分解页，执行一键/智能分解。", flush=True)
                    self._one_button_salvage_helper(width, height, mouse_x, mouse_y)
                    return
                if salvage_state[0] == 1:
                    print("助手未执行：识别到分解界面，但当前标签页不是可执行的装备分解页。", flush=True)
                    return

            if self.general.helper.reforge_enabled or self.general.helper.upgrade_enabled or self.general.helper.convert_enabled:
                kanai_state = is_kanai_cube_open(image, width, height, window.title)
                if kanai_state == 2 and self.general.helper.reforge_enabled and mouse_position == 1:
                    print("助手已启动：识别到卡奈魔盒重铸页，开始重铸。", flush=True)
                    self._one_button_reforge_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 3 and self.general.helper.upgrade_enabled:
                    print("助手已启动：识别到卡奈魔盒升级页，开始升级黄色装备。", flush=True)
                    self._one_button_upgrade_convert_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 4 and self.general.helper.convert_enabled:
                    print("助手已启动：识别到卡奈魔盒转化页，开始转化材料。", flush=True)
                    self._one_button_upgrade_convert_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 1:
                    print("助手未执行：识别到卡奈魔盒，但当前不是重铸/升级/转化页。", flush=True)
                    return

            if self.general.helper.abandon_enabled and mouse_position > 0 and is_inventory_open(image, width, height):
                print("助手已启动：识别到背包界面，执行丢装助手。", flush=True)
                self._one_button_abandon_helper(width, height, mouse_x, mouse_y, mouse_position)
                return

            if self.general.helper.loot_enabled:
                print("助手已启动：执行拾取助手。", flush=True)
                self._loot_helper(width, height)
                return
            print(f"助手未执行：未识别到已启用的助手场景。前台窗口：{format_window_debug(window)}", flush=True)
        finally:
            with self._lock:
                self._helper_running = False
                self._helper_break = False

    def _helper_sleep(self, ms: int) -> None:
        time.sleep(max(ms, 1) / 1000.0)

    def _helper_should_break(self) -> bool:
        return self._helper_break or self._shutdown_event.is_set()

    def _move_mouse(self, x: int, y: int) -> None:
        self.sender.move_mouse(x, y)
        self._helper_sleep(max(self.general.helper.animation_delay_ms // 4, 1))

    def _click_left(self) -> None:
        left = parse_send_spec("LButton")
        if left is not None:
            self.sender.click_mouse(left)

    def _click_right(self) -> None:
        right = parse_send_spec("RButton")
        if right is not None:
            self.sender.click_mouse(right)

    def _tap_enter(self) -> None:
        enter = parse_send_spec("Enter")
        if enter is not None:
            self.sender.tap(enter)

    def _gamble_helper(self) -> None:
        for _ in range(self.general.helper.gamble_times):
            if self._helper_should_break():
                break
            self._click_right()
            self._helper_sleep(self.general.helper.animation_delay_ms // 4)

    def _loot_helper(self, width: int, height: int) -> None:
        window = self._active_window()
        if window is None:
            return
        mouse_x, mouse_y = self.sender.mouse_position()
        if abs(mouse_x - (window.x + width / 2)) < 600 * 1440 / height and abs(mouse_y - (window.y + height / 2)) < 500 * 1440 / height:
            for _ in range(self.general.helper.loot_times):
                if self._helper_should_break():
                    break
                self._click_left()
                self._helper_sleep(self.general.helper.animation_delay_ms // 2)
        else:
            self._click_left()

    def _quick_salvage_helper(self, width: int, height: int) -> None:
        self._click_left()
        self._helper_sleep(self.general.helper.animation_delay_ms)
        capture = self._capture_game_image()
        if capture is None:
            return
        image, cur_width, cur_height = capture
        if is_dialog_box_on_screen(image, cur_width, cur_height):
            self._tap_enter()

    def _prepare_salvage_helper_mode(self, width: int, height: int, salvage_state) -> bool:
        window = self._active_window()
        if window is None:
            return False
        salvage_icons = get_salvage_icon_xy(height, "center")
        self._move_mouse(window.x + salvage_icons[0][0], window.y + salvage_icons[0][1])
        if salvage_mode_is_armed(salvage_state):
            if self._helper_should_break():
                return False
            self._click_right()
            self._helper_sleep(self.general.helper.animation_delay_ms)
            capture = self._capture_game_image()
            if capture is None:
                return False
            image, _, _ = capture
            salvage_state = is_salvage_page_open(image, width, height)
            if not salvage_state or salvage_state[0] != 2:
                return False
        bulk_clicked = False
        for button_index in salvage_bulk_buttons_from_state(salvage_state):
            if self._helper_should_break():
                return False
            point = salvage_icons[button_index]
            self._move_mouse(window.x + point[0], window.y + point[1])
            self._click_left()
            self._helper_sleep(self.general.helper.animation_delay_ms)
            self._tap_enter()
            bulk_clicked = True
        if self._helper_should_break():
            return False
        self._move_mouse(window.x + salvage_icons[0][0], window.y + salvage_icons[0][1])
        self._helper_sleep(max(self.general.helper.animation_delay_ms // 2, 1))
        self._click_left()
        self._helper_sleep(max(self.general.helper.animation_delay_ms // 2, 1))
        if bulk_clicked:
            self._helper_sleep(self.general.helper.animation_delay_ms + 50)
        return True

    def _classify_item_quality(self, sample_rgb: list[int], allow_ethereal: bool = True) -> int:
        if (
            (sample_rgb[0] >= 70 or sample_rgb[2] <= 20)
            and max(abs(sample_rgb[0] - sample_rgb[1]), abs(sample_rgb[0] - sample_rgb[2]), abs(sample_rgb[2] - sample_rgb[1])) > 20
            and sum(sample_rgb) < 460
        ):
            return 5 if sample_rgb[1] < 35 else 3
        if sample_rgb[2] > 100 and sample_rgb[2] > sample_rgb[1] > sample_rgb[0]:
            return 4
        if allow_ethereal and sample_rgb[0] < 50 and sample_rgb[1] > sample_rgb[2] > sample_rgb[0]:
            return 4
        return 2

    def _sample_stable_rgb(self, point_x: int, point_y: int, width: int = 3, height: int = 1, timeout_ms: int = 150) -> list[int]:
        deadline = time.monotonic() + timeout_ms / 1000.0
        previous = [-255, -255, -255]
        while time.monotonic() < deadline:
            capture = self._capture_game_image()
            if capture is None:
                return previous
            image, _, _ = capture
            current = image.get_pixels_rgb(point_x, point_y, width, height, "max")
            if arrays_equal(previous, current, 0):
                return current
            previous = current
            self._helper_sleep(20)
        return previous

    def _one_button_reforge_helper(self, width: int, height: int, mouse_x: int, mouse_y: int) -> None:
        window = self._active_window()
        if window is None:
            return
        kanai = get_kanai_cube_button_pos(height)
        box_1_1 = get_inventory_space_xy(width, height, 1, "kanai")
        box_1_2 = get_inventory_space_xy(width, height, 2, "kanai")
        for _ in range(self.general.helper.max_reforge):
            if self._helper_should_break():
                break
            self._click_right()
            self._helper_sleep(self.general.helper.animation_delay_ms // 4)
            for point in [kanai[1], kanai[0], kanai[2], kanai[3]]:
                self._move_mouse(window.x + point[0], window.y + point[1])
                self._click_left()
                self._helper_sleep(self.general.helper.animation_delay_ms // 4)
            if self.general.helper.reforge_method <= ReforgeMethod.ONCE:
                break
            self._move_mouse(mouse_x, mouse_y)
            self._click_right()
            self._move_mouse(window.x + box_1_1[0], window.y + box_1_1[1])
            self._helper_sleep(self.general.helper.animation_delay_ms // 2)
            color = self._sample_stable_rgb(box_1_2[2] + 1, box_1_2[1], 3, 1, self.general.helper.animation_delay_ms)
            quality = self._classify_item_quality(color, allow_ethereal=False)
            self._move_mouse(mouse_x, mouse_y)
            if quality > self.general.helper.reforge_method:
                break

    def _one_button_upgrade_convert_helper(self, width: int, height: int, mouse_x: int, mouse_y: int) -> None:
        window = self._active_window()
        if window is None:
            return
        bag_zone, _ = self._scan_inventory_state(width, height)
        kanai = get_kanai_cube_button_pos(height)
        for slot_id in range(1, 61):
            if self._helper_should_break():
                break
            if bag_zone[slot_id] != 10:
                continue
            current = get_inventory_space_xy(width, height, slot_id, "bag")
            below = get_inventory_space_xy(width, height, min(slot_id + 10, 60), "bag")
            large_item = slot_id <= 50 and bag_zone[min(slot_id + 10, 60)] in {-1, 10}
            below_before = None
            self._move_mouse(window.x + current[0], window.y + current[1])
            self._click_right()
            if large_item:
                capture = self._capture_game_image()
                if capture is not None:
                    image, _, _ = capture
                    below_before = image.get_pixel_rgb([below[0], below[1]])
            self._helper_sleep(self.general.helper.animation_delay_ms)
            for point in [kanai[1], kanai[0], kanai[3], kanai[2]]:
                self._move_mouse(window.x + point[0], window.y + point[1])
                self._click_left()
                self._helper_sleep(self.general.helper.animation_delay_ms + 50)
            if below_before is not None:
                capture = self._capture_game_image()
                if capture is not None:
                    image, _, _ = capture
                    if not arrays_equal(below_before, image.get_pixel_rgb([below[0], below[1]]), 3):
                        bag_zone[min(slot_id + 10, 60)] = 5
        self._move_mouse(mouse_x, mouse_y)

    def _one_button_salvage_helper(self, width: int, height: int, mouse_x: int, mouse_y: int) -> None:
        window = self._active_window()
        if window is None:
            return
        bag_zone, inventory_colors = self._scan_inventory_state(width, height)
        for slot_id in range(1, 61):
            if self._helper_should_break():
                break
            if bag_zone[slot_id] != 10:
                continue
            slot = get_inventory_space_xy(width, height, slot_id, "bag")
            self._move_mouse(window.x + slot[0], window.y + slot[1])
            quality = 0
            if self.general.helper.salvage_method > SalvageMethod.ONE_CLICK:
                color = self._sample_stable_rgb(round(slot[2] - 1 - 10 * height / 1440.0), slot[1], 3, 1, self.general.helper.animation_delay_ms)
                quality = self._classify_item_quality(color, allow_ethereal=True)
            if slot_id <= 50 and bag_zone[min(slot_id + 10, 60)] in {-1, 10}:
                below = get_inventory_space_xy(width, height, slot_id + 10, "bag")
                before = inventory_colors.get(slot_id + 10, [-255, -255, -255])
                after = self._sample_stable_rgb(
                    round(below[2] + 64 * 0.08 * height / 1440.0),
                    round(below[3] + 63 * 0.7 * height / 1440.0),
                    1,
                    1,
                    self.general.helper.animation_delay_ms,
                )
                if not arrays_equal(before, after, 0):
                    bag_zone[slot_id + 10] = 5
            if quality >= self.general.helper.salvage_method:
                continue
            self._click_left()
            deadline = time.monotonic() + self.general.helper.animation_delay_ms / 1000.0
            while time.monotonic() < deadline:
                capture = self._capture_game_image()
                if capture is None:
                    break
                image, cur_width, cur_height = capture
                if is_dialog_box_on_screen(image, cur_width, cur_height):
                    self._helper_sleep(self.general.helper.animation_delay_ms // 4)
                    self._tap_enter()
                    break
            self._helper_sleep(self.general.helper.animation_delay_ms // 2)
        self._click_right()
        self._move_mouse(mouse_x, mouse_y)

    def _one_button_abandon_helper(self, width: int, height: int, mouse_x: int, mouse_y: int, mouse_position: int) -> None:
        window = self._active_window()
        if window is None:
            return
        bag_zone, _ = self._scan_inventory_state(width, height)
        stash_open = None
        for slot_id in range(1, 61):
            if self._helper_should_break():
                break
            if bag_zone[slot_id] != 10:
                continue
            slot = get_inventory_space_xy(width, height, slot_id, "bag")
            self._move_mouse(window.x + slot[0], window.y + slot[1])
            if stash_open is None:
                capture = self._capture_game_image()
                if capture is None:
                    break
                image, _, cur_height = capture
                stash_open = is_stash_open(image, cur_height)
                if not stash_open and mouse_position != 1:
                    break
            if mouse_position == 1:
                self._click_left()
                self._helper_sleep(self.general.helper.animation_delay_ms // 2)
                self._move_mouse(window.x + width // 2, window.y + height // 2)
                left = parse_send_spec("LButton")
                if left is not None:
                    self._send_with_force_standing(left)
            else:
                self._click_right()
                self._helper_sleep(self.general.helper.animation_delay_ms // 2)
        self._move_mouse(mouse_x, mouse_y)

    def _scan_inventory_state(self, width: int, height: int):
        capture = self._capture_game_image()
        if capture is None:
            return [-1] * 61, {}
        image, _, _ = capture
        return scan_inventory_space(image, width, height, self.general.helper.safezone)

    def _start_focus_monitor(self) -> None:
        if not self.general.d3only or self.matcher is None or self._focus_thread is not None:
            return

        def monitor() -> None:
            while not self._shutdown_event.is_set():
                with self._lock:
                    running = self._running
                if running and not self.matcher.matches_active_window():
                    self.stop_macro(reason="检测到窗口焦点已离开游戏")
                if self._shutdown_event.wait(0.3):
                    break

        self._focus_thread = threading.Thread(target=monitor, daemon=True)
        self._focus_thread.start()

    def _print_profile_notes(self, profile: ProfileConfig) -> None:
        notes: list[str] = []
        if self._capture is None and any(skill.action == SkillAction.KEEP_BUFF for skill in profile.skills):
            notes.append("保持 Buff 需要图像捕获依赖")
        if self._capture is None and profile.potion_method == PotionMethod.KEEP_CD:
            notes.append("保持药水 CD 需要图像捕获依赖")
        if notes:
            print(f"[{profile.name}] 当前配置提示：{', '.join(notes)}", flush=True)

    def _print_helper_notes(self) -> None:
        enabled_helpers = describe_enabled_helpers(self.general.helper)
        helper_summary = "、".join(enabled_helpers) if enabled_helpers else "无已启用助手"
        print(
            f"助手热键：{format_hotkey(self.general.helper.hotkey)}；已启用：{helper_summary}",
            flush=True,
        )
        if session_uses_wayland_keyboard_hotkeys(self.general.helper.hotkey):
            print(
                "当前为 Wayland 会话，键盘全局热键可能不稳定；若 F5 没反应，优先改用鼠标侧键/滚轮，或改用 X11/XWayland。",
                flush=True,
            )


def normalize_token(raw: str) -> str:
    return raw.strip().replace(" ", "").lower()


def parse_hotkey_expression(expr: str) -> HotkeySpec | None:
    expr = expr.strip()
    if not expr:
        return None
    modifiers: set[str] = set()
    while expr and expr[0] in HOTKEY_MODIFIER_PREFIX:
        modifiers.add(HOTKEY_MODIFIER_PREFIX[expr[0]])
        expr = expr[1:]
    expr = expr.strip()
    if not expr:
        return None
    if "+" in expr:
        parts = [part.strip() for part in expr.split("+") if part.strip()]
        if len(parts) > 1:
            maybe_modifiers = [normalize_token(part) for part in parts[:-1]]
            if all(part in HOTKEY_MODIFIER_NAMES for part in maybe_modifiers):
                modifiers.update(HOTKEY_MODIFIER_NAMES[part] for part in maybe_modifiers)
                expr = parts[-1]
    base = normalize_hotkey_base(expr)
    if base is None:
        return None
    return HotkeySpec(base=base, modifiers=frozenset(modifiers))


def normalize_hotkey_base(raw: str) -> str | None:
    token = normalize_token(raw)
    if not token:
        return None
    if token in MOUSE_EVENT_ALIASES:
        return MOUSE_EVENT_ALIASES[token]
    if token in HOTKEY_MODIFIER_NAMES:
        return HOTKEY_MODIFIER_NAMES[token]
    if token in SPECIAL_KEY_ALIASES:
        return SPECIAL_KEY_ALIASES[token]
    if re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", token):
        return token
    if re.fullmatch(r"[a-z0-9]", token):
        return token
    numpad_match = re.fullmatch(r"numpad([0-9])", token)
    if numpad_match:
        return numpad_match.group(1)
    numpad_alias = {
        "numpaddot": ".",
        "numpaddiv": "/",
        "numpadmult": "*",
        "numpadsub": "-",
        "numpadadd": "+",
    }
    if token in numpad_alias:
        return numpad_alias[token]
    punctuation = {
        "`": "`",
        "~": "`",
        "-": "-",
        "=": "=",
        "[": "[",
        "]": "]",
        "\\": "\\",
        ";": ";",
        "'": "'",
        ",": ",",
        ".": ".",
        "/": "/",
    }
    if token in punctuation:
        return punctuation[token]
    return None


def parse_send_spec(expr: str) -> SendSpec | None:
    base = normalize_hotkey_base(expr)
    if base is None:
        return None
    if base in {"wheel_up", "wheel_down"}:
        return None
    return SendSpec(base=base)


def parse_boolean(value: str, default: bool) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_float(value: str, default: float) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_safezone(value: str) -> set[int]:
    out: set[int] = set()
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            number = int(part)
        except ValueError:
            continue
        if 1 <= number <= 60:
            out.add(number)
    return out


def method_to_hotkey(method: int, keyboard_expr: str, mapping: dict[int, str]) -> HotkeySpec | None:
    if method in mapping:
        return HotkeySpec(mapping[method])
    if method == 7:
        return parse_hotkey_expression(keyboard_expr)
    return None


def load_config(config_path: Path) -> tuple[GeneralConfig, list[ProfileConfig]]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower

    encodings = ["utf-16", "utf-8-sig", "utf-8"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with config_path.open("r", encoding=encoding) as handle:
                parser.read_file(handle)
            break
        except FileNotFoundError as exc:
            raise ConfigError(f"配置文件不存在：{config_path}") from exc
        except Exception as exc:
            last_error = exc
    else:
        raise ConfigError(f"无法读取配置文件：{config_path} ({last_error})")

    general_name = next((name for name in parser.sections() if name.lower() == "general"), None)
    if general_name is None:
        raise ConfigError("配置文件缺少 [General] 区块。")
    general_section = parser[general_name]
    profile_names = [name for name in parser.sections() if name.lower() != "general"]
    if not profile_names:
        raise ConfigError("配置文件中没有任何技能配置区块。")

    general = GeneralConfig(
        activated_profile=max(parse_int(general_section.get("activatedprofile", gd("activatedprofile")), 1), 1),
        start_hotkey=method_to_hotkey(
            parse_int(general_section.get("startmethod", gd("startmethod")), 7),
            general_section.get("starthotkey", gd("starthotkey")),
            START_METHOD_MOUSE,
        ),
        run_on_start=parse_boolean(general_section.get("runonstart", gd("runonstart")), True),
        d3only=parse_boolean(general_section.get("d3only", gd("d3only")), True),
        smart_pause=parse_boolean(general_section.get("enablesmartpause", gd("enablesmartpause")), True),
        sound_on_profile_switch=parse_boolean(general_section.get("enablesoundplay", gd("enablesoundplay")), True),
        custom_standing_enabled=parse_boolean(general_section.get("customstanding", gd("customstanding")), False),
        custom_standing_key=parse_send_spec(general_section.get("customstandinghk", gd("customstandinghk"))) or SendSpec("shift"),
        custom_moving_enabled=parse_boolean(general_section.get("custommoving", gd("custommoving")), False),
        custom_moving_key=parse_send_spec(general_section.get("custommovinghk", gd("custommovinghk"))) or SendSpec("e"),
        custom_potion_enabled=parse_boolean(general_section.get("custompotion", gd("custompotion")), False),
        custom_potion_key=parse_send_spec(general_section.get("custompotionhk", gd("custompotionhk"))) or SendSpec("q"),
        game_gamma=parse_float(general_section.get("gamegamma", gd("gamegamma")), 1.0),
        buff_percent=parse_float(general_section.get("buffpercent", gd("buffpercent")), 0.05),
        game_resolution=general_section.get("gameresolution", gd("gameresolution")),
        helper=HelperConfig(
            hotkey=method_to_hotkey(
                parse_int(general_section.get("oldsandhelpermethod", gd("oldsandhelpermethod")), 7),
                general_section.get("oldsandhelperhk", gd("oldsandhelperhk")),
                COMMON_METHOD_MOUSE,
            ),
            gamble_enabled=parse_boolean(general_section.get("enablegamblehelper", gd("enablegamblehelper")), True),
            gamble_times=max(parse_int(general_section.get("gamblehelpertimes", gd("gamblehelpertimes")), 15), 1),
            loot_enabled=parse_boolean(general_section.get("enableloothelper", gd("enableloothelper")), False),
            loot_times=max(parse_int(general_section.get("loothelpertimes", gd("loothelpertimes")), 30), 1),
            salvage_enabled=parse_boolean(general_section.get("enablesalvagehelper", gd("enablesalvagehelper")), False),
            salvage_method=parse_int(general_section.get("salvagehelpermethod", gd("salvagehelpermethod")), 1),
            reforge_enabled=parse_boolean(general_section.get("enablereforgehelper", gd("enablereforgehelper")), False),
            reforge_method=parse_int(general_section.get("reforgehelpermethod", gd("reforgehelpermethod")), 1),
            upgrade_enabled=parse_boolean(general_section.get("enableupgradehelper", gd("enableupgradehelper")), False),
            convert_enabled=parse_boolean(general_section.get("enableconverthelper", gd("enableconverthelper")), False),
            abandon_enabled=parse_boolean(general_section.get("enableabandonhelper", gd("enableabandonhelper")), False),
            mouse_speed=max(parse_int(general_section.get("helpermousespeed", gd("helpermousespeed")), 2), 0),
            animation_delay_ms=max(parse_int(general_section.get("helperanimationdelay", gd("helperanimationdelay")), 150), 1),
            max_reforge=max(parse_int(general_section.get("maxreforge", gd("maxreforge")), 10), 1),
            safezone=parse_safezone(general_section.get("safezone", gd("safezone"))),
        ),
    )

    profiles: list[ProfileConfig] = []
    for section_name in profile_names:
        section = parser[section_name]
        skills: list[SkillConfig] = []
        for index in range(1, 7):
            action = parse_int(section.get(f"action_{index}", sd("action")), 1)
            skills.append(
                SkillConfig(
                    hotkey=parse_send_spec(section.get(f"skill_{index}", skill_hotkey_default(index))),
                    action=action,
                    interval_ms=max(parse_int(section.get(f"interval_{index}", sd("interval")), 300), 20),
                    delay_ms=parse_int(section.get(f"delay_{index}", sd("delay")), 10),
                    randomize_delay=parse_boolean(section.get(f"random_{index}", sd("random")), True),
                    priority=max(parse_int(section.get(f"priority_{index}", sd("priority")), 1), 1),
                    repeat=max(parse_int(section.get(f"repeat_{index}", sd("repeat")), 1), 1),
                    repeat_interval_ms=max(parse_int(section.get(f"repeatinterval_{index}", sd("repeatinterval")), 30), 0),
                    trigger=parse_hotkey_expression(section.get(f"triggerbutton_{index}", sd("triggerbutton"))),
                )
            )

        profiles.append(
            ProfileConfig(
                name=section_name,
                skills=skills,
                profile_hotkey=method_to_hotkey(
                    parse_int(section.get("profilehkmethod", pd("profilehkmethod")), 1),
                    section.get("profilehkkey", pd("profilehkkey")),
                    COMMON_METHOD_MOUSE,
                ),
                autostart_macro=parse_boolean(section.get("autostartmarco", pd("autostartmarco")), False),
                start_mode=parse_int(section.get("lazymode", pd("lazymode")), 1),
                moving_method=parse_int(section.get("movingmethod", pd("movingmethod")), 1),
                moving_interval_ms=max(parse_int(section.get("movinginterval", pd("movinginterval")), 100), 20),
                potion_method=parse_int(section.get("potionmethod", pd("potionmethod")), 1),
                potion_interval_ms=max(parse_int(section.get("potioninterval", pd("potioninterval")), 500), 200),
                use_skill_queue=parse_boolean(section.get("useskillqueue", pd("useskillqueue")), False),
                use_skill_queue_interval_ms=max(parse_int(section.get("useskillqueueinterval", pd("useskillqueueinterval")), 200), 50),
                quick_pause=QuickPauseConfig(
                    enabled=parse_boolean(section.get("enablequickpause", pd("enablequickpause")), False),
                    mode=parse_int(section.get("quickpausemethod1", pd("quickpausemethod1")), 1),
                    trigger=method_to_hotkey(
                        parse_int(section.get("quickpausemethod2", pd("quickpausemethod2")), 1),
                        "",
                        QUICK_PAUSE_MOUSE,
                    ),
                    action=parse_int(section.get("quickpausemethod3", pd("quickpausemethod3")), 1),
                    delay_ms=max(parse_int(section.get("quickpausedelay", pd("quickpausedelay")), 1500), 50),
                ),
            )
        )

    return general, profiles


def default_skill_hotkey(index: int) -> str:
    return skill_hotkey_default(index)


def default_profile_dict() -> dict[str, str]:
    """Return the default key/value pairs for a new profile section."""
    return _schema_default_profile_dict()


def default_config_dir() -> Path:
    base_dir = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if base_dir:
        return Path(base_dir).expanduser() / CONFIG_DIR_NAME
    return Path.home() / ".config" / CONFIG_DIR_NAME


def default_config_path() -> Path:
    return default_config_dir() / CONFIG_FILE_NAME


def create_default_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    parser["General"] = build_general_section(DEFAULT_VERSION)
    for name in DEFAULT_PROFILE_NAMES:
        parser[name] = default_profile_dict()

    with config_path.open("w", encoding="utf-16") as handle:
        handle.write("; Linux native config for D3keyHelper\r\n")
        parser.write(handle)


def resolve_profile_index(profiles: list[ProfileConfig], selection: str | None, activated_profile: int) -> int:
    if not selection:
        return max(min(activated_profile - 1, len(profiles) - 1), 0)
    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(profiles):
            return index
        raise ConfigError(f"配置编号超出范围：{selection}")
    for index, profile in enumerate(profiles):
        if profile.name == selection:
            return index
    raise ConfigError(f"找不到配置：{selection}")


def ensure_runtime_dependencies() -> None:
    if keyboard is None or mouse is None:
        raise ConfigError("未安装 pynput，请先执行：pip install -r requirements.txt")
    if xdisplay is None or X is None:
        raise ConfigError("未安装 python-xlib，请先执行：pip install -r requirements.txt")
    if mss is None:
        raise ConfigError("未安装 mss，请先执行：pip install -r requirements.txt")
    if np is None:
        raise ConfigError("未安装 numpy，请先执行：pip install -r requirements.txt")
    if Image is None:
        raise ConfigError("未安装 Pillow，请先执行：pip install -r requirements.txt")


def normalize_keyboard_event(key_event) -> str | None:
    if keyboard is None:
        return None
    if isinstance(key_event, keyboard.KeyCode):
        if key_event.char is None:
            return None
        return key_event.char.lower()
    if hasattr(key_event, "name") and key_event.name:
        return SPECIAL_KEY_ALIASES.get(key_event.name, key_event.name)
    raw = str(key_event)
    if raw.startswith("Key."):
        return SPECIAL_KEY_ALIASES.get(raw[4:], raw[4:])
    return None


def normalize_mouse_button(button_event) -> str | None:
    if mouse is None:
        return None
    button_name = getattr(button_event, "name", None)
    if button_name == "left":
        return "mouse:left"
    if button_name == "right":
        return "mouse:right"
    if button_name == "middle":
        return "mouse:middle"
    if button_name in {"x1", "x2"}:
        return f"mouse:{button_name}"
    return None


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Linux native combat macro runner for D3keyHelper.")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help=f"配置文件路径，默认 {default_config_path()}",
    )
    parser.add_argument("--gui", action="store_true", help="启动 Linux 图形界面配置器")
    parser.add_argument("--init-config", action="store_true", help="生成一份默认配置文件后退出")
    parser.add_argument("--list-profiles", action="store_true", help="列出配置文件中的所有配置后退出")
    parser.add_argument("--profile", help="指定要启动的配置名或 1-based 编号")
    parser.add_argument(
        "--capture-backend",
        choices=["auto", "x11", "kde-wayland"],
        default="auto",
        help="图像捕获/窗口检测后端",
    )
    parser.add_argument(
        "--window-title-regex",
        default="Diablo III",
        help="游戏窗口标题匹配正则，默认匹配 Diablo III",
    )
    parser.add_argument(
        "--window-class-regex",
        default="",
        help="可选：窗口类名匹配正则。通常不需要设置。",
    )
    parser.add_argument(
        "--any-window",
        action="store_true",
        help="忽略配置中的 d3only，允许对任意当前前台窗口发送按键",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    config_path = Path(args.config).expanduser().resolve()

    if args.gui:
        gui_script = Path(__file__).with_name("d3keyhelper_linux_gui.py")
        completed = subprocess.run([sys.executable, str(gui_script), str(config_path)])
        return completed.returncode

    if args.init_config:
        if config_path.exists():
            print(f"配置文件已存在，未覆盖：{config_path}")
            return 0
        create_default_config(config_path)
        print(f"已生成默认配置文件：{config_path}")
        return 0

    general, profiles = load_config(config_path)
    if args.list_profiles:
        for index, profile in enumerate(profiles, start=1):
            print(f"{index}. {profile.name}")
        return 0

    ensure_runtime_dependencies()

    start_profile_index = resolve_profile_index(profiles, args.profile, general.activated_profile)
    if args.any_window:
        general.d3only = False

    matcher = None
    capture_backend = "x11"
    if general.d3only:
        if args.capture_backend == "kde-wayland" or (
            args.capture_backend == "auto"
            and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
            and "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
            and Path("/usr/bin/spectacle").exists()
        ):
            matcher = KWinWindowMatcher(
                title_regex=args.window_title_regex or None,
                class_regex=args.window_class_regex or None,
            )
            capture_backend = "kde-wayland"
        else:
            matcher = ActiveWindowMatcher(
                title_regex=args.window_title_regex or None,
                class_regex=args.window_class_regex or None,
            )

    event_filter = SyntheticEventFilter()
    sender = InputSender(event_filter)
    app = MacroApp(general, profiles, start_profile_index, sender, matcher, capture_backend)
    app.start()

    def on_key_press(key_event) -> None:
        base = normalize_keyboard_event(key_event)
        if base is not None:
            app.on_key_press(base)

    def on_key_release(key_event) -> None:
        base = normalize_keyboard_event(key_event)
        if base is not None:
            app.on_key_release(base)

    def on_click(_x, _y, button_event, pressed) -> None:
        base = normalize_mouse_button(button_event)
        if base is None:
            return
        if pressed:
            app.on_key_press(base)
        else:
            app.on_key_release(base)

    def on_scroll(_x, _y, _dx, dy) -> None:
        if dy > 0:
            app.on_scroll("wheel_up")
        elif dy < 0:
            app.on_scroll("wheel_down")

    key_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release) if app.needs_keyboard_listener() else None
    mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll) if app.needs_mouse_listener() else None
    if key_listener is not None:
        key_listener.start()
    if mouse_listener is not None:
        mouse_listener.start()

    profile = profiles[start_profile_index]
    print(
        f"Linux 运行器已启动，当前配置：{profile.name}，启动热键：{format_hotkey(general.start_hotkey)}，捕获后端：{capture_backend}",
        flush=True,
    )
    print("按 Ctrl+C 退出运行器。", flush=True)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("正在退出 Linux 运行器...", flush=True)
    finally:
        app.shutdown()
        if key_listener is not None:
            key_listener.stop()
        if mouse_listener is not None:
            mouse_listener.stop()
    return 0


def format_hotkey(spec: HotkeySpec | None) -> str:
    if spec is None:
        return "未配置"
    parts = []
    if "ctrl" in spec.modifiers:
        parts.append("Ctrl")
    if "alt" in spec.modifiers:
        parts.append("Alt")
    if "shift" in spec.modifiers:
        parts.append("Shift")
    if "cmd" in spec.modifiers:
        parts.append("Super")
    parts.append(spec.base)
    return "+".join(parts)


def describe_enabled_helpers(helper: HelperConfig) -> list[str]:
    enabled: list[str] = []
    if helper.gamble_enabled:
        enabled.append("赌博")
    if helper.loot_enabled:
        enabled.append("拾取")
    if helper.salvage_enabled:
        enabled.append("分解")
    if helper.reforge_enabled:
        enabled.append("重铸")
    if helper.upgrade_enabled:
        enabled.append("升级")
    if helper.convert_enabled:
        enabled.append("转化")
    if helper.abandon_enabled:
        enabled.append("丢装")
    return enabled


def session_uses_wayland_keyboard_hotkeys(spec: HotkeySpec | None) -> bool:
    if spec is None:
        return False
    if os.environ.get("XDG_SESSION_TYPE", "").lower() != "wayland":
        return False
    return not spec.base.startswith("mouse:") and not spec.base.startswith("wheel_")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ConfigError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
