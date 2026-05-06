#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import queue
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

try:
    from .enums import MovingMethod, PotionMethod, QuickPauseAction, QuickPauseMode, QueueReason, ReforgeMethod, SalvageMethod, SkillAction, StartMode
    from .runner_events import emit_runner_event, emit_runner_log
except ImportError:
    from enums import MovingMethod, PotionMethod, QuickPauseAction, QuickPauseMode, QueueReason, ReforgeMethod, SalvageMethod, SkillAction, StartMode  # type: ignore[no-redef]
    from runner_events import emit_runner_event, emit_runner_log  # type: ignore[no-redef]

try:
    from .gui_i18n import tr, set_ui_language
except ImportError:
    from gui_i18n import tr, set_ui_language  # type: ignore[no-redef]

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


try:
    from .config_io import (  # noqa: F401
        DEFAULT_VERSION, CONFIG_DIR_NAME, CONFIG_FILE_NAME, DEFAULT_PROFILE_NAMES,
        START_METHOD_MOUSE, COMMON_METHOD_MOUSE, QUICK_PAUSE_MOUSE,
        HOTKEY_MODIFIER_PREFIX, HOTKEY_MODIFIER_NAMES, SPECIAL_KEY_ALIASES,
        MOUSE_EVENT_ALIASES, MOUSE_BUTTONS,
        SYNTHETIC_PHASE_PRESS, SYNTHETIC_PHASE_RELEASE,
        HotkeySpec, SendSpec, SkillConfig, QuickPauseConfig, ProfileConfig,
        HelperConfig, GeneralConfig, WindowInfo, ConfigError,
        normalize_token, parse_hotkey_expression, normalize_hotkey_base,
        parse_send_spec, parse_boolean, parse_int, parse_float, parse_safezone,
        method_to_hotkey, load_config, default_skill_hotkey, default_profile_dict,
        default_config_dir, default_config_path, create_default_config,
    )
    from .capture import (  # noqa: F401
        clamp, adjusted_rgb, arrays_equal, pixels_to_adjusted_rgb,
        pixels_region_to_rgb, parse_resolution, GameImage,
        X11GameCapture, SpectacleGameCapture,
    )
    from .vision import (  # noqa: F401
        get_skill_button_buff_pos, get_inventory_space_xy,
        get_kanai_cube_button_pos, get_salvage_icon_xy,
        is_dialog_box_on_screen, is_salvage_page_open,
        salvage_mode_is_armed, salvage_bulk_buttons_from_state,
        is_kanai_cube_open, is_gamble_open, is_inventory_open,
        is_stash_open, is_inventory_space_empty, scan_inventory_space,
    )
except ImportError:
    from config_io import (  # type: ignore[no-redef]  # noqa: F401
        DEFAULT_VERSION, CONFIG_DIR_NAME, CONFIG_FILE_NAME, DEFAULT_PROFILE_NAMES,
        START_METHOD_MOUSE, COMMON_METHOD_MOUSE, QUICK_PAUSE_MOUSE,
        HOTKEY_MODIFIER_PREFIX, HOTKEY_MODIFIER_NAMES, SPECIAL_KEY_ALIASES,
        MOUSE_EVENT_ALIASES, MOUSE_BUTTONS,
        SYNTHETIC_PHASE_PRESS, SYNTHETIC_PHASE_RELEASE,
        HotkeySpec, SendSpec, SkillConfig, QuickPauseConfig, ProfileConfig,
        HelperConfig, GeneralConfig, WindowInfo, ConfigError,
        normalize_token, parse_hotkey_expression, normalize_hotkey_base,
        parse_send_spec, parse_boolean, parse_int, parse_float, parse_safezone,
        method_to_hotkey, load_config, default_skill_hotkey, default_profile_dict,
        default_config_dir, default_config_path, create_default_config,
    )
    from capture import (  # type: ignore[no-redef]  # noqa: F401
        clamp, adjusted_rgb, arrays_equal, pixels_to_adjusted_rgb,
        pixels_region_to_rgb, parse_resolution, GameImage,
        X11GameCapture, SpectacleGameCapture,
    )
    from vision import (  # type: ignore[no-redef]  # noqa: F401
        get_skill_button_buff_pos, get_inventory_space_xy,
        get_kanai_cube_button_pos, get_salvage_icon_xy,
        is_dialog_box_on_screen, is_salvage_page_open,
        salvage_mode_is_armed, salvage_bulk_buttons_from_state,
        is_kanai_cube_open, is_gamble_open, is_inventory_open,
        is_stash_open, is_inventory_space_empty, scan_inventory_space,
    )

