#!/usr/bin/env python3
from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from .d3keyhelper_linux import DEFAULT_VERSION, create_default_config, main as runtime_main
except ImportError:
    try:
        from linux_port.d3keyhelper_linux import DEFAULT_VERSION, create_default_config, main as runtime_main
    except ImportError:
        from d3keyhelper_linux import DEFAULT_VERSION, create_default_config, main as runtime_main


START_METHOD_ITEMS = [
    (1, "鼠标右键"),
    (2, "鼠标中键"),
    (3, "滚轮向上"),
    (4, "滚轮向下"),
    (5, "侧键1"),
    (6, "侧键2"),
    (7, "键盘按键"),
]
COMMON_METHOD_ITEMS = [
    (1, "无"),
    (2, "鼠标中键"),
    (3, "滚轮向上"),
    (4, "滚轮向下"),
    (5, "侧键1"),
    (6, "侧键2"),
    (7, "键盘按键"),
]
SKILL_ACTION_ITEMS = [
    (1, "禁用"),
    (2, "按住不放"),
    (3, "连点"),
    (4, "保持Buff"),
    (5, "按键触发"),
]
START_MODE_ITEMS = [(1, "懒人模式"), (2, "仅按住时"), (3, "仅按一次")]
MOVING_METHOD_ITEMS = [(1, "无"), (2, "强制站立"), (3, "强制走位（按住）"), (4, "强制走位（连点）")]
POTION_METHOD_ITEMS = [(1, "无"), (2, "定时连点"), (3, "保持药水CD")]
SALVAGE_METHOD_ITEMS = [
    (1, "快速分解"),
    (2, "一键分解"),
    (3, "智能分解"),
    (4, "智能分解（留神圣/无形/太古）"),
    (5, "智能分解（只留太古）"),
]
REFORGE_METHOD_ITEMS = [(1, "重铸一次"), (2, "重铸到远古/太古"), (3, "重铸到太古")]
QUICK_PAUSE_MODE_ITEMS = [(1, "双击"), (2, "单击"), (3, "按住")]
QUICK_PAUSE_TRIGGER_ITEMS = [(1, "鼠标左键"), (2, "鼠标右键"), (3, "鼠标中键"), (4, "侧键1"), (5, "侧键2")]
QUICK_PAUSE_ACTION_ITEMS = [(1, "暂停宏"), (2, "暂停宏并连点左键")]
HELPER_SPEED_PRESET_ITEMS = [(1, "非常快"), (2, "快速"), (3, "中等"), (4, "慢速"), (5, "自定义")]
HELPER_SPEED_PRESET_VALUES = {1: (0, 50), 2: (1, 100), 3: (2, 150), 4: (3, 200)}
SEND_MODE_ITEMS = [("Event", "Event"), ("Input", "Input")]
FULL_WINDOW_SIZE = (1600, 950)
COMPACT_WINDOW_SIZE = (1180, 760)
DEFAULT_SKILLS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "LButton", 6: "RButton"}

AUTOSTART_TOOLTIP = "开启后，以懒人模式启动的战斗宏可以在运行中无缝切换"
START_MODE_TOOLTIP = (
    "懒人模式：按下战斗宏快捷键时开启宏，再按一下关闭宏\n"
    "仅按住时：仅在战斗宏快捷键被压下时启动宏\n"
    "仅按一次：按下战斗宏快捷键即按下所有“按住不放”的技能键一次"
)
SKILL_QUEUE_TOOLTIP = (
    "开启后按键不会被立刻按下而是存储至一个按键队列中\n"
    "连点会使技能加入队列头部，保持Buff会使技能加入队列尾部\n"
    "并且连点时会自动按下强制站立"
)
SKILL_QUEUE_INTERVAL_TOOLTIP = "按键队列中的连点按键会以此间隔一一发送至游戏窗口"
POTION_TOOLTIP = "定时连点：以固定时间间隔连续点击药水按键\n保持药水CD：仅在药水CD结束时连点，从而使药水尽快重新进入CD"
DELAY_TOOLTIP = "正数代表策略延后执行，负数代表策略提前执行，设为0可以关闭延迟"
RANDOM_TOOLTIP = "勾选后，每次策略执行时的实际延迟为0至设置值之间的随机数"
SKILL_ACTION_TOOLTIP = (
    "禁用：不发送该技能按键\n"
    "按住不放：宏启动后一直按住该键\n"
    "连点：按设置间隔重复按键\n"
    "保持Buff：检测Buff将结束时补按\n"
    "按键触发：仅在按下触发键时执行"
)
PRIORITY_TOOLTIP = "多个保持Buff技能同时启用时，优先级越高越优先续按"
REPEAT_TOOLTIP = "每次策略触发时，连续发送该技能按键的次数"
REPEAT_INTERVAL_TOOLTIP = "重复发送同一技能时，两次按键之间的间隔"
TRIGGER_BUTTON_TOOLTIP = "当策略为“按键触发”时，按下这个触发键才会执行技能"
RUN_ON_START_TOOLTIP = "开启后，各技能策略会在宏启动瞬间先执行一次"
SMART_PAUSE_TOOLTIP = "开启后，游戏中按Tab键可以暂停宏\n回车键，M键，T键会停止宏"
GAME_GAMMA_TOOLTIP = "如果你在游戏里用了自定义 Gamma，把 D3Prefs.txt 里的 Gamma 值填到这里"
BUFF_PERCENT_TOOLTIP = "保持Buff模式会在Buff剩余低于这个比例时自动续按，范围 0 到 1"
GAME_RESOLUTION_TOOLTIP = "Auto 表示自动读取窗口大小，也可以手动写成 1920x1080 这种格式"
HELPER_HOTKEY_TOOLTIP = "按下这个热键后，程序会根据当前界面自动选择 赌博/分解/重铸/升级/转化/丢装/拾取 助手"
HELPER_SPEED_TOOLTIP = "当网络延迟较高时，适当降低动画速度可以减少宏出错的概率"
HELPER_SPEED_PRESET_TOOLTIP = (
    "非常快：鼠标速度0，动画延迟50\n"
    "快速：鼠标速度1，动画延迟100\n"
    "中等：鼠标速度2，动画延迟150\n"
    "慢速：鼠标速度3，动画延迟200\n"
    "自定义：使用配置文件中的预设值"
)
SAFEZONE_TOOLTIP = "格式为英文逗号连接的格子编号\n左上角格子编号为1，右上角为10，左下角为51，右下角为60"
GAMBLE_TOOLTIP = "赌博时按下助手快捷键可以自动点击右键"
LOOT_TOOLTIP = "拾取装备时按下助手快捷键可以自动点击左键"
SALVAGE_ENABLE_TOOLTIP = "分解装备时按下助手快捷键可以自动执行所选择的策略"
SALVAGE_METHOD_TOOLTIP = (
    "快速分解：按下快捷键即等同于点击鼠标左键+回车\n"
    "一键分解：一键分解背包内所有非安全格的装备\n"
    "智能分解：同一键分解，但会跳过远古，神圣，太古\n"
    "智能分解（留神圣/无形/太古）：只保留神圣，无形，太古装备\n"
    "智能分解（只留太古）：只保留太古装备"
)
UPGRADE_TOOLTIP = "当魔盒打开且在升级页面时，按下助手快捷键即自动升级所有非安全格内的稀有（黄色）装备"
CONVERT_TOOLTIP = "当魔盒打开且在转化材料页面时，按下助手快捷键即自动使用所有非安全格内的装备进行材料转化"
ABANDON_TOOLTIP = (
    "当背包栏打开且鼠标指针位于背包栏内时，按下助手快捷键即自动丢弃所有非安全格的物品\n"
    "若储物箱打开且鼠标位于银行格子内时，会存储所有非安全格内的物品至储物箱"
)
CUSTOM_STANDING_TOOLTIP = "开启后，用这里填写的按键替代默认的 Shift 强制站立键"
CUSTOM_MOVING_TOOLTIP = "开启后，用这里填写的按键替代默认的强制移动键"
CUSTOM_POTION_TOOLTIP = "开启后，用这里填写的按键替代默认的药水键"
PROFILE_HOTKEY_TOOLTIP = "按下这个按键可以快速切换到当前配置"
SEND_MODE_TOOLTIP = "Linux 版保留 sendmode 配置项以兼容原版配置；当前统一使用 Linux 输入后端，不直接映射 AHK SendMode"
SOUND_ON_SWITCH_TOOLTIP = "开启后，使用快捷键切换配置成功时播放提示音"
COMPACT_MODE_TOOLTIP = "开启后切换到更紧凑的窗口布局，并隐藏日志区域"
LEGACY_SAFEZONE_SENTINEL = "61,62,63"


