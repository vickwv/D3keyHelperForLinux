#!/usr/bin/env python3
from __future__ import annotations

import configparser
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QProcess, QTimer, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from .d3keyhelper_linux import DEFAULT_VERSION, create_default_config, default_config_path, main as runtime_main
except ImportError:
    try:
        from linux_port.d3keyhelper_linux import DEFAULT_VERSION, create_default_config, default_config_path, main as runtime_main
    except ImportError:
        from d3keyhelper_linux import DEFAULT_VERSION, create_default_config, default_config_path, main as runtime_main


UI_LANGUAGE_ENV = "D3HELPER_LANG"


def resolve_ui_language() -> str:
    value = os.environ.get(UI_LANGUAGE_ENV, "").strip().lower()
    if value.startswith("en"):
        return "en"
    return "zh"


UI_LANGUAGE = resolve_ui_language()


def tr(chinese: str, english: str) -> str:
    return english if UI_LANGUAGE == "en" else chinese


def app_icon_path() -> Path | None:
    filename = "d3keyhelper-linux-256.png"
    candidates = [
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / filename,
        Path(__file__).resolve().parent / filename,
        Path(__file__).resolve().parent / "packaging" / "icons" / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


APP_STYLE_SHEET = """
QMainWindow {
    background: #f6f7f9;
}
QScrollArea {
    border: none;
    background: transparent;
}
QListWidget#navigationList {
    background: #fbfcfd;
    border: 1px solid #e1e5eb;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}
QListWidget#navigationList::item {
    padding: 6px 8px;
    margin: 2px 0;
    border-radius: 3px;
    color: #233142;
}
QListWidget#navigationList::item:hover {
    background: #f1f4f8;
}
QListWidget#navigationList::item:selected {
    background: #e7f0ff;
    color: #1d4f91;
    font-weight: 600;
}
QStackedWidget {
    background: #ffffff;
}
QSplitter::handle {
    background: transparent;
    width: 8px;
}
QGroupBox {
    border: none;
    margin-top: 8px;
    padding-top: 4px;
    background: transparent;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 0;
    padding: 0 2px;
    color: #404b5a;
}
QPushButton {
    background: #ffffff;
    color: #204a87;
    border: 1px solid #cdd3db;
    border-radius: 4px;
    padding: 0 10px;
    min-height: 26px;
    font-weight: 600;
}
QPushButton:hover {
    background: #f4f6f8;
    border-color: #b8c1cc;
}
QPushButton:pressed {
    background: #e8ebef;
}
QPushButton#primaryButton {
    background: #2f72c4;
    color: #ffffff;
    border-color: #2f72c4;
}
QPushButton#primaryButton:hover {
    background: #295fa0;
    border-color: #295fa0;
}
QPushButton#primaryButton:pressed {
    background: #234d81;
    border-color: #234d81;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    border: 1px solid #cdd3db;
    border-radius: 6px;
    padding: 2px 6px;
    background: #ffffff;
    selection-background-color: #3584e4;
    min-height: 26px;
}
QComboBox {
    padding-right: 28px;
}
QComboBox:hover {
    border-color: #aeb8c5;
    background: #fbfcfe;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2f72c4;
}
QComboBox:disabled {
    color: #8a94a3;
    background: #f1f3f6;
}
QComboBox::drop-down {
    border: none;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    background: transparent;
}
QComboBox::drop-down:hover {
    background: #eef2f7;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #233142;
    border: none;
    border-radius: 0;
    padding: 1px;
    outline: none;
    selection-background-color: #e7f0ff;
    selection-color: #1d4f91;
}
QComboBox QAbstractItemView::item {
    min-height: 24px;
    padding: 4px 8px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background: #f1f4f8;
}
QComboBox QAbstractItemView::item:selected {
    background: #e7f0ff;
    color: #1d4f91;
}
QPlainTextEdit {
    background: #fbfcfd;
    color: #233142;
    border: 1px solid #d9dde3;
    border-radius: 4px;
    padding: 6px;
}
QCheckBox {
    spacing: 4px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QLabel#pathLabel {
    background: #ffffff;
    color: #526173;
    border: 1px solid #d9dde3;
    border-radius: 4px;
    padding: 4px 8px;
}
QFrame#statusStrip {
    background: #ffffff;
    border-top: 1px solid #d9dde3;
    border-left: none;
    border-right: none;
    border-bottom: none;
}
QLabel#statusStripLabel {
    font-weight: 600;
    color: #48566a;
}
QLabel#statusStripValue {
    color: #233142;
}
QFrame#statusDot {
    border-radius: 5px;
    background: #9aa5b1;
}
QFrame#statusDot[running="true"] {
    background: #2ca36c;
}
QFrame#logPanel {
    background: transparent;
    border: none;
}
QFrame#contentPanel {
    background: #ffffff;
}
QFrame#toolbarFrame {
    background: transparent;
}
QLabel#toolbarLabel {
    color: #48566a;
    font-size: 12px;
}
QLabel#sectionHint {
    color: #5d6978;
}
QLabel#pageTitle {
    font-weight: 700;
    color: #1f2933;
    padding-top: 2px;
}
QLabel#pageSubtitle {
    color: #5d6875;
}
QLabel#sectionTitle {
    font-weight: 600;
    color: #1f2933;
}
QLabel#inlineParamLabel {
    color: #48566a;
}
QFrame#sectionSeparator {
    background: #e6e9ee;
    min-height: 1px;
    max-height: 1px;
}
QWidget#pageContainer {
    background: #ffffff;
}
QScrollArea > QWidget {
    background: transparent;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f6f8fb;
    border: 1px solid #dde2ea;
    border-radius: 4px;
    gridline-color: #eaedf2;
    selection-background-color: #dbeafe;
    selection-color: #1f2933;
}
QHeaderView::section {
    background: #edf0f5;
    color: #344054;
    border: none;
    border-right: 1px solid #dde2ea;
    border-bottom: 2px solid #d0d5de;
    padding: 4px 6px;
    font-weight: 600;
}
QHeaderView::section:last {
    border-right: none;
}
QTableWidget QLineEdit, QTableWidget QComboBox, QTableWidget QSpinBox {
    border: none;
    border-radius: 3px;
    padding: 1px 4px;
    min-height: 22px;
    background: transparent;
}
QTableWidget QComboBox {
    padding-right: 22px;
}
QTableWidget QComboBox::drop-down {
    width: 20px;
    background: transparent;
    border-left: none;
}
QTableWidget QLineEdit:focus, QTableWidget QComboBox:focus, QTableWidget QSpinBox:focus {
    background: #ffffff;
    border: 1px solid #2f72c4;
}
"""


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
FULL_WINDOW_SIZE = (1120, 720)
DEFAULT_SKILLS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "LButton", 6: "RButton"}
FORM_LABEL_WIDTH = 116
FORM_FIELD_MIN_WIDTH = 120
FORM_FIELD_MAX_WIDTH = 180
FORM_CONTROL_HEIGHT = 26
TOGGLE_TEXT_WIDTH = 150
INLINE_LABEL_WIDTH = 76