def read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    if sys.platform == "win32":
        try:
            import ctypes
            import ctypes.wintypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return ""
            buf = ctypes.create_unicode_buffer(32768)
            size = ctypes.wintypes.DWORD(32768)
            ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
            ctypes.windll.kernel32.CloseHandle(handle)
            return buf.value
        except Exception:
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
    if sys.platform == "win32":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
        return
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
            raise ConfigError("缺少 pynput，请先安装 requirements.txt 中的依赖。")
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
        self._use_proton_fallback = not class_regex and title_regex == "Diablo III"

    def _variant_number(self, value: str, default: float = 0.0) -> float:
        matches = re.findall(r"-?\d+(?:\.\d+)?", str(value))
        return float(matches[-1]) if matches else default

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
        pid = int(self._variant_number(str(pairs.get("pid", "0")).strip("'"), 0.0))
        return WindowInfo(
            window_id=0,
            title=title,
            wm_class=wm_class,
            x=int(self._variant_number(pairs.get("x", "0.0"))),
            y=int(self._variant_number(pairs.get("y", "0.0"))),
            width=int(self._variant_number(pairs.get("width", "0.0"))),
            height=int(self._variant_number(pairs.get("height", "0.0"))),
            pid=pid,
            commandline=read_process_commandline(pid),
        )

    def matches_active_window(self) -> bool:
        window = self.get_active_window()
        if window is None:
            return False
        title_matches = bool(self._title_pattern and self._title_pattern.search(window.title))
        class_matches = bool(self._class_pattern and self._class_pattern.search(window.wm_class))
        proton_matches = self._use_proton_fallback and looks_like_proton_diablo_window(window)
        if self._title_pattern and not title_matches:
            if not proton_matches:
                return False
        if self._class_pattern and not class_matches:
            return False
        return bool(title_matches or class_matches or proton_matches)


