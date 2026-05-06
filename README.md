# D3Macro

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![Windows Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-windows.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-windows.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Language:** English | [简体中文](./README.zh-CN.md)

Cross-platform combat macro helper for **Diablo III**. Based on the original **[D3keyHelper](https://github.com/WeijieH/D3keyHelper)** by Weijie Huang, with platform-native input, window detection, screenshot handling, and a Qt GUI.

## Platforms

| Platform | Status |
|----------|--------|
| Linux – X11 / XWayland | ✅ Best supported |
| Linux – KDE Wayland | ✅ Via KDE/KWin backend |
| Windows | ✅ Native ctypes window detection |

## Screenshots

### Main Window

![Main Window](./mainwindow.png)

### Safezone Slot Map

![Safezone](./safezone.png)

## Quick Start

```bash
# 1. Install dependencies
uv venv --python 3.11 .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate default config
python d3keyhelper.py --init-config

# 3. Launch GUI
python d3keyhelper.py --gui
```

Config is saved to `~/.config/d3macro/d3oldsand.ini` on Linux, `%APPDATA%\d3macro\d3oldsand.ini` on Windows.

## Commands

```bash
python d3keyhelper.py --gui                          # launch GUI
python d3keyhelper.py                                # launch runner (terminal)
python d3keyhelper.py --init-config                  # create default config
python d3keyhelper.py --list-profiles                # list profiles
python d3keyhelper.py --profile 配置1                # start specific profile
python d3keyhelper.py --capture-backend kde-wayland  # force KDE Wayland backend
python d3keyhelper.py --any-window                   # skip D3-only window check
```

## Language

The GUI auto-detects system language. Manual switch: click `简 / EN / 繁` in the toolbar, or set `D3HELPER_LANG=zh|en|zh_TW` before launch.

## Build

### Linux AppImage

```bash
./build_appimage.sh
# Output: build/appimage/D3Macro-Linux-x86_64.AppImage
```

### Windows (on Windows)

```bat
build_windows.bat
:: Output: dist\D3Macro-Windows\D3Macro-Windows.exe
```

### Windows (via GitHub Actions)

Push a `v*` tag to trigger the Windows build workflow automatically. The zip is attached to the GitHub Release.

## Tests

```bash
python -m unittest discover -s tests
```

## Repository Layout

```text
.
├── d3keyhelper.py          # CLI entry point and runner
├── d3keyhelper_gui.py      # Qt GUI entry point
├── platform_compat.py      # all platform-specific code
├── config_io.py            # config parsing and I/O
├── capture.py              # screenshot backends
├── vision.py               # inventory detection
├── gui_widgets.py          # shared GUI widgets
├── gui_profile_page.py     # profile editor page
├── gui_i18n.py             # i18n helpers
├── enums.py                # shared enums
├── runner_events.py        # runner → GUI event bus
├── build_appimage.sh       # Linux AppImage build
├── build_windows.bat       # Windows PyInstaller build
├── tests/
├── packaging/
├── docs/
└── requirements.txt
```

## Credits

Based on [D3keyHelper](https://github.com/WeijieH/D3keyHelper) by Weijie Huang. MIT License.
