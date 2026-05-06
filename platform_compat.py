"""Platform-specific helpers: window detection, process info, sound.

All platform branching lives here.  d3keyhelper.py imports only the
public symbols below and never checks ``sys.platform`` directly.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from Xlib import X, display as xdisplay
except ImportError:
    X = None
    xdisplay = None

try:
    from .config_io import WindowInfo, ConfigError
except ImportError:
    from config_io import WindowInfo, ConfigError  # type: ignore[no-redef]

try:
    from .gui_i18n import tr
except ImportError:
    from gui_i18n import tr  # type: ignore[no-redef]


# ── process helpers ────────────────────────────────────────────────────────

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


# ── sound ─────────────────────────────────────────────────────────────────

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


# ── DPI awareness ─────────────────────────────────────────────────────────

def set_dpi_awareness() -> None:
    """Enable per-monitor DPI awareness (Windows only)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ── window matchers ───────────────────────────────────────────────────────

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


# ── platform factory functions ────────────────────────────────────────────

def detect_platform_backend(args_capture_backend: str) -> str:
    """Return the appropriate capture backend for the current platform."""
    if sys.platform == "win32":
        return "windows"
    if args_capture_backend == "kde-wayland":
        return "kde-wayland"
    if (
        args_capture_backend == "auto"
        and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        and "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        and Path("/usr/bin/spectacle").exists()
    ):
        return "kde-wayland"
    return "x11"


def make_window_matcher(title_regex: str | None, class_regex: str | None, capture_backend: str):
    """Instantiate the correct window matcher for the current platform."""
    if sys.platform == "win32":
        return WindowsWindowMatcher(title_regex=title_regex, class_regex=class_regex)
    if capture_backend == "kde-wayland":
        return KWinWindowMatcher(title_regex=title_regex, class_regex=class_regex)
    return ActiveWindowMatcher(title_regex=title_regex, class_regex=class_regex)


def platform_runner_label() -> str:
    return tr("Windows 运行器", "Windows runner") if sys.platform == "win32" else tr("Linux 运行器", "Linux runner")
