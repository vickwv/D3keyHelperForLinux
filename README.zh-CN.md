# D3keyHelperForLinux

[![AppImage Build](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/vickwv/D3keyHelperForLinux/actions/workflows/build-appimage.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**语言:** [English](./README.md) | 简体中文

`D3keyHelperForLinux` 是给 **Linux 下玩 Diablo III** 的玩家使用的按键助手。它把原版 **D3keyHelper** 的战斗宏和一键整理功能移植到 Linux，并提供一个新的 Qt 图形界面，用来编辑配置、启动/停止运行器、切换配置和查看运行状态。

这个项目主要解决三个问题：

1. 在 **Steam + Proton + Battle.net + Diablo III** 环境下继续使用 D3keyHelper 的宏配置。
2. 用 Linux 原生方式处理按键发送、鼠标操作、窗口识别和背包区域截图。
3. 用 AppImage 发布，尽量减少手动配置 Python 环境的成本。

它不是通用自动化工具，也不是游戏修改器；它只围绕 Diablo III 的按键循环、辅助操作和原版 `d3oldsand.ini` 配置兼容来设计。

## v1.0.1 重点

`v1.0.1` 是一次以界面为主的大改版：

1. 重新设计主界面布局，减少拥挤的表单堆叠。
2. 增加左侧导航、运行状态区域和更清晰的日志面板。
3. 优化配置页、技能表格、工具栏和活动配置显示。
4. 重做应用图标，改为暗黑风格的 `D3` 主视觉。
5. 优化 AppImage 打包，减少不必要的 Qt 模块依赖。

## 致谢与许可证

本项目基于原作者 **Weijie Huang** 的 **D3keyHelper** 移植而来。感谢原作者公开原始项目、配置格式和功能设计。

本项目继续遵循 **MIT License**。发布、分发或二次修改时，请保留原作者版权声明与 `LICENSE` 中的许可证文本。

## 适用环境

当前推荐环境，按优先级排序：

1. **X11 Linux 桌面**
2. **Wayland 会话下，以 XWayland 窗口运行 Diablo III**
3. **Steam + Proton + Battle.net + Diablo III**
4. **KDE Plasma** 兼容性相对更好，因为项目内置了 KDE 侧截图路径

当前完整度：

1. **X11 / XWayland：最完整、最稳定**
2. **KDE Wayland + XWayland 游戏窗口：可用**
3. **纯 Wayland 原生全链路：仍有限制**

## 功能概览

### 战斗宏运行器

运行器负责在游戏中执行按键循环和辅助逻辑。配置仍然保存为原版兼容的 `d3oldsand.ini`。

1. 支持懒人模式、按住运行、单次触发。
2. 支持 6 个技能位的独立策略：
   - 按住不放
   - 连点
   - 保持 Buff
   - 按键触发
3. 支持延迟、随机延迟、优先级、重复发送。
4. 支持强制站立、强制移动、药水辅助、保持药水 CD。
5. 支持快速暂停、智能暂停和快速切换配置。
6. 配置变更后自动保存，运行中修改关键配置时自动重启运行器。

### 图形界面

GUI 是当前版本的主要入口，用来替代手动编辑 ini。

1. 以分区表单编辑通用选项、配置页和技能策略。
2. 左侧导航显示通用页和所有配置页。
3. 顶部工具栏显示当前活动配置，并提供启动/停止运行器入口。
4. 底部日志和状态栏显示配置路径、运行状态和最近操作。
5. 保留原版配置字段，尽量避免破坏已有配置。

### 一键助手

这些功能主要面向城镇整理、背包处理和批量材料操作：

1. 赌博助手
2. 拾取助手
3. 分解助手
4. 重铸助手
5. 升级稀有物品助手
6. 转化材料助手
7. 丢装 / 存仓助手

### Linux / Proton 兼容

1. 支持 Steam/Proton 下的 Diablo III 窗口识别
2. 兼容空标题、乱码标题
3. 可通过进程命令行识别 `Diablo III64.exe`
4. 兼容原版 safezone 默认占位值 `61,62,63`
5. 保留原版配置兼容项：`sendmode`、`enablesoundplay`、`compactmode`

## 界面截图

### 主界面

![Main Window](./mainwindow.png)

### 配置说明图

![Settings](./settings.png)

### Safezone 编号示意

![Safezone](./safezone.png)

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果你是 Arch Linux，常见基础安装方式：

```bash
sudo pacman -S python python-pip
```

### 2. 生成默认配置

```bash
python d3keyhelper_linux.py --init-config
```

默认配置文件路径现在是：

```bash
~/.config/d3helperforlinux/d3oldsand.ini
```

如果设置了 `XDG_CONFIG_HOME`，则会创建到：

```bash
$XDG_CONFIG_HOME/d3helperforlinux/d3oldsand.ini
```

### 3. 启动 GUI

```bash
python d3keyhelper_linux.py --gui
```

GUI 里的主标签页现在默认显示为 **通用**。如果你想切换主要界面外壳为英文，可以在启动前设置 `D3HELPER_LANG=en`。

### 4. 或直接启动运行器

```bash
python d3keyhelper_linux.py
```

## 常用命令

```bash
# 图形界面
python d3keyhelper_linux.py --gui

# 创建默认配置
python d3keyhelper_linux.py --init-config

# 列出配置
python d3keyhelper_linux.py --list-profiles

# 按配置名启动
python d3keyhelper_linux.py --profile 配置1

# 强制使用 KDE Wayland 截图后端
python d3keyhelper_linux.py --capture-backend kde-wayland

# 临时忽略 d3only，只对当前前台窗口发按键
python d3keyhelper_linux.py --any-window
```

## Steam / Proton 使用建议

如果你是通过 **Steam -> Proton -> 战网 -> Diablo III** 启动游戏，最推荐的方式是：

1. 尽量让游戏跑在 **X11** 或 **XWayland** 窗口里
2. 在 GUI 里保持 `d3only` 开启
3. 助手热键优先使用：
   - 键盘按键
   - 鼠标侧键
   - 滚轮
4. 如果游戏窗口标题为空或乱码，项目也会回退到 Proton 进程命令行识别

如果你曾经遇到中文标题识别问题，可以尝试为游戏统一 locale：

```bash
LANG=zh_CN.UTF-8 %command%
```

## Safezone 说明

`safezone` 用来定义一键助手不会处理的背包格子。

常规格式：

```ini
safezone=1,2,3,10
```

特殊情况：

```ini
safezone=61,62,63
```

这三个编号实际上并不存在，只是原版 AHK 用来提示 safezone 配置格式的历史占位值。当前 Linux 版会把它识别成：

**未设置（沿用原版默认值）**

而不是把它报成格式错误。

## AppImage 打包

### 本地构建

```bash
./build_appimage.sh
```

### 产物

```bash
build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

### 运行

```bash
chmod +x build/appimage/D3keyHelper-Linux-x86_64.AppImage
./build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

## GitHub Actions 自动构建

仓库自带 GitHub Actions 工作流，会自动：

1. 运行测试
2. 构建 AppImage
3. 上传 AppImage 作为 workflow artifact
4. 当推送 `v1.0.0` 这类 tag 时，把 AppImage 附加到 GitHub Release

## 测试

```bash
python -m unittest discover -s tests
```

## 仓库结构

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