TOOLBAR_PATH_MIN_WIDTH = 220
TOOLBAR_PATH_MAX_WIDTH = 320
NAV_WIDTH = 150
SKILL_TEXT_WIDTH = 68
SKILL_TRIGGER_WIDTH = 72
SKILL_ACTION_WIDTH = 118
SKILL_NUMBER_WIDTH = 60
SKILL_TABLE_ROW_HEIGHT = 32
SKILL_TABLE_HEADER_HEIGHT = 30

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


def tune_combo_box(combo: QComboBox) -> QComboBox:
    popup = QListView()
    popup.setFrameShape(QFrame.Shape.NoFrame)
    popup.setUniformItemSizes(True)
    popup.setSpacing(1)
    popup.setViewportMargins(0, 0, 0, 0)
    popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    combo.setView(popup)
    combo.setMaxVisibleItems(12)
    return combo


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


def build_profile_selector(profile_names: list[str], active_profile: int) -> QComboBox:
    combo = QComboBox()
    tune_combo_box(combo)
    count = max(len(profile_names), active_profile, 1)
    for index in range(1, count + 1):
        name = profile_names[index - 1] if index <= len(profile_names) else f"配置{index}"
        combo.addItem(f"{index} - {name}", index)
    set_combo_value(combo, active_profile)
    return combo


def build_form_layout() -> QFormLayout:
    layout = QFormLayout()
    layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    return layout


def build_settings_grid(fields) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row, field in enumerate(fields):
        label, widget = field[0], field[1]
        tooltip = field[2] if len(field) > 2 else ""
        label_widget = QLabel(label)
        label_widget.setFixedWidth(FORM_LABEL_WIDTH)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            label_widget.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        tune_form_widget(widget)
        layout.addWidget(label_widget, row, 0)
        layout.addWidget(widget, row, 1)
    layout.setColumnMinimumWidth(0, FORM_LABEL_WIDTH)
    layout.setColumnMinimumWidth(1, FORM_FIELD_MIN_WIDTH)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 1)
    return wrapper


def add_form_rows(layout: QFormLayout, fields) -> None:
    for field in fields:
        label, widget = field[0], field[1]
        tooltip = field[2] if len(field) > 2 else ""
        if label is None:
            if tooltip:
                widget.setToolTip(tooltip)
            layout.addRow(widget)
            continue
        label_widget = QLabel(label)
        label_widget.setFixedWidth(FORM_LABEL_WIDTH)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            label_widget.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        tune_form_widget(widget)
        layout.addRow(label_widget, widget)


def build_section(title: str, hint: str | None = None) -> tuple[QWidget, QVBoxLayout]:
    section = QWidget()
    layout = QVBoxLayout(section)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    layout.addWidget(title_label)
    if hint:
        hint_label = QLabel(hint)
        hint_label.setObjectName("sectionHint")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
    separator = QFrame()
    separator.setObjectName("sectionSeparator")
    layout.addWidget(separator)
    return section, layout


def build_sub_header(text: str) -> QWidget:
    """Inline sub-section separator inside a build_section block."""
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 10, 0, 2)
    layout.setSpacing(4)
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    sep = QFrame()
    sep.setObjectName("sectionSeparator")
    layout.addWidget(label)
    layout.addWidget(sep)
    return wrapper


def build_two_column_form(fields) -> QWidget:
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(28)
    split_index = (len(fields) + 1) // 2
    left_form = build_form_layout()
    right_form = build_form_layout()
    add_form_rows(left_form, fields[:split_index])
    add_form_rows(right_form, fields[split_index:])
    left_widget = QWidget()
    left_widget.setLayout(left_form)
    right_widget = QWidget()
    right_widget.setLayout(right_form)
    layout.addWidget(left_widget, 1)
    layout.addWidget(right_widget, 1)
    return wrapper


def build_inline_field(*widgets: QWidget) -> QWidget:
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for widget in widgets:
        if isinstance(widget, QWidget):
            layout.addWidget(widget)
    layout.addStretch(1)
    return wrapper


def build_checkbox_field(
    checkbox: QCheckBox,
    text: str,
    tooltip: str = "",
    trailing_label: str | None = None,
    trailing_widget: QWidget | None = None,
) -> QWidget:
    checkbox.setText(text)
    if tooltip:
        checkbox.setToolTip(tooltip)
    widgets: list[QWidget] = [checkbox]
    if trailing_label:
        label = QLabel(trailing_label)
        if tooltip:
            label.setToolTip(tooltip)
        widgets.append(label)
    if trailing_widget is not None:
        widgets.append(trailing_widget)
    return build_inline_field(*widgets)


def build_toggle_grid(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        checkbox, text = row[0], row[1]
        tooltip = row[2] if len(row) > 2 else ""
        trailing_label = row[3] if len(row) > 3 else None
        trailing_widget = row[4] if len(row) > 4 else None
        checkbox.setText(text)
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        if tooltip:
            checkbox.setToolTip(tooltip)
        if trailing_label or trailing_widget is not None:
            # Row has trailing param: fix checkbox width so param columns align across rows
            checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
            checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout.addWidget(checkbox, row_index, 0)
            if trailing_label:
                label = QLabel(trailing_label)
                label.setObjectName("inlineParamLabel")
                label.setFixedWidth(INLINE_LABEL_WIDTH)
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if tooltip:
                    label.setToolTip(tooltip)
                layout.addWidget(label, row_index, 1)
            else:
                layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
            if trailing_widget is not None:
                tune_form_widget(trailing_widget)
                layout.addWidget(trailing_widget, row_index, 2)
            else:
                layout.addItem(QSpacerItem(FORM_FIELD_MIN_WIDTH, FORM_CONTROL_HEIGHT), row_index, 2)
        else:
            # Simple toggle: let text flow freely — span across all columns
            checkbox.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(checkbox, row_index, 0, 1, 4)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 1)
    return wrapper


