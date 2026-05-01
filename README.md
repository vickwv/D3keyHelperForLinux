# D3keyHelperForLinux

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Language:** English | [简体中文](./README.zh-CN.md)

`D3keyHelperForLinux` is a native Linux port of the original **D3keyHelper** project, focused on **Diablo III running through Steam + Proton**. It provides combat macros, helper automation, a Qt GUI editor, AppImage packaging, and compatibility with the original `d3oldsand.ini` configuration format.

## Credits and license

This project is based on the original **D3keyHelper** by **Weijie Huang**. Thanks to the original author for publishing the project, its configuration format, and the feature design that made this port possible.

This repository continues to use the **MIT License**. If you redistribute or modify it, keep the original copyright notice and the license text in `LICENSE`.

## Current target environment

Recommended environment, in order:

1. **Linux desktop running X11**
2. **Wayland session with Diablo III running as an XWayland window**
3. **Steam + Proton + Battle.net + Diablo III**
4. **KDE Plasma** is supported especially well because the project includes a KDE-oriented screenshot path

Current completeness:

1. **X11 / XWayland:** best supported
2. **KDE Wayland + XWayland game window:** usable
3. **Pure native Wayland end-to-end control path:** still limited

## Features

### Combat macro features

1. GUI editor for `d3oldsand.ini`
2. Lazy toggle mode / hold-to-run mode / one-shot mode
3. Skill actions:
   - hold key
   - repeated tapping
   - keep buff active
   - trigger-on-key
4. Delay, randomized delay, priority, repeat count
5. Single-thread skill queue
6. Force stand still, force move, potion helper, potion cooldown helper
7. Quick pause and smart pause
8. Fast profile switching
9. Auto-save config changes and auto-restart runner when needed

### One-button helper features

1. Gamble helper
2. Loot helper
3. Salvage helper
4. Reforge helper
5. Upgrade rare items helper
6. Convert materials helper
7. Drop/store items helper

### Linux / Proton compatibility

1. Diablo III window detection under Steam/Proton
2. Handles blank or garbled window titles
3. Falls back to process command line matching for `Diablo III64.exe`
4. Supports the original safezone placeholder value `61,62,63`
5. Preserves config compatibility keys such as `sendmode`, `enablesoundplay`, and `compactmode`

## Screenshots

### Main window

![Main Window](./mainwindow.png)

### Compact window

![Compact Window](./mainwindow_compact.png)

### Settings illustration

![Settings](./settings.png)

### Safezone slot map

![Safezone](./safezone.png)

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Arch Linux, a typical base setup is:

```bash
sudo pacman -S python python-pip
```

### 2. Generate the default config

```bash
python d3keyhelper_linux.py --init-config
```

### 3. Launch the GUI

```bash
python d3keyhelper_linux.py --gui
```

### 4. Or launch the runner directly

```bash
python d3keyhelper_linux.py
```

## Common commands

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

## Steam / Proton notes

If you launch Diablo III through **Steam -> Proton -> Battle.net -> Diablo III**, the most reliable setup is:

1. Run the game in **X11** or as an **XWayland** window
2. Keep `d3only` enabled in the GUI
3. Prefer helper hotkeys such as:
   - keyboard keys
   - mouse side buttons
   - mouse wheel
4. If the game window title is empty or broken, this project also matches the Proton process command line

If you previously hit Chinese title detection issues, setting a consistent locale may help:

```bash
LANG=zh_CN.UTF-8 %command%
```

## Safezone behavior

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

## AppImage packaging

### Build locally

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

## GitHub Actions AppImage builds

This repository includes a GitHub Actions workflow that:

1. runs the test suite
2. builds the AppImage automatically
3. uploads the AppImage as a workflow artifact
4. attaches the AppImage to GitHub Releases when a tag like `v1.0.0` is pushed

## Tests

```bash
python -m unittest discover -s tests
```

## Repository layout

```text
.
├── d3keyhelper_linux.py
├── d3keyhelper_linux_gui.py
├── build_appimage.sh
├── requirements.txt
├── packaging/
├── tests/
├── LICENSE
├── README.md
└── README.zh-CN.md
```
