# D3Macro

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![Windows Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-windows.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-windows.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**语言:** [English](./README.md) | 简体中文

跨平台暗黑破坏神 III 战斗宏助手。基于原版 **[D3keyHelper](https://github.com/WeijieH/D3keyHelper)**（作者：Weijie Huang），新增跨平台按键发送、窗口识别、截图处理和 Qt 图形界面。

## 支持平台

| 平台 | 状态 |
|------|------|
| Linux – X11 / XWayland | ✅ 支持最完整 |
| Linux – KDE Wayland | ✅ 通过 KDE/KWin 后端 |
| Windows | ✅ 原生 ctypes 窗口识别 |

> Windows 支持从 v2.0.0 起加入，v1.x 仅支持 Linux。

## 截图

### 主窗口

![Main Window](./mainwindow.png)

### 安全格示意

![Safezone](./safezone.png)

## 快速开始

```bash
# 1. 安装依赖
uv venv --python 3.11 .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 生成默认配置
python d3keyhelper.py --init-config

# 3. 启动 GUI
python d3keyhelper.py --gui
```

Linux 配置路径：`~/.config/d3macro/d3oldsand.ini`  
Windows 配置路径：`%APPDATA%\d3macro\d3oldsand.ini`

## 常用命令

```bash
python d3keyhelper.py --gui                          # 启动 GUI
python d3keyhelper.py                                # 直接启动运行器（终端）
python d3keyhelper.py --init-config                  # 生成默认配置
python d3keyhelper.py --list-profiles                # 列出配置
python d3keyhelper.py --profile 配置1                # 启动指定配置
python d3keyhelper.py --capture-backend kde-wayland  # 强制使用 KDE Wayland 后端
python d3keyhelper.py --any-window                   # 跳过 D3 窗口检测
```

## 界面语言

GUI 自动检测系统语言。点击顶部工具栏 `简 / EN / 繁` 手动切换，或启动前设置 `D3HELPER_LANG=zh|en|zh_TW`。

## 构建

### Linux AppImage

```bash
./build_appimage.sh
# 输出：build/appimage/D3Macro-Linux-x86_64.AppImage
```

### Windows（在 Windows 上）

```bat
build_windows.bat
:: 输出：dist\D3Macro-Windows.exe
```

### Windows（通过 GitHub Actions）

推送 `v*` 标签即可自动触发 Windows 构建工作流，构建产物以 zip 格式挂载到 GitHub Release。

## 测试

```bash
python -m unittest discover -s tests
```

## 目录结构

```text
.
├── d3keyhelper.py          # CLI 入口与运行器
├── d3keyhelper_gui.py      # Qt GUI 入口
├── platform_compat.py      # 平台相关代码
├── config_io.py            # 配置解析与读写
├── capture.py              # 截图后端
├── vision.py               # 背包识别
├── gui_widgets.py          # 共用 GUI 组件
├── gui_profile_page.py     # 配置页
├── gui_i18n.py             # 多语言
├── enums.py                # 枚举定义
├── runner_events.py        # 运行器事件总线
├── build_appimage.sh       # Linux AppImage 构建脚本
├── build_windows.bat       # Windows PyInstaller 构建脚本
├── tests/
├── packaging/
├── docs/
└── requirements.txt
```

## 致谢

基于 Weijie Huang 的 [D3keyHelper](https://github.com/WeijieH/D3keyHelper)，MIT License。