def build_option_grid(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        label_text, widget = row[0], row[1]
        tooltip = row[2] if len(row) > 2 else ""
        label = QLabel(label_text)
        label.setFixedWidth(TOGGLE_TEXT_WIDTH)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            label.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        tune_form_widget(widget)
        layout.addWidget(label, row_index, 0)
        layout.addWidget(widget, row_index, 1)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 1)
    return wrapper


def build_helper_grid(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        label_text, main_widget = row[0], row[1]
        tooltip = row[2] if len(row) > 2 else ""
        param_label = row[3] if len(row) > 3 else None
        param_widget = row[4] if len(row) > 4 else None
        label = QLabel(label_text)
        label.setFixedWidth(TOGGLE_TEXT_WIDTH)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if tooltip:
            label.setToolTip(tooltip)
            main_widget.setToolTip(tooltip)
        tune_form_widget(main_widget)
        layout.addWidget(label, row_index, 0)
        if param_label or isinstance(main_widget, QCheckBox):
            layout.addWidget(main_widget, row_index, 1)
        else:
            layout.addItem(QSpacerItem(24, FORM_CONTROL_HEIGHT), row_index, 1)
        if param_label:
            trailing_label = QLabel(param_label)
            trailing_label.setObjectName("inlineParamLabel")
            trailing_label.setFixedWidth(INLINE_LABEL_WIDTH)
            trailing_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                trailing_label.setToolTip(tooltip)
            layout.addWidget(trailing_label, row_index, 2)
        else:
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 2)
        if param_widget is not None:
            tune_form_widget(param_widget)
            layout.addWidget(param_widget, row_index, 3)
        elif not isinstance(main_widget, QCheckBox):
            layout.addWidget(main_widget, row_index, 3)
        else:
            layout.addItem(QSpacerItem(FORM_FIELD_MIN_WIDTH, FORM_CONTROL_HEIGHT), row_index, 3)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 0)
    layout.setColumnStretch(4, 1)
    return wrapper