class WindowsWindowMatcher:
    """Active-window matcher for Windows using ctypes (no extra dependencies)."""

    def __init__(self, title_regex: str | None, class_regex: str | None) -> None:
        self._title_pattern = re.compile(title_regex, re.IGNORECASE) if title_regex else None
        self._class_pattern = re.compile(class_regex, re.IGNORECASE) if class_regex else None

    def get_active_window(self) -> WindowInfo | None:
        import ctypes
        import ctypes.wintypes

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            title_buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, title_buf, length + 1)
            class_buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, class_buf, 256)
            pid = ctypes.wintypes.DWORD(0)
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid_val = int(pid.value)
            rect = RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            pt = POINT(0, 0)
            ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
            return WindowInfo(
                window_id=int(hwnd),
                title=title_buf.value,
                wm_class=class_buf.value,
                x=int(pt.x),
                y=int(pt.y),
                width=int(rect.right - rect.left),
                height=int(rect.bottom - rect.top),
                pid=pid_val,
                commandline=read_process_commandline(pid_val),
            )
        except Exception:
            return None

    def matches_active_window(self) -> bool:
        window = self.get_active_window()
        return window is not None and self.matches_window(window)

    def matches_window(self, window: WindowInfo) -> bool:
        title_ok = bool(self._title_pattern and self._title_pattern.search(window.title))
        class_ok = bool(self._class_pattern and self._class_pattern.search(window.wm_class))
        return bool(title_ok or class_ok)


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
        if matcher is not None and np is not None and capture_backend == "kde-wayland" and Image is not None:
            self._capture = SpectacleGameCapture(matcher, general)
        elif matcher is not None and mss is not None and np is not None:
            self._capture = X11GameCapture(matcher, general)
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
                print(tr("当前配置使用滚轮作为启动键，但 Linux 首版不支持“仅按下时”滚轮保持模式。", 'Current profile uses scroll wheel as start key, but "hold while pressed" scroll wheel mode is not supported on Linux.'), flush=True)
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
            print(tr(f"未检测到目标游戏窗口，当前不会启动宏。前台窗口：{format_window_debug(active_window)}", f"Game window not found; macro will not start. Active window: {format_window_debug(active_window)}"), flush=True)
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
                print(tr(f"[{profile.name}] 检测到按键触发策略，但触发键无效，已跳过。", f"[{profile.name}] Key-trigger skill has no trigger key; skipped."), flush=True)

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

        emit_runner_event("macro_started", profile.name)
        emit_runner_log(tr(f"已启动 Linux 战斗宏：{profile.name}", f"Combat macro started: {profile.name}"))

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
            emit_runner_event("macro_stopped", reason)
            emit_runner_log(tr(f"已停止战斗宏：{reason}", f"Combat macro stopped: {reason}"))
        else:
            emit_runner_event("macro_stopped")
            emit_runner_log(tr("已停止战斗宏", "Combat macro stopped"))

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
            emit_runner_event("macro_paused")
            emit_runner_log(tr("战斗宏已暂停", "Combat macro paused"))
        else:
            for send_spec in held_keys:
                self.sender.press(send_spec)
            emit_runner_event("macro_resumed")
            emit_runner_log(tr("战斗宏已恢复", "Combat macro resumed"))

    def send_once_actions(self) -> None:
        profile = self.current_profile
        for skill in profile.skills:
            if skill.action == SkillAction.HOLD and skill.hotkey is not None:
                self.sender.tap(skill.hotkey)
        print(tr(f"已执行一次性按键：{profile.name}", f"One-shot actions sent: {profile.name}"), flush=True)

    def switch_profile(self, index: int) -> None:
        with self._lock:
            if index == self.current_profile_index:
                return
            was_running = self._running
            was_paused = self._paused
        self.stop_macro(reason=None)
        self.current_profile_index = index
        profile = self.current_profile
        emit_runner_event("profile_switched", profile.name)
        emit_runner_log(tr(f"已切换配置：{profile.name}", f"Profile switched: {profile.name}"))
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
                    # Re-check state while holding the lock so we never put
                    # items into the queue after stop_macro() has drained it.
                    with self._lock:
                        if not self._running or self._paused:
                            return
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
            with self._lock:
                if not self._running or self._paused:
                    return
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
                print(tr("已请求停止当前助手流程。", "Stop requested for current helper."), flush=True)
                return
            if self._running:
                print(tr("战斗宏运行中，当前不会启动助手。", "Combat macro is running; helper will not start."), flush=True)
                return
            self._helper_running = True
            self._helper_break = False
        print(tr("已收到助手热键，正在识别当前界面...", "Helper hotkey received; detecting current screen..."), flush=True)
        self._helper_thread = threading.Thread(target=self._run_helper, daemon=True)
        self._helper_thread.start()

    def _run_helper(self) -> None:
        try:
            capture = self._capture_game_image()
            if capture is None:
                print(tr("助手未执行：无法截取当前游戏画面。", "Helper skipped: unable to capture game screen."), flush=True)
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
                print(tr(f"助手已启动：识别到赌博界面，连续右键 {self.general.helper.gamble_times} 次。", f"Helper started: Gambling detected; right-clicking {self.general.helper.gamble_times} times."), flush=True)
                self._gamble_helper()
                return

            if self.general.helper.salvage_enabled:
                salvage_state = is_salvage_page_open(image, width, height)
                if salvage_state[0] == 2:
                    if self.general.helper.salvage_method == SalvageMethod.QUICK and mouse_position == 1:
                        print(tr("助手已启动：识别到分解页，执行快速分解。", "Helper started: Salvage page detected; running fast salvage."), flush=True)
                        self._quick_salvage_helper(width, height)
                        return
                    if not self._prepare_salvage_helper_mode(width, height, salvage_state):
                        if not self._helper_should_break():
                            print(tr("助手未执行：无法进入可分解状态。", "Helper skipped: unable to enter salvageable state."), flush=True)
                        return
                    print(tr("助手已启动：识别到分解页，执行一键/智能分解。", "Helper started: Salvage page detected; running one-click/smart salvage."), flush=True)
                    self._one_button_salvage_helper(width, height, mouse_x, mouse_y)
                    return
                if salvage_state[0] == 1:
                    print(tr("助手未执行：识别到分解界面，但当前标签页不是可执行的装备分解页。", "Helper skipped: Salvage UI detected, but current tab is not the equipment salvage page."), flush=True)
                    return

            if self.general.helper.reforge_enabled or self.general.helper.upgrade_enabled or self.general.helper.convert_enabled:
                kanai_state = is_kanai_cube_open(image, width, height, window.title)
                if kanai_state == 2 and self.general.helper.reforge_enabled and mouse_position == 1:
                    print(tr("助手已启动：识别到卡奈魔盒重铸页，开始重铸。", "Helper started: Kanai's Cube reforge page detected; starting reforge."), flush=True)
                    self._one_button_reforge_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 3 and self.general.helper.upgrade_enabled:
                    print(tr("助手已启动：识别到卡奈魔盒升级页，开始升级黄色装备。", "Helper started: Kanai's Cube upgrade page detected; upgrading rare items."), flush=True)
                    self._one_button_upgrade_convert_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 4 and self.general.helper.convert_enabled:
                    print(tr("助手已启动：识别到卡奈魔盒转化页，开始转化材料。", "Helper started: Kanai's Cube convert page detected; converting materials."), flush=True)
                    self._one_button_upgrade_convert_helper(width, height, mouse_x, mouse_y)
                    return
                if kanai_state == 1:
                    print(tr("助手未执行：识别到卡奈魔盒，但当前不是重铸/升级/转化页。", "Helper skipped: Kanai's Cube detected, but current tab is not reforge/upgrade/convert."), flush=True)
                    return

            if self.general.helper.abandon_enabled and mouse_position > 0 and is_inventory_open(image, width, height):
                print(tr("助手已启动：识别到背包界面，执行丢装助手。", "Helper started: Inventory detected; running drop/store helper."), flush=True)
                self._one_button_abandon_helper(width, height, mouse_x, mouse_y, mouse_position)
                return

            if self.general.helper.loot_enabled:
                print(tr("助手已启动：执行拾取助手。", "Helper started: Running loot helper."), flush=True)
                self._loot_helper(width, height)
                return
            print(tr(f"助手未执行：未识别到已启用的助手场景。前台窗口：{format_window_debug(window)}", f"Helper skipped: No enabled helper scenario detected. Active window: {format_window_debug(window)}"), flush=True)
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
                    self.stop_macro(reason=tr("检测到窗口焦点已离开游戏", "Game window lost focus"))
                if self._shutdown_event.wait(0.3):
                    break

        self._focus_thread = threading.Thread(target=monitor, daemon=True)
        self._focus_thread.start()

    def _print_profile_notes(self, profile: ProfileConfig) -> None:
        notes: list[str] = []
        if self._capture is None and any(skill.action == SkillAction.KEEP_BUFF for skill in profile.skills):
            notes.append(tr("保持 Buff 需要图像捕获依赖", "Keep Buff requires image capture dependencies"))
        if self._capture is None and profile.potion_method == PotionMethod.KEEP_CD:
            notes.append(tr("保持药水 CD 需要图像捕获依赖", "Keep Potion CD requires image capture dependencies"))
        if notes:
            print(tr(f"[{profile.name}] 当前配置提示：{'、'.join(notes)}", f"[{profile.name}] Profile notes: {', '.join(notes)}"), flush=True)

    def _print_helper_notes(self) -> None:
        enabled_helpers = describe_enabled_helpers(self.general.helper)
        helper_summary = tr("、", ", ").join(enabled_helpers) if enabled_helpers else tr("无已启用助手", "No helpers enabled")
        print(
            tr(f"助手热键：{format_hotkey(self.general.helper.hotkey)}；已启用：{helper_summary}", f"Helper hotkey: {format_hotkey(self.general.helper.hotkey)}; Enabled: {helper_summary}"),
            flush=True,
        )
        if session_uses_wayland_keyboard_hotkeys(self.general.helper.hotkey):
            print(
                tr("当前为 Wayland 会话，键盘全局热键可能不稳定；若 F5 没反应，优先改用鼠标侧键/滚轮，或改用 X11/XWayland。", "Wayland session detected; global keyboard hotkeys may be unreliable. If the hotkey doesn't respond, consider using a mouse side button/scroll wheel, or switch to X11/XWayland."),
                flush=True,
            )


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


