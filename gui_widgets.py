from __future__ import annotations
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import io as _io
_stdout_backup = sys.stdout
sys.stdout = _io.StringIO()
from qfluentwidgets import (  # noqa: E402
    ComboBox as FluentComboBox,
    LineEdit,
)
sys.stdout = _stdout_backup
del _stdout_backup, _io

try:
    from .gui_i18n import tr, localize_text
except ImportError:
    from gui_i18n import tr, localize_text  # type: ignore[no-redef]

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
    background: #f0f2f5;
}
QScrollArea {
    border: none;
    background: transparent;
}
QListWidget#navigationList {
    background: #f9fafb;
    border: none;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget#navigationList::item {
    padding: 4px 12px;
    margin: 1px 0;
    border-radius: 6px;
    color: #333333;
    font-size: 13px;
}
QListWidget#navigationList::item:hover {
    background: rgba(0, 0, 0, 0.05);
}
QListWidget#navigationList::item:selected {
    background: #e8f0fe;
    color: #1a73e8;
    font-weight: 600;
}
QWidget#navSidebar {
    background: transparent;
}
QFrame#navActions {
    background: transparent;
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
QFrame#langSwitcher {
    border: 1px solid #d0d5dc;
    border-radius: 5px;
    background: transparent;
}
QPushButton#langButton {
    border: none;
    background: transparent;
    color: #48566a;
    font-size: 12px;
    font-weight: 500;
    padding: 0 6px;
    min-width: 28px;
    min-height: 22px;
    border-radius: 4px;
}
QPushButton#langButton:checked {
    background: #3b6fe8;
    color: #ffffff;
}
QPushButton#langButton:hover:!checked {
    background: #eef1f5;
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
    background: #f8faff;
    alternate-background-color: #eef3fc;
    border: 1px solid #c8d6f0;
    border-radius: 6px;
    gridline-color: #dce8f7;
    selection-background-color: #cfe0fc;
    selection-color: #1a3a6b;
}
QHeaderView::section {
    background: #dce8f7;
    color: #1a3a6b;
    border: none;
    border-right: 1px solid #c8d6f0;
    border-bottom: 2px solid #2f72c4;
    padding: 4px 6px;
    font-weight: 600;
}
QHeaderView::section:last {
    border-right: none;
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
TOGGLE_TEXT_WIDTH = 180
INLINE_LABEL_WIDTH = 110

TOOLBAR_PATH_MIN_WIDTH = 80
TOOLBAR_PATH_MAX_WIDTH = 160
NAV_WIDTH = 150
NAV_ACTION_MARGIN = 6
SKILL_TEXT_WIDTH = 84
SKILL_TRIGGER_WIDTH = 84
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
    return localize_text(
        "重铸一次：重铸鼠标指针处的装备一次\n"
        f"重铸到远古/太古：不停重铸鼠标指针处的装备，直到变为远古或者太古装备，最多重铸{max_reforge}次\n"
        f"重铸到太古：不停重铸鼠标指针处的装备，直到变成太古装备，最多重铸{max_reforge}次\n"
        "***重铸过程中再次按下助手快捷键可以打断宏！***"
    )


def set_combo_value(combo: QComboBox, value) -> None:
    index = combo.findData(value)
    combo.setCurrentIndex(index if index >= 0 else 0)


def _make_line_edit(text: str = "") -> LineEdit:
    w = LineEdit()
    w.setText(text)
    return w


def _add_combo_item(combo, text: str, data) -> None:
    if isinstance(combo, FluentComboBox):
        combo.addItem(text, userData=data)
    else:
        combo.addItem(text, data)


def tune_combo_box(combo):
    if isinstance(combo, QComboBox):
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


def build_profile_selector(profile_names: list[str], active_profile: int) -> FluentComboBox:
    combo = FluentComboBox()
    tune_combo_box(combo)
    count = max(len(profile_names), active_profile, 1)
    for index in range(1, count + 1):
        name = profile_names[index - 1] if index <= len(profile_names) else tr(f"配置{index}", f"Profile {index}")
        combo.addItem(f"{index} - {localize_text(name)}", userData=index)
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
        tooltip = localize_text(tooltip)
        label_widget = QLabel(localize_text(label))
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
            tooltip = localize_text(tooltip)
            if tooltip:
                widget.setToolTip(tooltip)
            layout.addRow(widget)
            continue
        tooltip = localize_text(tooltip)
        label_widget = QLabel(localize_text(label))
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
    title_label = QLabel(localize_text(title))
    title_label.setObjectName("sectionTitle")
    layout.addWidget(title_label)
    if hint:
        hint_label = QLabel(localize_text(hint))
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
    label = QLabel(localize_text(text))
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
    tooltip = localize_text(tooltip)
    checkbox.setText(localize_text(text))
    if tooltip:
        checkbox.setToolTip(tooltip)
    widgets: list[QWidget] = [checkbox]
    if trailing_label:
        label = QLabel(localize_text(trailing_label))
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
        tooltip = localize_text(tooltip)
        checkbox.setText(localize_text(text))
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        if tooltip:
            checkbox.setToolTip(tooltip)
        if trailing_label or trailing_widget is not None:
            # Row has trailing param: fix checkbox width so param columns align across rows
            checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
            checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout.addWidget(checkbox, row_index, 0)
            if trailing_label:
                label = QLabel(localize_text(trailing_label))
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
        tooltip = localize_text(tooltip)
        label = QLabel(localize_text(label_text))
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
        tooltip = localize_text(tooltip)
        label = QLabel(localize_text(label_text))
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
            trailing_label = QLabel(localize_text(param_label))
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
        tooltip = localize_text(tooltip)
        checkbox.setText(localize_text(text))
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(localize_text(param_label))
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
            tooltip = localize_text(tooltip)
            label = QLabel(localize_text(label_text))
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
        tooltip = localize_text(tooltip)
        checkbox.setText(localize_text(text))
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(localize_text(param_label))
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
            tooltip = localize_text(tooltip)
            label = QLabel(localize_text(label_text))
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
        tooltip = localize_text(tooltip)
        checkbox.setText(localize_text(text))
        checkbox.setMinimumHeight(FORM_CONTROL_HEIGHT)
        checkbox.setFixedWidth(TOGGLE_TEXT_WIDTH)
        checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if tooltip:
            checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox, row_index, 0)
        if param_label:
            label = QLabel(localize_text(param_label))
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
    title_label = QLabel(localize_text(title))
    title_label.setObjectName("pageTitle")
    subtitle_label = QLabel(localize_text(subtitle))
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
    if isinstance(widget, (QLineEdit, QComboBox, FluentComboBox, QSpinBox, QDoubleSpinBox)):
        widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
        widget.setMinimumWidth(FORM_FIELD_MIN_WIDTH)
        widget.setMaximumWidth(FORM_FIELD_MAX_WIDTH)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def tune_skill_widget(widget: QWidget, role: str) -> None:
    if isinstance(widget, QCheckBox):
        widget.setFixedWidth(28)
        widget.setMinimumHeight(FORM_CONTROL_HEIGHT)
        return
    if not isinstance(widget, (QLineEdit, QComboBox, FluentComboBox, QSpinBox)):
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


def build_runner_command(config_path: Path, profile: str) -> list[str]:
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--runner", "--config", str(config_path)]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--runner", "--config", str(config_path)]
    if profile:
        command += ["--profile", profile]
    return command


# Column weight ratios (pixels at baseline window size — distributed proportionally)
_SKILL_COL_WEIGHTS = [66, 84, 118, 60, 60, 54, 60, 60, 86, 84]
_SKILL_COL_TOTAL = sum(_SKILL_COL_WEIGHTS)


