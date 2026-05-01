# D3keyHelper Linux Port

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

这是 **D3keyHelper** 的 Linux 原生移植版子项目，目标是让暗黑 3 在 **Arch Linux / Steam / Proton / X11 / XWayland** 环境下也能尽量接近原版 AHK 的体验。

## 致谢与许可证

本项目基于原作者 **Weijie Huang** 的 **D3keyHelper** 改造而来，感谢原作者公开发布原版项目与配置格式。

Linux 版继续遵循仓库根目录中的 **MIT License**；为了便于单独分发，本目录也附带了一份同样的许可证文本：`linux_port/LICENSE`。

## 目录说明

1. `d3keyhelper_linux.py`：Linux 运行时
2. `d3keyhelper_linux_gui.py`：Linux 图形配置器
3. `requirements-linux.txt`：Python 依赖
4. `tests/`：回归测试
5. `packaging/`：AppImage 打包元数据
6. `build_appimage.sh`：AppImage 构建脚本

## 当前功能

1. 图形界面编辑 `d3oldsand.ini`
2. 战斗宏启动/停止、快速切换配置、自动保存并自动重启运行器
3. 懒人模式 / 仅按住时 / 仅按一次
4. 技能策略：按住不放、连点、保持 Buff、按键触发
5. 延迟、随机延迟、优先级、重复发送、按键队列
6. 强制站立、强制移动、药水辅助、保持药水 CD
7. 快速暂停、智能暂停
8. 赌博、拾取、分解、重铸、升级、转化、丢装助手
9. Steam/Proton 下基于窗口类名与进程命令行的 Diablo III 识别
10. 原版配置兼容项：`sendmode`、`enablesoundplay`、`compactmode`
11. safezone 兼容原版默认值 `61,62,63`，GUI 会识别为“未设置（沿用原版默认值）”

## 运行方式

```bash
python linux_port/d3keyhelper_linux.py --init-config
python linux_port/d3keyhelper_linux.py --gui
python linux_port/d3keyhelper_linux.py --list-profiles
python linux_port/d3keyhelper_linux.py --profile 配置1
```

也可以继续使用仓库根目录兼容入口：

```bash
python d3keyhelper_linux.py --gui
```

## 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r linux_port/requirements-linux.txt
```

## AppImage 打包

```bash
./linux_port/build_appimage.sh
```

构建完成后产物位于：

```bash
linux_port/build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

运行方式：

```bash
chmod +x linux_port/build/appimage/D3keyHelper-Linux-x86_64.AppImage
./linux_port/build/appimage/D3keyHelper-Linux-x86_64.AppImage
```

## 测试

```bash
python -m unittest discover -s linux_port/tests
```

## GitHub 开源建议

如果要把 Linux 版单独放到 GitHub：

1. 保留本目录下的 `README.md` 与 `LICENSE`
2. 在仓库描述里注明“基于 Weijie Huang 的 D3keyHelper 移植”
3. 发布时附上 AppImage 与 `requirements-linux.txt`
4. 不要移除原作者版权和 MIT 许可证声明