def make_reforge_method_tooltip(max_reforge: int) -> str:
    return (
        "重铸一次：重铸鼠标指针处的装备一次\n"
        f"重铸到远古/太古：不停重铸鼠标指针处的装备，直到变为远古或者太古装备，最多重铸{max_reforge}次\n"
        f"重铸到太古：不停重铸鼠标指针处的装备，直到变成太古装备，最多重铸{max_reforge}次\n"
        "***重铸过程中再次按下助手快捷键可以打断宏！***"
    )


def set_combo_value(combo: QComboBox, value) -> None:
    index = combo.findData(value)
    combo.setCurrentIndex(index if index >= 0 else 0)


def combo_value(combo: QComboBox) -> int:
    return int(combo.currentData())


def combo_data(combo: QComboBox):
    return combo.currentData()


def classify_safezone_text(text: str) -> tuple[str, set[int]]:
    stripped = text.strip()
    if not stripped:
        return "unset", set()
    normalized_parts = [part.strip() for part in stripped.split(",") if part.strip()]
    normalized = ",".join(normalized_parts)
    if normalized == LEGACY_SAFEZONE_SENTINEL:
        return "legacy-default", set()
    if any(not part.isdigit() for part in normalized_parts):
        return "invalid", set()
    values = {int(part) for part in normalized_parts if 1 <= int(part) <= 60}
    if values:
        return "set", values
    return "unset", set()


def helper_speed_preset_from_values(mouse_speed: int, animation_delay: int, configured_preset: int = 5) -> int:
    for preset_id, values in HELPER_SPEED_PRESET_VALUES.items():
        if values == (mouse_speed, animation_delay):
            return preset_id
    return configured_preset if configured_preset in {1, 2, 3, 4, 5} else 5


def add_compact_rows(layout: QGridLayout, fields, columns: int = 2) -> None:
    for index, field in enumerate(fields):
        label, widget = field[0], field[1]
        tooltip = field[2] if len(field) > 2 else ""
        row = index // columns
        column = (index % columns) * 2
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            label_widget.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        layout.addWidget(label_widget, row, column)
        layout.addWidget(widget, row, column + 1)
    for column in range(columns * 2):
        layout.setColumnStretch(column, 1 if column % 2 else 0)


def load_parser(config_path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    encodings = ["utf-16", "utf-8-sig", "utf-8"]
    for encoding in encodings:
        try:
            with config_path.open("r", encoding=encoding) as handle:
                parser.read_file(handle)
            return parser
        except FileNotFoundError:
            raise
        except Exception:
            continue
    raise RuntimeError(f"无法读取配置文件：{config_path}")


def build_runner_command(config_path: Path, profile: str) -> list[str]:
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--runner", "--config", str(config_path)]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--runner", "--config", str(config_path)]
    if profile:
        command += ["--profile", profile]
    return command


