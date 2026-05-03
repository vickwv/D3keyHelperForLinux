# D3keyHelperForLinux

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Language:** English | [简体中文](./README.zh-CN.md)

`D3keyHelperForLinux` is a Linux port of the original **[D3keyHelper](https://github.com/WeijieH/D3keyHelper)** project for playing **Diablo III** with helper hotkeys and repeatable combat actions. It keeps the original `d3oldsand.ini`-style configuration compatible where possible, then adds Linux-native input, window detection, screenshot handling, and a Qt GUI.

This project is scoped to Diablo III key loops, town helpers, inventory workflows, and compatibility with the original configuration format. It is not a general automation framework or a game modification tool.

## Credits And License

This project is based on the original **D3keyHelper** by **Weijie Huang**:

<https://github.com/WeijieH/D3keyHelper>

Thanks to the original author for publishing the project, its configuration format, and the feature design that made this Linux port possible.

This repository continues to use the **MIT License**. If you redistribute or modify it, keep the original copyright notice and the license text in [LICENSE](./LICENSE).

## Current Status

Recommended environment:

1. **Linux desktop running X11**
2. **Wayland session with Diablo III running as an XWayland window**
3. **Steam + Proton + Battle.net + Diablo III**
4. **KDE Plasma**, especially when using the KDE-oriented screenshot path

Support level:

1. **X11 / XWayland:** best supported
2. **KDE Wayland + XWayland game window:** usable
3. **Pure native Wayland end-to-end control path:** still limited

Recent project highlights:

1. Qt GUI for profile editing, runner control, language switching, and runtime logs.
2. Refreshed Fluent-style layout, sidebar navigation, profile pages, and app icon.
3. Linux-native key sending, mouse actions, window matching, and screenshot backends.
4. Original-compatible `d3oldsand.ini` config loading and saving.
5. AppImage packaging and GitHub Actions builds.

## Screenshots

### Main Window

![Main Window](./mainwindow.png)

### Safezone Slot Map

![Safezone](./safezone.png)

## Quick Start

### 1. Install dependencies

```bash
uv python install 3.11
UV_CACHE_DIR=/tmp/uv-cache uv venv --python 3.11 .venv311
source .venv311/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

On Arch Linux, a typical base setup is:

```bash
sudo pacman -S python python-pip
```

### 2. Generate the default config

```bash
python d3keyhelper_linux.py --init-config
```

Default config path:

```bash
~/.config/d3helperforlinux/d3oldsand.ini
```

If `XDG_CONFIG_HOME` is set, the file is created under:

```bash
$XDG_CONFIG_HOME/d3helperforlinux/d3oldsand.ini
```

### 3. Launch the GUI

```bash
python d3keyhelper_linux.py --gui
```

The GUI is the recommended entry point. It edits general options, profile settings, skill strategies, helper settings, and runtime controls without requiring manual ini edits.

On first launch, the GUI detects the system language:

1. `en*` uses English
2. `zh_TW` / `zh_HK` / `zh-Hant` uses Traditional Chinese
3. `zh*` uses Simplified Chinese
4. Other languages fall back to Simplified Chinese

You can switch manually from the compact language selector in the top toolbar, shown as `简 / EN / 繁`. Manual selection is saved to `d3oldsand.ini` and takes priority on later launches.

For temporary override, set `D3HELPER_LANG` before launch:

```bash
# Simplified Chinese
D3HELPER_LANG=zh python d3keyhelper_linux.py --gui

# English
D3HELPER_LANG=en python d3keyhelper_linux.py --gui

# Traditional Chinese
D3HELPER_LANG=zh_TW python d3keyhelper_linux.py --gui
```

Traditional Chinese aliases such as `zh-hant`, `zh_HK`, `tw`, and `hk` are also accepted.

### 4. Or launch the runner directly

```bash
python d3keyhelper_linux.py
```

## Common Commands

```bash
# GUI
python d3keyhelper_linux.py --gui

# Create default config
python d3keyhelper_linux.py --init-config

# List profiles
python d3keyhelper_linux.py --list-profiles

# Launch a specific profile
python d3keyhelper_linux.py --profile 配置1

# Force KDE Wayland capture backend
python d3keyhelper_linux.py --capture-backend kde-wayland

# Ignore d3only for the current run
python d3keyhelper_linux.py --any-window
```

## Features

### Combat Macro Runner

The runner executes key loops and helper logic in game. Configuration is saved in the original-compatible `d3oldsand.ini` format.

1. Lazy toggle mode, hold-to-run mode, and one-shot mode.
2. Independent actions for six skill slots:
   - hold key
   - repeated tapping
   - keep buff active
   - trigger-on-key
3. Delay, randomized delay, priority, and repeat count.
4. Force stand still, force move, potion helper, and potion cooldown helper.
5. Quick pause, smart pause, and fast profile switching.
6. Auto-save config changes and restart the runner when a live change requires it.

### Graphical Interface

1. Structured forms for general options, profile settings, and skill strategies.
2. Left-side navigation for the general page and all profiles.
3. Top toolbar for active profile display, language switching, and runner start/stop controls.
4. Bottom status and log area for config path, runtime state, and recent messages.
5. Preserves original config fields where possible to avoid breaking existing setups.

### One-Button Helpers

These helpers target town workflows, inventory cleanup, and batch material operations:

1. Gamble helper
2. Loot helper
3. Salvage helper
4. Reforge helper
5. Upgrade rare items helper
6. Convert materials helper
7. Drop/store items helper

### Linux / Proton Compatibility

1. Diablo III window detection under Steam/Proton.
2. Handles blank or garbled window titles.
3. Falls back to process command line matching for `Diablo III64.exe`.
4. Supports the original safezone placeholder value `61,62,63`.
5. Preserves config compatibility keys such as `sendmode`, `enablesoundplay`, and `compactmode`.

## Steam / Proton Notes

If you launch Diablo III through **Steam -> Proton -> Battle.net -> Diablo III**, the most reliable setup is:

1. Run the game in **X11** or as an **XWayland** window.
2. Keep `d3only` enabled in the GUI.
3. Prefer helper hotkeys such as:
   - keyboard keys
   - mouse side buttons
   - mouse wheel
4. If the game window title is empty or broken, this project also matches the Proton process command line.

If you previously hit Chinese title detection issues, setting a consistent locale may help:

```bash
LANG=zh_CN.UTF-8 %command%
```

## Safezone Behavior

`safezone` defines inventory slots that helpers must not touch.

Expected format:

```ini
safezone=1,2,3,10
```

Special case:

```ini
safezone=61,62,63
```

Those three slot numbers do not actually exist. They were used by the original AHK project as a placeholder showing the expected format. This Linux port treats that value as:

**Not configured (legacy default)**

instead of reporting it as an invalid format.

## AppImage Packaging

### Build locally

Local AppImage builds use Python 3.11 to match GitHub Actions. The build script prefers `.venv311/bin/python`, then `python3.11`; it exits if another Python version is selected.

```bash
./build_appimage.sh
```

### Output

```bash
build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

### Run

```bash
chmod +x build/appimage/D3keyHelper-Linux-x86_64.AppImage
./build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

## GitHub Actions Builds

This repository includes a GitHub Actions workflow that:

1. runs the test suite
2. builds the AppImage automatically
3. uploads the AppImage as a workflow artifact
4. attaches the AppImage to GitHub Releases when a tag like `v1.0.6` is pushed

Release notes are stored under [.github/release-notes](./.github/release-notes).

## Tests

```bash
python -m unittest discover -s tests
```

## Repository Layout

```text
.
├── config_io.py
├── config_schema.py
├── capture.py
├── vision.py
├── enums.py
├── runner_events.py
├── d3keyhelper_linux.py
├── d3keyhelper_linux_gui.py
├── gui_i18n.py
├── gui_widgets.py
├── gui_profile_page.py
├── build_appimage.sh
├── requirements.txt
├── docs/
├── packaging/
├── tests/
├── LICENSE
├── README.md
└── README.zh-CN.md
```
