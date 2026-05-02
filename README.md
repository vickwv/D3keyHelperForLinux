# D3keyHelperForLinux

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**Language:** English | [简体中文](./README.zh-CN.md)

`D3keyHelperForLinux` is a key helper for playing **Diablo III on Linux**. It ports the combat macro runner and one-button helper workflows from the original **D3keyHelper** project, then adds a new Qt GUI for editing profiles, starting and stopping the runner, switching active configs, and watching runtime status.

The project focuses on three practical goals:

1. Keep existing D3keyHelper-style macro configs usable under **Steam + Proton + Battle.net + Diablo III**.
2. Handle key sending, mouse actions, window detection, and inventory screenshots through Linux-native code.
3. Ship as an AppImage so users do not have to manage a Python environment manually.

It is not a general automation framework or a game modification tool. It is scoped around Diablo III key loops, helper actions, and compatibility with the original `d3oldsand.ini` format.

## v1.0.1 highlights

`v1.0.1` is primarily a major UI refresh:

1. Redesigned the main window layout to reduce dense, stacked forms.
2. Added left-side navigation, a clearer runtime status area, and a cleaner log panel.
3. Improved profile pages, skill tables, toolbar behavior, and active profile display.
4. Reworked the app icon around a dark Diablo-style `D3` mark.
5. Trimmed AppImage packaging so unrelated Qt modules are no longer bundled.

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

## Feature Overview

### Combat macro runner

The runner executes key loops and helper logic in game. Configuration is still saved in the original-compatible `d3oldsand.ini` format.

1. Supports lazy toggle mode, hold-to-run mode, and one-shot mode.
2. Supports independent actions for six skill slots:
   - hold key
   - repeated tapping
   - keep buff active
   - trigger-on-key
3. Supports delay, randomized delay, priority, and repeat count.
4. Supports force stand still, force move, potion helper, and potion cooldown helper.
5. Supports quick pause, smart pause, and fast profile switching.
6. Auto-saves config changes and restarts the runner when a live change requires it.

### Graphical interface

The GUI is the main entry point in the current version and replaces most manual ini editing.

1. Edits general options, profile settings, and skill strategies through structured forms.
2. Shows the general page and all profiles in left-side navigation.
3. Shows the active profile in the top toolbar and provides runner start/stop controls.
4. Shows config path, runtime state, and recent messages in the bottom status/log area.
5. Preserves original config fields where possible to avoid breaking existing setups.

### One-button helpers

These helpers target town workflows, inventory cleanup, and batch material operations:

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

The default config path is:

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

On first launch, the GUI detects the current system language:

1. `en*` uses English
2. `zh_TW` / `zh_HK` / `zh-Hant` uses Traditional Chinese
3. `zh*` uses Simplified Chinese
4. Other languages fall back to Simplified Chinese

You can also switch manually from the compact language selector in the top toolbar, shown as `简 / EN / 繁`. Manual selection is saved to `d3oldsand.ini` and takes priority on later launches.

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