class ProfileTab(QWidget):
    def __init__(self, section_name: str, section: configparser.SectionProxy) -> None:
        super().__init__()
        self.widgets: dict[str, object] = {}
        self.section_name = section_name
        root = QVBoxLayout(self)

        header = QGroupBox("配置")
        header_grid = QGridLayout(header)
        self.widgets["name"] = QLineEdit(section_name)
        self.widgets["profilehkmethod"] = self._combo(COMMON_METHOD_ITEMS, int(section.get("profilehkmethod", "1")))
        self.widgets["profilehkkey"] = QLineEdit(section.get("profilehkkey", ""))
        self.widgets["autostartmarco"] = self._check(section.get("autostartmarco", "0") == "1")
        self.widgets["lazymode"] = self._combo(START_MODE_ITEMS, int(section.get("lazymode", "1")))
        self.widgets["movingmethod"] = self._combo(MOVING_METHOD_ITEMS, int(section.get("movingmethod", "1")))
        self.widgets["movinginterval"] = self._spin(20, 3000, int(section.get("movinginterval", "100")))
        self.widgets["potionmethod"] = self._combo(POTION_METHOD_ITEMS, int(section.get("potionmethod", "1")))
        self.widgets["potioninterval"] = self._spin(200, 30000, int(section.get("potioninterval", "500")))
        self.widgets["useskillqueue"] = self._check(section.get("useskillqueue", "0") == "1")
        self.widgets["useskillqueueinterval"] = self._spin(50, 1000, int(section.get("useskillqueueinterval", "200")))
        self.widgets["enablequickpause"] = self._check(section.get("enablequickpause", "0") == "1")
        self.widgets["quickpausemethod1"] = self._combo(QUICK_PAUSE_MODE_ITEMS, int(section.get("quickpausemethod1", "1")))
        self.widgets["quickpausemethod2"] = self._combo(QUICK_PAUSE_TRIGGER_ITEMS, int(section.get("quickpausemethod2", "1")))
        self.widgets["quickpausemethod3"] = self._combo(QUICK_PAUSE_ACTION_ITEMS, int(section.get("quickpausemethod3", "1")))
        self.widgets["quickpausedelay"] = self._spin(50, 5000, int(section.get("quickpausedelay", "1500")))

        add_compact_rows(
            header_grid,
            [
                ("配置名", self.widgets["name"]),
                ("快速切换类型", self.widgets["profilehkmethod"], PROFILE_HOTKEY_TOOLTIP),
                ("快速切换按键", self.widgets["profilehkkey"], PROFILE_HOTKEY_TOOLTIP),
                ("切换后自动启动宏", self.widgets["autostartmarco"], AUTOSTART_TOOLTIP),
                ("宏启动方式", self.widgets["lazymode"], START_MODE_TOOLTIP),
                ("走位辅助", self.widgets["movingmethod"]),
                ("走位间隔（毫秒）", self.widgets["movinginterval"]),
                ("药水辅助", self.widgets["potionmethod"], POTION_TOOLTIP),
                ("药水间隔（毫秒）", self.widgets["potioninterval"]),
                ("单线程按键队列", self.widgets["useskillqueue"], SKILL_QUEUE_TOOLTIP),
                ("按键队列间隔（毫秒）", self.widgets["useskillqueueinterval"], SKILL_QUEUE_INTERVAL_TOOLTIP),
                ("快速暂停", self.widgets["enablequickpause"]),
                ("快速暂停触发方式", self.widgets["quickpausemethod1"]),
                ("快速暂停按键", self.widgets["quickpausemethod2"]),
                ("快速暂停动作", self.widgets["quickpausemethod3"]),
                ("快速暂停时长（毫秒）", self.widgets["quickpausedelay"]),
            ],
            columns=2,
        )
        root.addWidget(header)

        skill_group = QGroupBox("技能")
        skill_grid = QGridLayout(skill_group)
        headers = ["槽位", "按键", "策略", "间隔", "延迟", "随机", "优先级", "重复", "重复间隔", "触发键"]
        header_tooltips = {
            "策略": SKILL_ACTION_TOOLTIP,
            "延迟": DELAY_TOOLTIP,
            "随机": RANDOM_TOOLTIP,
            "优先级": PRIORITY_TOOLTIP,
            "重复": REPEAT_TOOLTIP,
            "重复间隔": REPEAT_INTERVAL_TOOLTIP,
            "触发键": TRIGGER_BUTTON_TOOLTIP,
        }
        for column, text in enumerate(headers):
            label = QLabel(text)
            if text in header_tooltips:
                label.setToolTip(header_tooltips[text])
            skill_grid.addWidget(label, 0, column)

        skill_widgets = []
        for index in range(1, 7):
            row = {}
            row["hotkey"] = QLineEdit(section.get(f"skill_{index}", DEFAULT_SKILLS[index]))
            row["action"] = self._combo(SKILL_ACTION_ITEMS, int(section.get(f"action_{index}", "1")))
            row["interval"] = self._spin(20, 60000, int(section.get(f"interval_{index}", "300")))
            row["delay"] = self._spin(-30000, 30000, int(section.get(f"delay_{index}", "10")))
            row["random"] = self._check(section.get(f"random_{index}", "1") == "1")
            row["priority"] = self._spin(1, 10, int(section.get(f"priority_{index}", "1")))
            row["repeat"] = self._spin(1, 99, int(section.get(f"repeat_{index}", "1")))
            row["repeatinterval"] = self._spin(0, 1000, int(section.get(f"repeatinterval_{index}", "30")))
            row["triggerbutton"] = QLineEdit(section.get(f"triggerbutton_{index}", "LButton"))
            row["action"].setToolTip(SKILL_ACTION_TOOLTIP)
            row["delay"].setToolTip(DELAY_TOOLTIP)
            row["random"].setToolTip(RANDOM_TOOLTIP)
            row["priority"].setToolTip(PRIORITY_TOOLTIP)
            row["repeat"].setToolTip(REPEAT_TOOLTIP)
            row["repeatinterval"].setToolTip(REPEAT_INTERVAL_TOOLTIP)
            row["triggerbutton"].setToolTip(TRIGGER_BUTTON_TOOLTIP)
            if index in {5, 6}:
                row["hotkey"].setReadOnly(True)
            skill_grid.addWidget(QLabel(f"技能{index}"), index, 0)
            skill_grid.addWidget(row["hotkey"], index, 1)
            skill_grid.addWidget(row["action"], index, 2)
            skill_grid.addWidget(row["interval"], index, 3)
            skill_grid.addWidget(row["delay"], index, 4)
            skill_grid.addWidget(row["random"], index, 5, alignment=Qt.AlignmentFlag.AlignCenter)
            skill_grid.addWidget(row["priority"], index, 6)
            skill_grid.addWidget(row["repeat"], index, 7)
            skill_grid.addWidget(row["repeatinterval"], index, 8)
            skill_grid.addWidget(row["triggerbutton"], index, 9)
            skill_widgets.append(row)
        self.widgets["skills"] = skill_widgets
        self.skill_queue_warning = QLabel("注意：当前按键队列可能跟不上连点技能的入队速度")
        self.skill_queue_warning.setStyleSheet("color: #c62828;")
        self.skill_queue_warning.hide()
        root.addWidget(skill_group)
        root.addWidget(self.skill_queue_warning)
        self._start_method_conflict = False
        self._connect_dynamic_controls()
        self.refresh_dynamic_state()

    def _combo(self, items, value: int) -> QComboBox:
        combo = QComboBox()
        for data, text in items:
            combo.addItem(text, data)
        set_combo_value(combo, value)
        return combo

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        return widget

    def _check(self, checked: bool) -> QCheckBox:
        widget = QCheckBox()
        widget.setChecked(checked)
        return widget

    def _connect_dynamic_controls(self) -> None:
        self.widgets["profilehkmethod"].currentIndexChanged.connect(self._sync_profile_hotkey_state)
        self.widgets["lazymode"].currentIndexChanged.connect(self._sync_start_mode_state)
        self.widgets["movingmethod"].currentIndexChanged.connect(self._sync_moving_potion_state)
        self.widgets["potionmethod"].currentIndexChanged.connect(self._sync_moving_potion_state)
        self.widgets["useskillqueue"].toggled.connect(self._sync_skill_queue_state)
        self.widgets["useskillqueueinterval"].valueChanged.connect(self._sync_skill_queue_warning)
        self.widgets["enablequickpause"].toggled.connect(self._sync_quick_pause_state)
        self.widgets["quickpausemethod1"].currentIndexChanged.connect(self._sync_quick_pause_state)
        for row in self.widgets["skills"]:
            row["action"].currentIndexChanged.connect(self.refresh_dynamic_state)
            row["interval"].valueChanged.connect(self._sync_skill_queue_warning)

    def refresh_dynamic_state(self, *_args) -> None:
        self._sync_profile_hotkey_state()
        self._sync_start_mode_state()
        self._sync_moving_potion_state()
        self._sync_skill_queue_state()
        self._sync_quick_pause_state()
        for index, row in enumerate(self.widgets["skills"], start=1):
            self._sync_skill_row_state(index, row)
        self._sync_skill_queue_warning()

    def apply_start_hotkey_conflict(self, start_method: int) -> None:
        self._start_method_conflict = start_method == 1
        if self._start_method_conflict:
            row = self.widgets["skills"][5]
            old = row["action"].blockSignals(True)
            set_combo_value(row["action"], 1)
            row["action"].blockSignals(old)
        self.refresh_dynamic_state()

    def _sync_profile_hotkey_state(self, *_args) -> None:
        method = combo_value(self.widgets["profilehkmethod"])
        keyboard_only = method == 7
        enabled = method != 1
        self.widgets["profilehkkey"].setEnabled(keyboard_only)
        self.widgets["autostartmarco"].setEnabled(enabled)

    def _sync_start_mode_state(self, *_args) -> None:
        start_mode = combo_value(self.widgets["lazymode"])
        if start_mode in {2, 3}:
            widget = self.widgets["enablequickpause"]
            old = widget.blockSignals(True)
            widget.setChecked(False)
            widget.blockSignals(old)
        if start_mode == 3:
            for widget, value in [
                (self.widgets["useskillqueue"], False),
            ]:
                old = widget.blockSignals(True)
                widget.setChecked(value)
                widget.blockSignals(old)
            for widget, value in [
                (self.widgets["movingmethod"], 1),
                (self.widgets["potionmethod"], 1),
            ]:
                old = widget.blockSignals(True)
                set_combo_value(widget, value)
                widget.blockSignals(old)
        self.widgets["useskillqueue"].setEnabled(start_mode != 3)
        self.widgets["movingmethod"].setEnabled(start_mode != 3)
        self.widgets["potionmethod"].setEnabled(start_mode != 3)
        self.widgets["enablequickpause"].setEnabled(start_mode == 1)

    def _sync_moving_potion_state(self, *_args) -> None:
        self.widgets["movinginterval"].setEnabled(combo_value(self.widgets["movingmethod"]) == 4 and self.widgets["movingmethod"].isEnabled())
        self.widgets["potioninterval"].setEnabled(combo_value(self.widgets["potionmethod"]) > 1 and self.widgets["potionmethod"].isEnabled())

    def _sync_skill_queue_state(self, *_args) -> None:
        enabled = self.widgets["useskillqueue"].isChecked() and self.widgets["useskillqueue"].isEnabled()
        self.widgets["useskillqueueinterval"].setEnabled(enabled)
        self._sync_skill_queue_warning()

    def _sync_quick_pause_state(self, *_args) -> None:
        enabled = self.widgets["enablequickpause"].isChecked() and self.widgets["enablequickpause"].isEnabled()
        for key in ["quickpausemethod1", "quickpausemethod2", "quickpausemethod3"]:
            self.widgets[key].setEnabled(enabled)
        self.widgets["quickpausedelay"].setEnabled(enabled and combo_value(self.widgets["quickpausemethod1"]) != 3)

    def _sync_skill_row_state(self, index: int, row: dict[str, QWidget]) -> None:
        action = combo_value(row["action"])
        if index == 6 and self._start_method_conflict:
            row["action"].setEnabled(False)
            action = 1
        else:
            row["action"].setEnabled(True)
        row["interval"].setEnabled(action in {3, 4})
        row["delay"].setEnabled(action in {3, 5})
        row["random"].setEnabled(action in {3, 5})
        row["priority"].setEnabled(action == 4)
        row["repeat"].setEnabled(action in {3, 5})
        row["repeatinterval"].setEnabled(action in {3, 5})
        row["triggerbutton"].setEnabled(action == 5)

    def _sync_skill_queue_warning(self, *_args) -> None:
        if not self.widgets["useskillqueue"].isChecked() or not self.widgets["useskillqueue"].isEnabled():
            self.skill_queue_warning.hide()
            return
        interval = self.widgets["useskillqueueinterval"].value()
        if interval <= 0:
            self.skill_queue_warning.hide()
            return
        queue_out = 1000.0 / interval
        queue_in = 0.0
        for row in self.widgets["skills"]:
            if combo_value(row["action"]) == 3:
                queue_in += 1000.0 / max(row["interval"].value(), 20)
        if queue_in > queue_out:
            self.skill_queue_warning.setToolTip(
                f"当前按键配置每秒向队列中填入{queue_in:.2f}个“连点”技能，但却只取出{queue_out:.2f}个\n"
                "你应当把Buff类技能设置为“保持Buff”而不是“连点”，或者增加连点间隔，或者减少按键队列发送间隔"
            )
            self.skill_queue_warning.show()
        else:
            self.skill_queue_warning.hide()