def build_helper_list(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        checkbox, text = row[0], row[1]
        tooltip = row[2] if len(row) > 2 else ""
        param_label = row[3] if len(row) > 3 else None
        param_widget = row[4] if len(row) > 4 else None
        checkbox.setText(text)
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(param_label)
            label.setObjectName("inlineParamLabel")
            label.setFixedWidth(INLINE_LABEL_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
            layout.addWidget(label, row_index, 1)
        else:
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
        if param_widget is not None:
            tune_form_widget(param_widget)
            layout.addWidget(param_widget, row_index, 2)
        else:
            layout.addItem(QSpacerItem(FORM_FIELD_MIN_WIDTH, FORM_CONTROL_HEIGHT), row_index, 2)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 1)
    return wrapper


def build_helper_section_grid(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        kind = row[0]
        if kind == "option":
            label_text, widget = row[1], row[2]
            tooltip = row[3] if len(row) > 3 else ""
            label = QLabel(label_text)
            label.setFixedWidth(TOGGLE_TEXT_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)
            tune_form_widget(widget)
            layout.addWidget(label, row_index, 0)
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
            layout.addWidget(widget, row_index, 2)
            continue

        checkbox, text = row[1], row[2]
        tooltip = row[3] if len(row) > 3 else ""
        param_label = row[4] if len(row) > 4 else None
        param_widget = row[5] if len(row) > 5 else None
        checkbox.setText(text)
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(param_label)
            label.setObjectName("inlineParamLabel")
            label.setFixedWidth(INLINE_LABEL_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
            layout.addWidget(label, row_index, 1)
        else:
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
        if param_widget is not None:
            tune_form_widget(param_widget)
            layout.addWidget(param_widget, row_index, 2)
        else:
            layout.addItem(QSpacerItem(FORM_FIELD_MIN_WIDTH, FORM_CONTROL_HEIGHT), row_index, 2)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 1)
    return wrapper


def build_parameter_section_grid(rows) -> QWidget:
    wrapper = QWidget()
    layout = QGridLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)
    for row_index, row in enumerate(rows):
        kind = row[0]
        if kind == "option":
            label_text, widget = row[1], row[2]
            tooltip = row[3] if len(row) > 3 else ""
            label = QLabel(label_text)
            label.setFixedWidth(TOGGLE_TEXT_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
                widget.setToolTip(tooltip)
            tune_form_widget(widget)
            layout.addWidget(label, row_index, 0)
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
            layout.addWidget(widget, row_index, 2)
            continue

        checkbox, text = row[1], row[2]
        tooltip = row[3] if len(row) > 3 else ""
        param_label = row[4] if len(row) > 4 else None
        param_widget = row[5] if len(row) > 5 else None
        checkbox.setText(text)
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(param_label)
            label.setObjectName("inlineParamLabel")
            label.setFixedWidth(INLINE_LABEL_WIDTH)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if tooltip:
                label.setToolTip(tooltip)
            layout.addWidget(label, row_index, 1)
        else:
            layout.addItem(QSpacerItem(INLINE_LABEL_WIDTH, FORM_CONTROL_HEIGHT), row_index, 1)
        if param_widget is not None:
            tune_form_widget(param_widget)
            layout.addWidget(param_widget, row_index, 2)
        else:
            layout.addItem(QSpacerItem(FORM_FIELD_MIN_WIDTH, FORM_CONTROL_HEIGHT), row_index, 2)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 0)
    layout.setColumnStretch(2, 0)
    layout.setColumnStretch(3, 1)
    return wrapper


def build_page_header(title: str, subtitle: str) -> QWidget:
    header = QWidget()
    header.setFixedHeight(64)
    layout = QVBoxLayout(header)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("pageTitle")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("pageSubtitle")
    separator = QFrame()
    separator.setObjectName("sectionSeparator")
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    layout.addStretch(1)
    layout.addWidget(separator)
    header.title_label = title_label
    header.subtitle_label = subtitle_label
    return header


def tune_form_widget(widget: QWidget) -> None:
    if isinstance(widget, QCheckBox):
        widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
        if widget.text():
            widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        else:
            widget.setFixedWidth(24)
            widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return
    if isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
        widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
        widget.setMinimumWidth(FORM_FIELD_MIN_WIDTH)
        widget.setMaximumWidth(FORM_FIELD_MAX_WIDTH)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def tune_skill_widget(widget: QWidget, role: str) -> None:
    if isinstance(widget, QCheckBox):
        widget.setFixedWidth(28)
        widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
        return
    if not isinstance(widget, (QLineEdit, QComboBox, QSpinBox)):
        return
    widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
    if role == "action":
        widget.setFixedWidth(SKILL_ACTION_WIDTH)
        return
    width = SKILL_NUMBER_WIDTH
    if role == "hotkey":
        width = SKILL_TEXT_WIDTH
    elif role == "triggerbutton":
        width = SKILL_TRIGGER_WIDTH
    widget.setFixedWidth(width)


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


# Column weight ratios (pixels at baseline window size — distributed proportionally)
_SKILL_COL_WEIGHTS = [50, 68, 118, 60, 60, 54, 60, 60, 86, 72]
_SKILL_COL_TOTAL = sum(_SKILL_COL_WEIGHTS)


class _SkillColumnDistributor(QObject):
    """Proportionally fills all skill table columns to the viewport width on resize."""

    def __init__(self, table: QTableWidget) -> None:
        super().__init__(table.viewport())
        self._table = table
        table.viewport().installEventFilter(self)
        self._distribute()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self._distribute()
        return False

    def _distribute(self) -> None:
        avail = self._table.viewport().width()
        if avail < 200:
            return
        remainder = avail
        for i, w in enumerate(_SKILL_COL_WEIGHTS[:-1]):
            col_w = max(40, int(avail * w / _SKILL_COL_TOTAL))
            self._table.setColumnWidth(i, col_w)
            remainder -= col_w
        self._table.setColumnWidth(len(_SKILL_COL_WEIGHTS) - 1, max(40, remainder))


class ProfileTab(QWidget):
    def __init__(self, section_name: str, section: configparser.SectionProxy) -> None:
        super().__init__()
        self.setObjectName("pageContainer")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.widgets: dict[str, object] = {}
        self.section_name = section_name
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        self.page_header_title = section_name
        self.page_header = build_page_header(
            self.page_header_title,
            tr("配置档基础选项与技能策略", "Profile basics and skill strategies."),
        )
        self.page_header.setFixedHeight(46)
        root.addWidget(self.page_header)

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

        settings_columns = QHBoxLayout()
        settings_columns.setContentsMargins(0, 0, 0, 0)
        settings_columns.setSpacing(32)
        settings_left = QVBoxLayout()
        settings_left.setSpacing(16)
        settings_right = QVBoxLayout()
        settings_right.setSpacing(16)
        settings_columns.addLayout(settings_left, 1)
        settings_columns.addLayout(settings_right, 1)
        root.addLayout(settings_columns)

        basics_section, basics_layout = build_section(tr("基础", "Basics"))
        basics_layout.addWidget(
            build_option_grid(
                [
                    ("配置名", self.widgets["name"]),
                    ("宏启动方式", self.widgets["lazymode"], START_MODE_TOOLTIP),
                    ("切换类型", self.widgets["profilehkmethod"], PROFILE_HOTKEY_TOOLTIP),
                    ("切换按键", self.widgets["profilehkkey"], PROFILE_HOTKEY_TOOLTIP),
                ]
            )
        )
        basics_layout.addWidget(
            build_toggle_grid(
                [
                    (self.widgets["autostartmarco"], "切换后自动启动宏", AUTOSTART_TOOLTIP),
                ]
            )
        )
        settings_left.addWidget(basics_section)

        movement_section, movement_layout = build_section(tr("走位与药水", "Movement & Potion"))
        movement_layout.addWidget(
            build_option_grid(
                [
                    ("走位辅助", self.widgets["movingmethod"]),
                    ("走位间隔", self.widgets["movinginterval"]),
                    ("药水辅助", self.widgets["potionmethod"], POTION_TOOLTIP),
                    ("药水间隔", self.widgets["potioninterval"]),
                ]
            )
        )
        settings_left.addWidget(movement_section)
        settings_left.addStretch(1)

        queue_section, queue_layout = build_section(tr("按键队列", "Skill Queue"))
        queue_layout.addWidget(
            build_helper_section_grid(
                [
                    ("toggle", self.widgets["useskillqueue"], "单线程按键队列", SKILL_QUEUE_TOOLTIP, "间隔", self.widgets["useskillqueueinterval"]),
                ]
            )
        )
        settings_right.addWidget(queue_section)

        pause_section, pause_layout = build_section(tr("快速暂停", "Quick Pause"))
        pause_layout.addWidget(
            build_helper_section_grid(
                [
                    ("toggle", self.widgets["enablequickpause"], "启用快速暂停", ""),
                    ("option", "暂停触发", self.widgets["quickpausemethod1"]),
                    ("option", "暂停按键", self.widgets["quickpausemethod2"]),
                    ("option", "暂停动作", self.widgets["quickpausemethod3"]),
                    ("option", "暂停时长", self.widgets["quickpausedelay"]),
                ]
            )
        )
        settings_right.addWidget(pause_section)
        settings_right.addStretch(1)

        skill_section, skill_layout = build_section(tr("技能表", "Skill table"))
        self.skill_table = QTableWidget(6, 10)
        self.skill_table.viewport().setStyleSheet("background: transparent;")
        self.skill_table.setHorizontalHeaderLabels(
            [
                tr("槽位", "Slot"),
                tr("按键", "Key"),
                tr("策略", "Action"),
                tr("间隔", "Interval"),
                tr("延迟", "Delay"),
                tr("随机", "Random"),
                tr("优先级", "Priority"),
                tr("重复", "Repeat"),
                tr("重复间隔", "Repeat gap"),
                tr("触发", "Trigger"),
            ]
        )
        self.skill_table.verticalHeader().setVisible(False)
        self.skill_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.skill_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.skill_table.setShowGrid(True)
        self.skill_table.setAlternatingRowColors(True)
        self.skill_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.skill_table.horizontalHeader().setStretchLastSection(False)
        self.skill_table.horizontalHeader().setDefaultSectionSize(SKILL_NUMBER_WIDTH)
        self.skill_table.horizontalHeader().setMinimumSectionSize(40)
        self.skill_table.horizontalHeader().setFixedHeight(SKILL_TABLE_HEADER_HEIGHT)
        self.skill_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.skill_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.skill_table.verticalScrollBar().setEnabled(False)
        self.skill_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.skill_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for row_index in range(6):
            self.skill_table.setRowHeight(row_index, SKILL_TABLE_ROW_HEIGHT)
        self.skill_table.setFixedHeight(SKILL_TABLE_HEADER_HEIGHT + SKILL_TABLE_ROW_HEIGHT * 6 + 4)
        self._col_distributor = _SkillColumnDistributor(self.skill_table)

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
            for key in ["hotkey", "action", "interval", "delay", "random", "priority", "repeat", "repeatinterval", "triggerbutton"]:
                tune_skill_widget(row[key], key)
            if index in {5, 6}:
                row["hotkey"].setReadOnly(True)
            slot_item = QTableWidgetItem(tr(f"技能{index}", f"Skill {index}"))
            slot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.skill_table.setItem(index - 1, 0, slot_item)
            self.skill_table.setCellWidget(index - 1, 1, row["hotkey"])
            self.skill_table.setCellWidget(index - 1, 2, row["action"])
            self.skill_table.setCellWidget(index - 1, 3, row["interval"])
            self.skill_table.setCellWidget(index - 1, 4, row["delay"])
            random_wrapper = QWidget()
            random_layout = QHBoxLayout(random_wrapper)
            random_layout.setContentsMargins(0, 0, 0, 0)
            random_layout.setSpacing(0)
            random_layout.addStretch()
            random_layout.addWidget(row["random"])
            random_layout.addStretch()
            self.skill_table.setCellWidget(index - 1, 5, random_wrapper)
            self.skill_table.setCellWidget(index - 1, 6, row["priority"])
            self.skill_table.setCellWidget(index - 1, 7, row["repeat"])
            self.skill_table.setCellWidget(index - 1, 8, row["repeatinterval"])
            self.skill_table.setCellWidget(index - 1, 9, row["triggerbutton"])
            skill_widgets.append(row)
        self.skill_table.setColumnWidth(0, 50)   # 槽位
        self.skill_table.setColumnWidth(1, SKILL_TEXT_WIDTH)    # 按键
        self.skill_table.setColumnWidth(2, SKILL_ACTION_WIDTH)  # 策略 (fixed)
        self.skill_table.setColumnWidth(3, SKILL_NUMBER_WIDTH)  # 间隔
        self.skill_table.setColumnWidth(4, SKILL_NUMBER_WIDTH)  # 延迟
        self.skill_table.setColumnWidth(5, 54)   # 随机
        self.skill_table.setColumnWidth(6, SKILL_NUMBER_WIDTH)  # 优先级
        self.skill_table.setColumnWidth(7, SKILL_NUMBER_WIDTH)  # 重复
        self.skill_table.setColumnWidth(8, 86)   # 重复间隔
        self.skill_table.setColumnWidth(9, SKILL_TRIGGER_WIDTH) # 触发
        self.widgets["skills"] = skill_widgets
        self.skill_queue_warning = QLabel(
            tr(
                "注意：当前按键队列可能跟不上连点技能的入队速度",
                "Warning: the single-threaded skill queue may be slower than the spam inputs.",
            )
        )
        self.skill_queue_warning.setStyleSheet("color: #c62828;")
        self.skill_queue_warning.hide()
        skill_layout.addWidget(self.skill_table)
        skill_layout.addWidget(self.skill_queue_warning)
        root.addWidget(skill_section)
        root.addStretch(1)
        self._start_method_conflict = False
        self._connect_dynamic_controls()
        self.refresh_dynamic_state()

    def _combo(self, items, value: int) -> QComboBox:
        combo = QComboBox()
        tune_combo_box(combo)
        for data, text in items:
            combo.addItem(text, data)
        set_combo_value(combo, value)
        return combo

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
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
        self.profile_nav_items: list[QListWidgetItem] = []
        self._last_log_line = tr("尚无日志。", "No log messages yet.")
        self._path_text = str(self.config_path)
        self._log_expanded = False
        self._suspend_config_watch = False
        self._config_apply_timer = QTimer(self)
        self._config_apply_timer.setSingleShot(True)
        self._config_apply_timer.setInterval(500)
        self._config_apply_timer.timeout.connect(self._apply_live_config_change)
        self.navigation = QListWidget()
        self.page_stack = QStackedWidget()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        self.setWindowTitle("D3keyHelper Linux")
        self.setStyleSheet(APP_STYLE_SHEET)
        self.resize(*FULL_WINDOW_SIZE)
        self.setMinimumSize(960, 620)
        self._build_shell()
        self.reload_config()

    def _build_shell(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.root_layout = layout
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbarFrame")
        toolbar_frame.setFixedHeight(44)
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)
        self.toolbar_layout = toolbar
        self.path_label = QLabel()
        self.path_label.setObjectName("pathLabel")
        self.path_label.setMinimumWidth(TOOLBAR_PATH_MIN_WIDTH)
        self.path_label.setMaximumWidth(TOOLBAR_PATH_MAX_WIDTH)
        self.path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        reload_button = QPushButton(tr("重新载入", "Reload"))
        reload_button.clicked.connect(self.reload_config)
        save_button = QPushButton(tr("保存配置", "Save"))
        save_button.clicked.connect(self.save_config)
        start_button = QPushButton(tr("启动", "Start"))
        start_button.setObjectName("primaryButton")
        start_button.clicked.connect(self.start_runner)
        stop_button = QPushButton(tr("停止", "Stop"))
        stop_button.clicked.connect(lambda _checked=False: self.stop_runner())
        toolbar.addWidget(self.path_label)
        toolbar.addStretch(1)
        profile_label = QLabel(tr("激活配置:", "Profile:"))
        profile_label.setObjectName("toolbarLabel")
        self.toolbar_profile_combo = QComboBox()
        tune_combo_box(self.toolbar_profile_combo)
        self.toolbar_profile_combo.setFixedWidth(140)
        self.toolbar_profile_combo.setToolTip(tr("当前激活配置", "Active profile"))
        toolbar.addWidget(profile_label)
        toolbar.addWidget(self.toolbar_profile_combo)
        toolbar.addWidget(reload_button)
        toolbar.addWidget(save_button)
        toolbar.addWidget(start_button)
        toolbar.addWidget(stop_button)
        layout.addWidget(toolbar_frame)
        self.navigation.setObjectName("navigationList")
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.navigation.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.navigation.setSpacing(2)
        self.navigation.setFixedWidth(NAV_WIDTH)
        self.navigation.currentRowChanged.connect(self._select_page)
        content_widget = QFrame()
        content_widget.setObjectName("contentPanel")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 18, 24, 0)
        content_layout.setSpacing(8)
        self.content_layout = content_layout
        self.log_panel = QFrame()
        self.log_panel.setObjectName("logPanel")
        log_layout = QVBoxLayout(self.log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(4)
        self.log_panel_title = QLabel(tr("运行日志", "Runner log"))
        self.log_panel_title.setObjectName("sectionHint")
        log_layout.addWidget(self.log_panel_title)
        log_layout.addWidget(self.log)
        content_layout.addWidget(self.page_stack, 1)
        content_layout.addWidget(self.log_panel)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.navigation)
        splitter.addWidget(content_widget)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([NAV_WIDTH, FULL_WINDOW_SIZE[0] - NAV_WIDTH])
        self.body_splitter = splitter
        layout.addWidget(splitter, 1)
        self.status_strip = QFrame()
        self.status_strip.setObjectName("statusStrip")
        self.status_strip.setFixedHeight(34)
        status_layout = QHBoxLayout(self.status_strip)
        status_layout.setContentsMargins(10, 4, 12, 4)
        status_layout.setSpacing(8)
        self.status_strip_layout = status_layout
        self.status_dot = QFrame()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(10, 10)
        self.status_runner_label = QLabel()
        self.status_runner_label.setObjectName("statusStripLabel")
        self.status_log_title = QLabel(tr("最近日志", "Latest log"))
        self.status_log_title.setObjectName("statusStripLabel")
        self.status_log_value = QLabel()
        self.status_log_value.setObjectName("statusStripValue")
        self.status_log_value.setMinimumWidth(0)
        self.status_log_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.log_toggle_button = QPushButton(tr("展开日志", "Show Log"))
        self.log_toggle_button.setCheckable(True)
        self.log_toggle_button.setFixedHeight(24)
        self.log_toggle_button.setMinimumWidth(76)
        self.log_toggle_button.toggled.connect(self._set_log_expanded)
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_runner_label)
        status_layout.addSpacing(16)
        status_layout.addWidget(self.status_log_title)
        status_layout.addWidget(self.status_log_value, 1)
        status_layout.addWidget(self.log_toggle_button)
        layout.addWidget(self.status_strip)
        self.setCentralWidget(central)
        self._set_log_expanded(False)
        self._update_path_label()
        self._update_runtime_status_widgets()

    def _select_page(self, index: int) -> None:
        if 0 <= index < self.page_stack.count():
            self.page_stack.setCurrentIndex(index)

    def _clear_page_stack(self) -> None:
        while self.page_stack.count():
            widget = self.page_stack.widget(0)
            self.page_stack.removeWidget(widget)
            widget.deleteLater()

    def reload_config(self) -> None:
        self._config_apply_timer.stop()
        self._suspend_config_watch = True
        parser = load_parser(self.config_path)
        self.navigation.clear()
        self._clear_page_stack()
        self.general_widgets.clear()
        self.profile_tabs.clear()
        self.profile_nav_items.clear()
        self._path_text = str(self.config_path)
        self._update_path_label()
        self._append_log(tr(f"已载入配置：{self.config_path}", f"Loaded config: {self.config_path}"))
        general_name = next(name for name in parser.sections() if name.lower() == "general")
        profile_names = [name for name in parser.sections() if name.lower() != "general"]
        self.navigation.addItem(QListWidgetItem(tr("通用", "General")))
        self.page_stack.addWidget(self._build_general_tab(parser[general_name], profile_names))
        for name in profile_names:
            tab = ProfileTab(name, parser[name])
            self.profile_tabs.append(tab)
            item = QListWidgetItem(name)
            self.profile_nav_items.append(item)
            self.navigation.addItem(item)
            self.page_stack.addWidget(self._wrap_scroll_tab(tab))
        self.navigation.setCurrentRow(0)
        self._refresh_general_state()
        self._connect_config_change_watchers()
        self._suspend_config_watch = False
        self._update_runtime_status_widgets()
        self._sync_toolbar_profile_combo(profile_names)

    def _sync_toolbar_profile_combo(self, profile_names: list[str]) -> None:
        """Populate toolbar profile combo and wire it to the General tab's activatedprofile widget."""
        general_combo = self.general_widgets.get("activatedprofile")
        combo = self.toolbar_profile_combo
        combo.blockSignals(True)
        combo.clear()
        count = max(len(profile_names), 1)
        for index in range(1, count + 1):
            name = profile_names[index - 1] if index <= len(profile_names) else f"配置{index}"
            combo.addItem(f"{index} - {name}", index)
        if general_combo is not None:
            set_combo_value(combo, combo_value(general_combo))
        combo.blockSignals(False)
        if general_combo is not None:
            if getattr(self, "_toolbar_profile_synced", False):
                try:
                    combo.currentIndexChanged.disconnect()
                except Exception:
                    pass
                try:
                    general_combo.currentIndexChanged.disconnect(self._on_general_profile_changed)
                except Exception:
                    pass
            self._toolbar_profile_synced = True
            combo.currentIndexChanged.connect(
                lambda _: set_combo_value(general_combo, combo_value(combo))
            )
            general_combo.currentIndexChanged.connect(self._on_general_profile_changed)

    def _on_general_profile_changed(self) -> None:
        general_combo = self.general_widgets.get("activatedprofile")
        if general_combo is None:
            return
        self.toolbar_profile_combo.blockSignals(True)
        set_combo_value(self.toolbar_profile_combo, combo_value(general_combo))
        self.toolbar_profile_combo.blockSignals(False)

    def _build_general_tab(self, section: configparser.SectionProxy, profile_names: list[str]) -> QWidget:
        container = QWidget()
        container.setObjectName("pageContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        helper_speed_preset = helper_speed_preset_from_values(
            int(section.get("helpermousespeed", "2")),
            int(section.get("helperanimationdelay", "150")),
            int(section.get("helperspeed", "3")),
        )
        root.addWidget(
            build_page_header(
                tr("通用设置", "General settings"),
                tr("编辑全局热键、助手行为、输入方式与高级参数", "Edit global hotkeys, helper behavior, input mode, and advanced options."),
            )
        )
        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(32)
        root.addLayout(columns)

        self.general_widgets["activatedprofile"] = build_profile_selector(profile_names, int(section.get("activatedprofile", "1")))
        self.general_widgets["startmethod"] = self._combo(START_METHOD_ITEMS, int(section.get("startmethod", "7")))
        self.general_widgets["starthotkey"] = QLineEdit(section.get("starthotkey", "F2"))
        self.general_widgets["oldsandhelpermethod"] = self._combo(COMMON_METHOD_ITEMS, int(section.get("oldsandhelpermethod", "7")))
        self.general_widgets["oldsandhelperhk"] = QLineEdit(section.get("oldsandhelperhk", "F5"))
        self.general_widgets["sendmode"] = self._combo(SEND_MODE_ITEMS, section.get("sendmode", "Event"))
        self.general_widgets["runonstart"] = self._check(section.get("runonstart", "1") == "1")
        self.general_widgets["d3only"] = self._check(section.get("d3only", "1") == "1")
        self.general_widgets["enablesmartpause"] = self._check(section.get("enablesmartpause", "1") == "1")
        self.general_widgets["enablesoundplay"] = self._check(section.get("enablesoundplay", "1") == "1")
        self.general_widgets["gameresolution"] = QLineEdit(section.get("gameresolution", "Auto"))
        self.general_widgets["gamegamma"] = self._float_spin(0.5, 1.5, float(section.get("gamegamma", "1.0")), 6)
        self.general_widgets["buffpercent"] = self._float_spin(0.0, 1.0, float(section.get("buffpercent", "0.05")), 6)
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
        self.general_widgets["enablegamblehelper"].setToolTip(GAMBLE_TOOLTIP)
        self.general_widgets["gamblehelpertimes"].setToolTip(GAMBLE_TOOLTIP)
        self.general_widgets["enableloothelper"].setToolTip(LOOT_TOOLTIP)
        self.general_widgets["loothelpertimes"].setToolTip(LOOT_TOOLTIP)
        self.general_widgets["enablesalvagehelper"].setToolTip(SALVAGE_ENABLE_TOOLTIP)
        self.general_widgets["salvagehelpermethod"].setToolTip(SALVAGE_METHOD_TOOLTIP)
        self.general_widgets["enablereforgehelper"].setToolTip(make_reforge_method_tooltip(self.general_widgets["maxreforge"].value()))
        self.general_widgets["reforgehelpermethod"].setToolTip(make_reforge_method_tooltip(self.general_widgets["maxreforge"].value()))
        self.general_widgets["enableupgradehelper"].setToolTip(UPGRADE_TOOLTIP)
        self.general_widgets["enableconverthelper"].setToolTip(CONVERT_TOOLTIP)
        self.general_widgets["enableabandonhelper"].setToolTip(ABANDON_TOOLTIP)
        self.general_widgets["helperspeed"].currentIndexChanged.connect(self._apply_helper_speed_preset)
        self.general_widgets["helpermousespeed"].valueChanged.connect(self._sync_helper_speed_preset)
        self.general_widgets["helperanimationdelay"].valueChanged.connect(self._sync_helper_speed_preset)
        basic_section, basic_layout = build_section(tr("基础", "Basics"))
        basic_layout.addWidget(
            build_option_grid(
                [
                    ("当前激活配置", self.general_widgets["activatedprofile"]),
                    ("战斗宏启动方式", self.general_widgets["startmethod"]),
                    ("战斗宏启动热键", self.general_widgets["starthotkey"]),
                    ("助手启动方式", self.general_widgets["oldsandhelpermethod"], HELPER_HOTKEY_TOOLTIP),
                    ("助手启动热键", self.general_widgets["oldsandhelperhk"], HELPER_HOTKEY_TOOLTIP),
                    ("发送模式", self.general_widgets["sendmode"], SEND_MODE_TOOLTIP),
                    ("游戏分辨率", self.general_widgets["gameresolution"], GAME_RESOLUTION_TOOLTIP),
                    ("游戏 Gamma", self.general_widgets["gamegamma"], GAME_GAMMA_TOOLTIP),
                    ("Buff 续按阈值", self.general_widgets["buffpercent"], BUFF_PERCENT_TOOLTIP),
                ]
            )
        )
        basic_layout.addWidget(
            build_toggle_grid(
                [
                    (self.general_widgets["runonstart"], "宏启动瞬间执行一次", RUN_ON_START_TOOLTIP),
                    (self.general_widgets["d3only"], "只作用于 Diablo III 前台窗口", ""),
                    (self.general_widgets["enablesmartpause"], "智能暂停", SMART_PAUSE_TOOLTIP),
                    (self.general_widgets["enablesoundplay"], "切换配置提示音", SOUND_ON_SWITCH_TOOLTIP),
                ]
            )
        )
        basic_layout.addStretch(1)
        columns.addWidget(basic_section, 1)

        input_section, input_layout = build_section(tr("助手/输入", "Helpers / Input"))
        input_layout.addWidget(
            build_toggle_grid(
                [
                    (self.general_widgets["customstanding"], "自定义强制站立", CUSTOM_STANDING_TOOLTIP, "按键", self.general_widgets["customstandinghk"]),
                    (self.general_widgets["custommoving"], "自定义强制移动", CUSTOM_MOVING_TOOLTIP, "按键", self.general_widgets["custommovinghk"]),
                    (self.general_widgets["custompotion"], "自定义药水按键", CUSTOM_POTION_TOOLTIP, "按键", self.general_widgets["custompotionhk"]),
                ]
            )
        )
        input_layout.addWidget(
            build_helper_list(
                [
                    (self.general_widgets["enablegamblehelper"], "赌博助手", GAMBLE_TOOLTIP, "点击次数", self.general_widgets["gamblehelpertimes"]),
                    (self.general_widgets["enableloothelper"], "拾取助手", LOOT_TOOLTIP, "点击次数", self.general_widgets["loothelpertimes"]),
                    (self.general_widgets["enablesalvagehelper"], "分解助手", SALVAGE_ENABLE_TOOLTIP, "分解策略", self.general_widgets["salvagehelpermethod"]),
                    (
                        self.general_widgets["enablereforgehelper"],
                        "重铸助手",
                        make_reforge_method_tooltip(self.general_widgets["maxreforge"].value()),
                        "重铸策略",
                        self.general_widgets["reforgehelpermethod"],
                    ),
                    (self.general_widgets["enableupgradehelper"], "升级助手", UPGRADE_TOOLTIP),
                    (self.general_widgets["enableconverthelper"], "转化助手", CONVERT_TOOLTIP),
                    (self.general_widgets["enableabandonhelper"], "丢装助手", ABANDON_TOOLTIP),
                ]
            )
        )
        input_layout.addWidget(
            build_option_grid(
                [
                    ("动画速度预设", self.general_widgets["helperspeed"], HELPER_SPEED_PRESET_TOOLTIP),
                    ("辅助鼠标速度", self.general_widgets["helpermousespeed"], HELPER_SPEED_TOOLTIP),
                    ("辅助动画延迟", self.general_widgets["helperanimationdelay"], HELPER_SPEED_TOOLTIP),
                    ("安全格", self.general_widgets["safezone"], SAFEZONE_TOOLTIP),
                    ("最大重铸次数", self.general_widgets["maxreforge"]),
                ]
            )
        )
        input_layout.addWidget(self.general_widgets["safezonestatus"])
        input_layout.addStretch(1)
        columns.addWidget(input_section, 1)
        self.general_widgets["maxreforge"].valueChanged.connect(self._sync_reforge_tooltip)
        self._sync_reforge_tooltip()
        self._sync_helper_speed_preset()
        self._connect_general_dynamic_controls()
        self._refresh_general_state()
        root.addStretch(1)
        self._update_runtime_status_widgets()
        return self._wrap_scroll_tab(container)

    def _wrap_scroll_tab(self, widget: QWidget) -> QScrollArea:
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setFrameShape(QFrame.Shape.NoFrame)
        tab.setWidget(widget)
        tab.viewport().setAutoFillBackground(False)
        return tab

    def _combo(self, items, value: int) -> QComboBox:
        combo = QComboBox()
        tune_combo_box(combo)
        for data, text in items:
            combo.addItem(text, data)
        set_combo_value(combo, value)
        return combo

    def _spin(self, minimum: int, maximum: int, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        return widget

    def _float_spin(self, minimum: float, maximum: float, value: float, decimals: int) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
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

    def _append_log(self, text: str) -> None:
        message = text.rstrip()
        if not message:
            return
        self.log.appendPlainText(message)
        self._last_log_line = message.splitlines()[-1]
        self._update_runtime_status_widgets()

    def _set_log_expanded(self, expanded: bool) -> None:
        self._log_expanded = expanded
        self.log_toggle_button.blockSignals(True)
        self.log_toggle_button.setChecked(expanded)
        self.log_toggle_button.blockSignals(False)
        self.log_toggle_button.setText(tr("收起日志", "Hide Log") if expanded else tr("展开日志", "Show Log"))
        self.log_panel.setVisible(expanded)

    def _update_path_label(self) -> None:
        available = self.path_label.width()
        if available <= 0:
            available = TOOLBAR_PATH_MAX_WIDTH - 24
        text = self.path_label.fontMetrics().elidedText(
            self._path_text,
            Qt.TextElideMode.ElideMiddle,
            max(available - 12, 120),
        )
        self.path_label.setText(text)
        self.path_label.setToolTip(self._path_text)

    def _update_runtime_status_widgets(self) -> None:
        running = self._runner_is_active()
        runner_text = tr("运行中", "Running") if running else tr("未运行", "Stopped")
        latest_text = self._last_log_line
        self.status_dot.setProperty("running", running)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.status_runner_label.setText(runner_text)
        available = self.status_log_value.width()
        if available <= 0:
            available = 420
        log_text = self.status_log_value.fontMetrics().elidedText(
            latest_text,
            Qt.TextElideMode.ElideRight,
            max(available - 6, 120),
        )
        self.status_log_value.setText(log_text)
        self.status_log_value.setToolTip(latest_text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_path_label()
        self._update_runtime_status_widgets()

    def save_config(self, log_message: str = "已保存配置。") -> None:
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str.lower
        parser["General"] = {
            "version": DEFAULT_VERSION,
            "activatedprofile": str(combo_value(self.general_widgets["activatedprofile"])),
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
            "compactmode": "0",
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

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-16") as handle:
            handle.write("; Linux GUI config for D3keyHelper\r\n")
            parser.write(handle)
        if log_message:
            self._append_log(log_message)
        for item, tab in zip(self.profile_nav_items, self.profile_tabs):
            title = tab.widgets["name"].text().strip() or tab.section_name
            item.setText(title)
            if hasattr(tab, "page_header") and hasattr(tab.page_header, "title_label"):
                tab.page_header.title_label.setText(title)

    def start_runner(self) -> None:
        self._launch_runner(save_first=True, log_message="已启动运行器。")

    def _launch_runner(self, save_first: bool, log_message: str) -> None:
        self._config_apply_timer.stop()
        if save_first:
            self.save_config()
        self.stop_runner(log_message=None)
        command = build_runner_command(self.config_path, "")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_process_output)
        self.process.finished.connect(self._runner_finished)
        self.process.start(command[0], command[1:])
        if not self.process.waitForStarted(5000):
            QMessageBox.critical(self, tr("启动失败", "Start failed"), tr("无法启动 Linux 运行器。", "Failed to start the Linux runner."))
            self.process = None
            self._update_runtime_status_widgets()
            return
        if log_message:
            self._append_log(log_message)
        else:
            self._update_runtime_status_widgets()

    def stop_runner(self, log_message: str | None = "已停止运行器。") -> None:
        if self.process is None:
            return
        finished = self.process.finished
        try:
            finished.disconnect(self._runner_finished)
        except Exception:
            pass
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()
            self.process.waitForFinished(1000)
        if log_message:
            self._append_log(log_message)
        self.process = None
        self._update_runtime_status_widgets()

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
            self._append_log(text)

    def _runner_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        if exit_status == QProcess.ExitStatus.NormalExit:
            self._append_log(tr(f"运行器已退出，返回码：{exit_code}", f"Runner exited with code: {exit_code}"))
        else:
            self._append_log(tr(f"运行器异常退出，返回码：{exit_code}", f"Runner crashed with code: {exit_code}"))
        self.process = None
        self._update_runtime_status_widgets()

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
    config_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else default_config_path().resolve()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon_path = app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow(config_path)
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