def ensure_runtime_dependencies(capture_backend: str) -> None:
    if keyboard is None or mouse is None:
        raise ConfigError("未安装 pynput，请先执行：pip install -r requirements.txt")
    if capture_backend == "none":
        return
    if np is None:
        raise ConfigError("未安装 numpy，请先执行：pip install -r requirements.txt")
    if capture_backend == "x11" and (xdisplay is None or X is None):
        raise ConfigError("未安装 python-xlib，请先执行：pip install -r requirements.txt")
    if capture_backend in ("x11", "windows") and mss is None:
        raise ConfigError("未安装 mss，请先执行：pip install -r requirements.txt")
    if Image is None:
        raise ConfigError("未安装 Pillow，请先执行：pip install -r requirements.txt")
    if capture_backend == "kde-wayland":
        if not shutil.which("gdbus"):
            raise ConfigError("缺少 gdbus，无法通过 KDE/KWin 获取活动窗口。")
        if not shutil.which("spectacle"):
            raise ConfigError("缺少 spectacle，无法使用 KDE Wayland 截图后端。")


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
    parser = argparse.ArgumentParser(description="D3keyHelper combat macro runner (Windows/Linux).")
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help=f"配置文件路径，默认 {default_config_path()}",
    )
    parser.add_argument("--gui", action="store_true", help="启动图形界面配置器")
    parser.add_argument("--init-config", action="store_true", help="生成一份默认配置文件后退出")
    parser.add_argument("--list-profiles", action="store_true", help="列出配置文件中的所有配置后退出")
    parser.add_argument("--profile", help="指定要启动的配置名或 1-based 编号")
    parser.add_argument(
        "--capture-backend",
        choices=["auto", "x11", "kde-wayland", "windows"],
        default="auto",
        help="图像捕获/窗口检测后端（auto 自动选择）",
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
    parser.add_argument("--lang", default=None, help="界面语言 (zh/en/zh_TW)")
    return parser


def _set_windows_dpi_awareness() -> None:
    """Enable per-monitor DPI awareness so pixel coordinates and mss captures are consistent."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()
    if args.lang:
        set_ui_language(args.lang)

    if sys.platform == "win32":
        _set_windows_dpi_awareness()

    config_path = Path(args.config).expanduser().resolve()

    if args.gui:
        gui_script = Path(__file__).with_name("d3keyhelper_linux_gui.py")
        completed = subprocess.run([sys.executable, str(gui_script), str(config_path)])
        return completed.returncode

    if args.init_config:
        if config_path.exists():
            print(tr(f"配置文件已存在，未覆盖：{config_path}", f"Config file already exists, skipped: {config_path}"))
            return 0
        create_default_config(config_path)
        print(tr(f"已生成默认配置文件：{config_path}", f"Default config created: {config_path}"))
        return 0

    general, profiles = load_config(config_path)
    if args.list_profiles:
        for index, profile in enumerate(profiles, start=1):
            print(f"{index}. {profile.name}")
        return 0

    start_profile_index = resolve_profile_index(profiles, args.profile, general.activated_profile)
    if args.any_window:
        general.d3only = False

    matcher = None
    if sys.platform == "win32":
        capture_backend = "windows"
        if general.d3only:
            matcher = WindowsWindowMatcher(
                title_regex=args.window_title_regex or None,
                class_regex=args.window_class_regex or None,
            )
    else:
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
    ensure_runtime_dependencies(capture_backend if general.d3only else "none")

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

    platform_label = tr("Windows 运行器", "Windows runner") if sys.platform == "win32" else tr("Linux 运行器", "Linux runner")
    profile = profiles[start_profile_index]
    print(
        tr(f"{platform_label}已启动，当前配置：{profile.name}，启动热键：{format_hotkey(general.start_hotkey)}，捕获后端：{capture_backend}", f"{platform_label} started. Profile: {profile.name}, start hotkey: {format_hotkey(general.start_hotkey)}, capture backend: {capture_backend}"),
        flush=True,
    )
    print(tr("按 Ctrl+C 退出运行器。", "Press Ctrl+C to stop the runner."), flush=True)

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print(tr(f"正在退出{platform_label}...", f"Stopping {platform_label}..."), flush=True)
    finally:
        app.shutdown()
        if key_listener is not None:
            key_listener.stop()
        if mouse_listener is not None:
            mouse_listener.stop()
    return 0


def format_hotkey(spec: HotkeySpec | None) -> str:
    if spec is None:
        return tr("未配置", "Not configured")
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
        enabled.append(tr("赌博", "Gamble"))
    if helper.loot_enabled:
        enabled.append(tr("拾取", "Loot"))
    if helper.salvage_enabled:
        enabled.append(tr("分解", "Salvage"))
    if helper.reforge_enabled:
        enabled.append(tr("重铸", "Reforge"))
    if helper.upgrade_enabled:
        enabled.append(tr("升级", "Upgrade"))
    if helper.convert_enabled:
        enabled.append(tr("转化", "Convert"))
    if helper.abandon_enabled:
        enabled.append(tr("丢装", "Drop/store"))
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
        print(tr(f"错误：{exc}", f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)