class MainWindow(QMainWindow):
    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path
        if not self.config_path.exists():
            create_default_config(self.config_path)
        self.process: Optional[QProcess] = None
        self.general_widgets: dict[str, object] = {}
        self.profile_tabs: list[ProfileTab] = []
        self._suspend_config_watch = False
        self._config_apply_timer = QTimer(self)
        self._config_apply_timer.setSingleShot(True)
        self._config_apply_timer.setInterval(500)
        self._config_apply_timer.timeout.connect(self._apply_live_config_change)
        self.tabs = QTabWidget()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.setWindowTitle("D3keyHelper Linux")
        self.resize(*FULL_WINDOW_SIZE)
        self._build_shell()
        self.reload_config()

    def _build_shell(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        toolbar = QHBoxLayout()
        self.path_label = QLabel(str(self.config_path))
        self.profile_line = QLineEdit()
        self.profile_line.setPlaceholderText("启动时可选：配置名或编号")
        reload_button = QPushButton("重新载入")
        reload_button.clicked.connect(self.reload_config)
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        start_button = QPushButton("启动运行器")
        start_button.clicked.connect(self.start_runner)
        stop_button = QPushButton("停止运行器")
        stop_button.clicked.connect(self.stop_runner)
        toolbar.addWidget(self.path_label, 1)
        toolbar.addWidget(self.profile_line)
        toolbar.addWidget(reload_button)
        toolbar.addWidget(save_button)
        toolbar.addWidget(start_button)
        toolbar.addWidget(stop_button)
        layout.addLayout(toolbar)
        layout.addWidget(self.tabs, 3)
        layout.addWidget(self.log, 1)
        self.setCentralWidget(central)

    def reload_config(self) -> None:
        self._config_apply_timer.stop()
        self._suspend_config_watch = True
        parser = load_parser(self.config_path)
        self.tabs.clear()
        self.profile_tabs.clear()
        self.log.appendPlainText(f"已载入配置：{self.config_path}")
        general_name = next(name for name in parser.sections() if name.lower() == "general")
        self.tabs.addTab(self._build_general_tab(parser[general_name]), "General")
        for name in parser.sections():
            if name.lower() == "general":
                continue
            tab = ProfileTab(name, parser[name])
            self.profile_tabs.append(tab)
            self.tabs.addTab(tab, name)
        self._refresh_general_state()
        self._apply_compact_mode()
        self._connect_config_change_watchers()
        self._suspend_config_watch = False

    def _build_general_tab(self, section: configparser.SectionProxy) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)
        summary_grid = QGridLayout()
        helper_speed_preset = helper_speed_preset_from_values(
            int(section.get("helpermousespeed", "2")),
            int(section.get("helperanimationdelay", "150")),
            int(section.get("helperspeed", "3")),
        )

        basic = QGroupBox("基础")
        basic_grid = QGridLayout(basic)
        self.general_widgets["activatedprofile"] = self._spin(1, 99, int(section.get("activatedprofile", "1")))
        self.general_widgets["startmethod"] = self._combo(START_METHOD_ITEMS, int(section.get("startmethod", "7")))
        self.general_widgets["starthotkey"] = QLineEdit(section.get("starthotkey", "F2"))
        self.general_widgets["oldsandhelpermethod"] = self._combo(COMMON_METHOD_ITEMS, int(section.get("oldsandhelpermethod", "7")))
        self.general_widgets["oldsandhelperhk"] = QLineEdit(section.get("oldsandhelperhk", "F5"))
        self.general_widgets["sendmode"] = self._combo(SEND_MODE_ITEMS, section.get("sendmode", "Event"))
        self.general_widgets["runonstart"] = self._check(section.get("runonstart", "1") == "1")
        self.general_widgets["d3only"] = self._check(section.get("d3only", "1") == "1")
        self.general_widgets["enablesmartpause"] = self._check(section.get("enablesmartpause", "1") == "1")
        self.general_widgets["enablesoundplay"] = self._check(section.get("enablesoundplay", "1") == "1")
        self.general_widgets["compactmode"] = self._check(section.get("compactmode", "0") == "1")
        self.general_widgets["gameresolution"] = QLineEdit(section.get("gameresolution", "Auto"))
        self.general_widgets["gamegamma"] = self._float_spin(0.5, 1.5, float(section.get("gamegamma", "1.0")), 6)
        self.general_widgets["buffpercent"] = self._float_spin(0.0, 1.0, float(section.get("buffpercent", "0.05")), 6)
        add_compact_rows(
            basic_grid,
            [
                ("当前激活配置", self.general_widgets["activatedprofile"]),
                ("战斗宏启动方式", self.general_widgets["startmethod"]),
                ("战斗宏启动热键", self.general_widgets["starthotkey"]),
                ("助手启动方式", self.general_widgets["oldsandhelpermethod"], HELPER_HOTKEY_TOOLTIP),
                ("助手启动热键", self.general_widgets["oldsandhelperhk"], HELPER_HOTKEY_TOOLTIP),
                ("发送模式", self.general_widgets["sendmode"], SEND_MODE_TOOLTIP),
                ("宏启动瞬间执行一次", self.general_widgets["runonstart"], RUN_ON_START_TOOLTIP),
                ("只作用于 Diablo III 前台窗口", self.general_widgets["d3only"]),
                ("智能暂停", self.general_widgets["enablesmartpause"], SMART_PAUSE_TOOLTIP),
                ("切换配置提示音", self.general_widgets["enablesoundplay"], SOUND_ON_SWITCH_TOOLTIP),
                ("紧凑布局", self.general_widgets["compactmode"], COMPACT_MODE_TOOLTIP),
                ("游戏分辨率（Auto/宽x高）", self.general_widgets["gameresolution"], GAME_RESOLUTION_TOOLTIP),
                ("游戏 Gamma", self.general_widgets["gamegamma"], GAME_GAMMA_TOOLTIP),
                ("Buff 续按阈值", self.general_widgets["buffpercent"], BUFF_PERCENT_TOOLTIP),
            ],
            columns=2,
        )
        summary_grid.addWidget(basic, 0, 0)

        helper = QGroupBox("助手/输入")
        helper_grid = QGridLayout(helper)
        for key, value in [
            ("customstanding", section.get("customstanding", "0") == "1"),
            ("custommoving", section.get("custommoving", "0") == "1"),
            ("custompotion", section.get("custompotion", "0") == "1"),
            ("enablegamblehelper", section.get("enablegamblehelper", "1") == "1"),
            ("enableloothelper", section.get("enableloothelper", "0") == "1"),
            ("enablesalvagehelper", section.get("enablesalvagehelper", "0") == "1"),
            ("enablereforgehelper", section.get("enablereforgehelper", "0") == "1"),
            ("enableupgradehelper", section.get("enableupgradehelper", "0") == "1"),
            ("enableconverthelper", section.get("enableconverthelper", "0") == "1"),
            ("enableabandonhelper", section.get("enableabandonhelper", "0") == "1"),
        ]:
            self.general_widgets[key] = self._check(value)
        self.general_widgets["customstandinghk"] = QLineEdit(section.get("customstandinghk", "LShift"))
        self.general_widgets["custommovinghk"] = QLineEdit(section.get("custommovinghk", "e"))
        self.general_widgets["custompotionhk"] = QLineEdit(section.get("custompotionhk", "q"))
        self.general_widgets["gamblehelpertimes"] = self._spin(1, 60, int(section.get("gamblehelpertimes", "15")))
        self.general_widgets["loothelpertimes"] = self._spin(1, 99, int(section.get("loothelpertimes", "30")))
        self.general_widgets["salvagehelpermethod"] = self._combo(SALVAGE_METHOD_ITEMS, int(section.get("salvagehelpermethod", "1")))
        self.general_widgets["reforgehelpermethod"] = self._combo(REFORGE_METHOD_ITEMS, int(section.get("reforgehelpermethod", "1")))
        self.general_widgets["helperspeed"] = self._combo(HELPER_SPEED_PRESET_ITEMS, helper_speed_preset)
        self.general_widgets["helpermousespeed"] = self._spin(0, 10, int(section.get("helpermousespeed", "2")))
        self.general_widgets["helperanimationdelay"] = self._spin(1, 1000, int(section.get("helperanimationdelay", "150")))
        self.general_widgets["safezone"] = QLineEdit(section.get("safezone", "61,62,63"))
        self.general_widgets["maxreforge"] = self._spin(1, 999, int(section.get("maxreforge", "10")))
        self.general_widgets["safezonestatus"] = QLabel()
        self.general_widgets["helperspeed"].currentIndexChanged.connect(self._apply_helper_speed_preset)
        self.general_widgets["helpermousespeed"].valueChanged.connect(self._sync_helper_speed_preset)
        self.general_widgets["helperanimationdelay"].valueChanged.connect(self._sync_helper_speed_preset)
        add_compact_rows(
            helper_grid,
            [
                ("自定义强制站立", self.general_widgets["customstanding"], CUSTOM_STANDING_TOOLTIP),
                ("强制站立按键", self.general_widgets["customstandinghk"], CUSTOM_STANDING_TOOLTIP),
                ("自定义强制移动", self.general_widgets["custommoving"], CUSTOM_MOVING_TOOLTIP),
                ("强制移动按键", self.general_widgets["custommovinghk"], CUSTOM_MOVING_TOOLTIP),
                ("自定义药水按键", self.general_widgets["custompotion"], CUSTOM_POTION_TOOLTIP),
                ("药水按键", self.general_widgets["custompotionhk"], CUSTOM_POTION_TOOLTIP),
                ("赌博助手", self.general_widgets["enablegamblehelper"], GAMBLE_TOOLTIP),
                ("赌博点击次数", self.general_widgets["gamblehelpertimes"]),
                ("拾取助手", self.general_widgets["enableloothelper"], LOOT_TOOLTIP),
                ("拾取点击次数", self.general_widgets["loothelpertimes"]),
                ("分解助手", self.general_widgets["enablesalvagehelper"], SALVAGE_ENABLE_TOOLTIP),
                ("分解策略", self.general_widgets["salvagehelpermethod"], SALVAGE_METHOD_TOOLTIP),
                ("重铸助手", self.general_widgets["enablereforgehelper"], "当魔盒打开且在重铸页面时，按下助手快捷键可以自动执行所选择的重铸策略\n***最大重铸次数可以通过配置文件中的 maxreforge 变量修改***"),
                ("重铸策略", self.general_widgets["reforgehelpermethod"], make_reforge_method_tooltip(self.general_widgets["maxreforge"].value())),
                ("升级助手", self.general_widgets["enableupgradehelper"], UPGRADE_TOOLTIP),
                ("转化助手", self.general_widgets["enableconverthelper"], CONVERT_TOOLTIP),
                ("丢装助手", self.general_widgets["enableabandonhelper"], ABANDON_TOOLTIP),
                ("动画速度预设", self.general_widgets["helperspeed"], HELPER_SPEED_PRESET_TOOLTIP),
                ("辅助鼠标速度", self.general_widgets["helpermousespeed"], HELPER_SPEED_TOOLTIP),
                ("辅助动画延迟（毫秒）", self.general_widgets["helperanimationdelay"], HELPER_SPEED_TOOLTIP),
                ("安全格", self.general_widgets["safezone"], SAFEZONE_TOOLTIP),
                ("最大重铸次数", self.general_widgets["maxreforge"]),
            ],
            columns=2,
        )
        helper_grid.addWidget(self.general_widgets["safezonestatus"], helper_grid.rowCount(), 0, 1, 4)
        self.general_widgets["maxreforge"].valueChanged.connect(self._sync_reforge_tooltip)
        self._sync_reforge_tooltip()
        self._sync_helper_speed_preset()
        self._connect_general_dynamic_controls()
        self._refresh_general_state()
        summary_grid.addWidget(helper, 0, 1)
        summary_grid.setColumnStretch(0, 1)
        summary_grid.setColumnStretch(1, 1)
        root.addLayout(summary_grid)
        root.addStretch(1)
        return tab

    def _combo(self, items, value: int) -> QComboBox:
        combo = QComboBox()
        for data, text in items:
            combo.addItem(text, data)
        set_combo_value(combo, value)
        return combo

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        return widget

    def _float_spin(self, minimum: float, maximum: float, value: float, decimals: int) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setSingleStep(0.01)
        widget.setValue(value)
        return widget

    def _check(self, checked: bool) -> QCheckBox:
        widget = QCheckBox()
        widget.setChecked(checked)
        return widget

    def _bool_text(self, widget: QCheckBox) -> str:
        return "1" if widget.isChecked() else "0"

    def _apply_helper_speed_preset(self, *_args) -> None:
        preset = combo_value(self.general_widgets["helperspeed"])
        if preset not in HELPER_SPEED_PRESET_VALUES:
            return
        mouse_speed, animation_delay = HELPER_SPEED_PRESET_VALUES[preset]
        for widget, value in [
            (self.general_widgets["helpermousespeed"], mouse_speed),
            (self.general_widgets["helperanimationdelay"], animation_delay),
        ]:
            old = widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(old)
        self._sync_helper_speed_preset()

    def _sync_helper_speed_preset(self, *_args) -> None:
        preset = helper_speed_preset_from_values(
            self.general_widgets["helpermousespeed"].value(),
            self.general_widgets["helperanimationdelay"].value(),
            5,
        )
        combo = self.general_widgets["helperspeed"]
        old = combo.blockSignals(True)
        set_combo_value(combo, preset)
        combo.blockSignals(old)

    def _sync_reforge_tooltip(self, *_args) -> None:
        tooltip = make_reforge_method_tooltip(self.general_widgets["maxreforge"].value())
        self.general_widgets["reforgehelpermethod"].setToolTip(tooltip)

    def _connect_general_dynamic_controls(self) -> None:
        self.general_widgets["startmethod"].currentIndexChanged.connect(self._refresh_general_state)
        self.general_widgets["oldsandhelpermethod"].currentIndexChanged.connect(self._refresh_general_state)
        self.general_widgets["customstanding"].toggled.connect(self._refresh_general_state)
        self.general_widgets["custommoving"].toggled.connect(self._refresh_general_state)
        self.general_widgets["custompotion"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enablegamblehelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enableloothelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enablesalvagehelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enablereforgehelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enableupgradehelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enableconverthelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["enableabandonhelper"].toggled.connect(self._refresh_general_state)
        self.general_widgets["salvagehelpermethod"].currentIndexChanged.connect(self._refresh_general_state)
        self.general_widgets["safezone"].editingFinished.connect(self._refresh_general_state)
        self.general_widgets["compactmode"].toggled.connect(self._apply_compact_mode)

    def _refresh_general_state(self, *_args) -> None:
        start_method = combo_value(self.general_widgets["startmethod"])
        helper_method = combo_value(self.general_widgets["oldsandhelpermethod"])
        self.general_widgets["starthotkey"].setEnabled(start_method == 7)
        self.general_widgets["oldsandhelperhk"].setEnabled(helper_method == 7)
        self.general_widgets["customstandinghk"].setEnabled(self.general_widgets["customstanding"].isChecked())
        self.general_widgets["custommovinghk"].setEnabled(self.general_widgets["custommoving"].isChecked())
        self.general_widgets["custompotionhk"].setEnabled(self.general_widgets["custompotion"].isChecked())
        self.general_widgets["gamblehelpertimes"].setEnabled(self.general_widgets["enablegamblehelper"].isChecked())
        self.general_widgets["loothelpertimes"].setEnabled(self.general_widgets["enableloothelper"].isChecked())
        self.general_widgets["salvagehelpermethod"].setEnabled(self.general_widgets["enablesalvagehelper"].isChecked())
        self.general_widgets["reforgehelpermethod"].setEnabled(self.general_widgets["enablereforgehelper"].isChecked())
        self.general_widgets["maxreforge"].setEnabled(self.general_widgets["enablereforgehelper"].isChecked())
        self._update_safezone_status()
        for tab in self.profile_tabs:
            tab.apply_start_hotkey_conflict(start_method)

    def _update_safezone_status(self) -> None:
        salvage_enabled = self.general_widgets["enablesalvagehelper"].isChecked()
        salvage_mode = combo_value(self.general_widgets["salvagehelpermethod"])
        needs_safezone = any(
            widget.isChecked()
            for widget in [
                self.general_widgets["enableupgradehelper"],
                self.general_widgets["enableconverthelper"],
                self.general_widgets["enableabandonhelper"],
            ]
        ) or (salvage_enabled and salvage_mode != 1)
        status = self.general_widgets["safezonestatus"]
        self.general_widgets["safezone"].setEnabled(needs_safezone)
        if not needs_safezone:
            status.hide()
            return
        text = self.general_widgets["safezone"].text().strip()
        state, values = classify_safezone_text(text)
        if state == "set":
            status.setText("安全格状态：已设置")
            status.setStyleSheet("color: #2e7d32;")
            status.setToolTip(f"当前安全格：{','.join(str(value) for value in sorted(values))}")
        elif state == "legacy-default":
            status.setText("安全格状态：未设置（沿用原版默认值 61,62,63）")
            status.setStyleSheet("color: #616161;")
            status.setToolTip("原版 AHK 默认把 safezone 写成 61,62,63，用来提示格式；这三个格子并不存在。")
        elif state == "unset":
            status.setText("安全格状态：未设置")
            status.setStyleSheet("color: #616161;")
            status.setToolTip("当前没有启用任何 1-60 的安全格。")
        else:
            status.setText("安全格状态：格式错误")
            status.setStyleSheet("color: #c62828;")
            status.setToolTip("请填写 1-60 之间的格子编号，使用英文逗号分隔，例如：1,2,3")
        status.show()

    def _apply_compact_mode(self, *_args) -> None:
        compact = self.general_widgets.get("compactmode")
        enabled = bool(compact.isChecked()) if isinstance(compact, QCheckBox) else False
        self.log.setVisible(not enabled)
        width, height = COMPACT_WINDOW_SIZE if enabled else FULL_WINDOW_SIZE
        self.resize(width, height)

    def save_config(self, log_message: str = "已保存配置。") -> None:
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str.lower
        parser["General"] = {
            "version": DEFAULT_VERSION,
            "activatedprofile": str(self.general_widgets["activatedprofile"].value()),
            "oldsandhelpermethod": str(combo_value(self.general_widgets["oldsandhelpermethod"])),
            "oldsandhelperhk": self.general_widgets["oldsandhelperhk"].text().strip(),
            "sendmode": str(combo_data(self.general_widgets["sendmode"])),
            "enablegamblehelper": self._bool_text(self.general_widgets["enablegamblehelper"]),
            "gamblehelpertimes": str(self.general_widgets["gamblehelpertimes"].value()),
            "enableloothelper": self._bool_text(self.general_widgets["enableloothelper"]),
            "loothelpertimes": str(self.general_widgets["loothelpertimes"].value()),
            "enablesalvagehelper": self._bool_text(self.general_widgets["enablesalvagehelper"]),
            "salvagehelpermethod": str(combo_value(self.general_widgets["salvagehelpermethod"])),
            "enablereforgehelper": self._bool_text(self.general_widgets["enablereforgehelper"]),
            "reforgehelpermethod": str(combo_value(self.general_widgets["reforgehelpermethod"])),
            "enableconverthelper": self._bool_text(self.general_widgets["enableconverthelper"]),
            "enableupgradehelper": self._bool_text(self.general_widgets["enableupgradehelper"]),
            "enableabandonhelper": self._bool_text(self.general_widgets["enableabandonhelper"]),
            "enablesmartpause": self._bool_text(self.general_widgets["enablesmartpause"]),
            "enablesoundplay": self._bool_text(self.general_widgets["enablesoundplay"]),
            "startmethod": str(combo_value(self.general_widgets["startmethod"])),
            "starthotkey": self.general_widgets["starthotkey"].text().strip(),
            "custommoving": self._bool_text(self.general_widgets["custommoving"]),
            "custommovinghk": self.general_widgets["custommovinghk"].text().strip(),
            "customstanding": self._bool_text(self.general_widgets["customstanding"]),
            "customstandinghk": self.general_widgets["customstandinghk"].text().strip(),
            "custompotion": self._bool_text(self.general_widgets["custompotion"]),
            "custompotionhk": self.general_widgets["custompotionhk"].text().strip(),
            "safezone": self.general_widgets["safezone"].text().strip(),
            "gamegamma": f"{self.general_widgets['gamegamma'].value():.6f}",
            "buffpercent": f"{self.general_widgets['buffpercent'].value():.6f}",
            "runonstart": self._bool_text(self.general_widgets["runonstart"]),
            "gameresolution": self.general_widgets["gameresolution"].text().strip() or "Auto",
            "helperspeed": str(combo_value(self.general_widgets["helperspeed"])),
            "helpermousespeed": str(self.general_widgets["helpermousespeed"].value()),
            "helperanimationdelay": str(self.general_widgets["helperanimationdelay"].value()),
            "d3only": self._bool_text(self.general_widgets["d3only"]),
            "maxreforge": str(self.general_widgets["maxreforge"].value()),
            "compactmode": self._bool_text(self.general_widgets["compactmode"]),
        }

        for tab in self.profile_tabs:
            name = tab.widgets["name"].text().strip() or tab.section_name
            parser[name] = {
                "profilehkmethod": str(combo_value(tab.widgets["profilehkmethod"])),
                "profilehkkey": tab.widgets["profilehkkey"].text().strip(),
                "movingmethod": str(combo_value(tab.widgets["movingmethod"])),
                "movinginterval": str(tab.widgets["movinginterval"].value()),
                "potionmethod": str(combo_value(tab.widgets["potionmethod"])),
                "potioninterval": str(tab.widgets["potioninterval"].value()),
                "lazymode": str(combo_value(tab.widgets["lazymode"])),
                "enablequickpause": self._bool_text(tab.widgets["enablequickpause"]),
                "quickpausemethod1": str(combo_value(tab.widgets["quickpausemethod1"])),
                "quickpausemethod2": str(combo_value(tab.widgets["quickpausemethod2"])),
                "quickpausemethod3": str(combo_value(tab.widgets["quickpausemethod3"])),
                "quickpausedelay": str(tab.widgets["quickpausedelay"].value()),
                "useskillqueue": self._bool_text(tab.widgets["useskillqueue"]),
                "useskillqueueinterval": str(tab.widgets["useskillqueueinterval"].value()),
                "autostartmarco": self._bool_text(tab.widgets["autostartmarco"]),
            }
            for index, row in enumerate(tab.widgets["skills"], start=1):
                parser[name][f"skill_{index}"] = row["hotkey"].text().strip() or DEFAULT_SKILLS[index]
                parser[name][f"action_{index}"] = str(combo_value(row["action"]))
                parser[name][f"interval_{index}"] = str(row["interval"].value())
                parser[name][f"delay_{index}"] = str(row["delay"].value())
                parser[name][f"random_{index}"] = "1" if row["random"].isChecked() else "0"
                parser[name][f"priority_{index}"] = str(row["priority"].value())
                parser[name][f"repeat_{index}"] = str(row["repeat"].value())
                parser[name][f"repeatinterval_{index}"] = str(row["repeatinterval"].value())
                parser[name][f"triggerbutton_{index}"] = row["triggerbutton"].text().strip() or "LButton"

        with self.config_path.open("w", encoding="utf-16") as handle:
            handle.write("; Linux GUI config for D3keyHelper\r\n")
            parser.write(handle)
        if log_message:
            self.log.appendPlainText(log_message)
        for index, tab in enumerate(self.profile_tabs, start=1):
            self.tabs.setTabText(index, tab.widgets["name"].text().strip() or tab.section_name)

    def start_runner(self) -> None:
        self._launch_runner(save_first=True, log_message="已启动运行器。")

    def _launch_runner(self, save_first: bool, log_message: str) -> None:
        self._config_apply_timer.stop()
        if save_first:
            self.save_config()
        self.stop_runner(log_message=None)
        command = build_runner_command(self.config_path, self.profile_line.text().strip())
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_process_output)
        self.process.finished.connect(self._runner_finished)
        self.process.start(command[0], command[1:])
        if not self.process.waitForStarted(5000):
            QMessageBox.critical(self, "启动失败", "无法启动 Linux 运行器。")
            self.process = None
            return
        if log_message:
            self.log.appendPlainText(log_message)

    def stop_runner(self, log_message: str | None = "已停止运行器。") -> None:
        if self.process is None:
            return
        finished = self.process.finished
        try:
            finished.disconnect(self._runner_finished)
        except Exception:
            pass
        self.process.terminate()
        self.process.waitForFinished(3000)
        if log_message:
            self.log.appendPlainText(log_message)
        self.process = None

    def _read_process_output(self) -> None:
        if self.process is None:
            return
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if text:
            if "\a" in text or (
                "已切换配置：" in text and self.general_widgets["enablesoundplay"].isChecked()
            ):
                QApplication.beep()
                text = text.replace("\a", "")
            self.log.appendPlainText(text.rstrip())

    def _runner_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if exit_status == QProcess.ExitStatus.NormalExit:
            self.log.appendPlainText(f"运行器已退出，返回码：{exit_code}")
        else:
            self.log.appendPlainText(f"运行器异常退出，返回码：{exit_code}")
        self.process = None

    def _runner_is_active(self) -> bool:
        return self.process is not None and self.process.state() != QProcess.ProcessState.NotRunning

    def _connect_widget_change(self, widget: QWidget) -> None:
        if isinstance(widget, QLineEdit):
            widget.editingFinished.connect(self._schedule_live_config_change)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._schedule_live_config_change)
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(self._schedule_live_config_change)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self._schedule_live_config_change)

    def _connect_config_change_watchers(self) -> None:
        for widget in self.general_widgets.values():
            if isinstance(widget, QWidget):
                self._connect_widget_change(widget)
        for tab in self.profile_tabs:
            for key, widget in tab.widgets.items():
                if key == "skills":
                    for row in widget:
                        for row_widget in row.values():
                            if isinstance(row_widget, QWidget):
                                self._connect_widget_change(row_widget)
                    continue
                if isinstance(widget, QWidget):
                    self._connect_widget_change(widget)

    def _schedule_live_config_change(self, *_args) -> None:
        if self._suspend_config_watch:
            return
        self._config_apply_timer.start()

    def _apply_live_config_change(self) -> None:
        if self._suspend_config_watch:
            return
        was_running = self._runner_is_active()
        self.save_config(log_message="已自动保存配置。")
        if was_running:
            self._launch_runner(save_first=False, log_message="检测到配置变更，已自动重启运行器。")


def main() -> int:
    if "--runner" in sys.argv[1:]:
        original_argv = sys.argv[:]
        try:
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--runner"]
            return runtime_main()
        finally:
            sys.argv = original_argv
    config_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path("d3oldsand.ini").resolve()
    app = QApplication(sys.argv)
    window = MainWindow(config_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
