from __future__ import annotations
import configparser
import sys
import io as _io

_stdout_backup = sys.stdout
sys.stdout = _io.StringIO()
try:
    from qfluentwidgets import (
        CheckBox,
        ComboBox as FluentComboBox,
        SpinBox,
        TableWidget,
    )
finally:
    sys.stdout = _stdout_backup
del _stdout_backup, _io

from PySide6.QtCore import QEvent, QObject, Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractSpinBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from .gui_i18n import tr, localize_text
    from .gui_widgets import (
        AUTOSTART_TOOLTIP, COMMON_METHOD_ITEMS, DELAY_TOOLTIP,
        MOVING_METHOD_ITEMS, POTION_METHOD_ITEMS,
        PRIORITY_TOOLTIP, PROFILE_HOTKEY_TOOLTIP, POTION_TOOLTIP,
        QUICK_PAUSE_ACTION_ITEMS, QUICK_PAUSE_MODE_ITEMS,
        QUICK_PAUSE_TRIGGER_ITEMS, RANDOM_TOOLTIP, REPEAT_TOOLTIP,
        REPEAT_INTERVAL_TOOLTIP, SKILL_ACTION_ITEMS, SKILL_ACTION_TOOLTIP,
        SKILL_ACTION_WIDTH, SKILL_NUMBER_WIDTH, SKILL_TABLE_HEADER_HEIGHT,
        SKILL_TABLE_ROW_HEIGHT, SKILL_TEXT_WIDTH, SKILL_TRIGGER_WIDTH,
        SKILL_QUEUE_TOOLTIP, START_MODE_ITEMS, START_MODE_TOOLTIP,
        TRIGGER_BUTTON_TOOLTIP,
        _add_combo_item, _make_line_edit, build_option_grid,
        build_helper_section_grid, build_page_header, build_section,
        build_toggle_grid, combo_value, set_combo_value, tune_combo_box,
        tune_skill_widget,
    )
    from .config_schema import pd, skill_hotkey_default
    from .enums import MovingMethod, PotionMethod, QuickPauseMode, SkillAction, StartMethod, StartMode
except ImportError:
    from gui_i18n import tr, localize_text  # type: ignore[no-redef]
    from gui_widgets import (  # type: ignore[no-redef]
        AUTOSTART_TOOLTIP, COMMON_METHOD_ITEMS, DELAY_TOOLTIP,
        MOVING_METHOD_ITEMS, POTION_METHOD_ITEMS,
        PRIORITY_TOOLTIP, PROFILE_HOTKEY_TOOLTIP, POTION_TOOLTIP,
        QUICK_PAUSE_ACTION_ITEMS, QUICK_PAUSE_MODE_ITEMS,
        QUICK_PAUSE_TRIGGER_ITEMS, RANDOM_TOOLTIP, REPEAT_TOOLTIP,
        REPEAT_INTERVAL_TOOLTIP, SKILL_ACTION_ITEMS, SKILL_ACTION_TOOLTIP,
        SKILL_ACTION_WIDTH, SKILL_NUMBER_WIDTH, SKILL_TABLE_HEADER_HEIGHT,
        SKILL_TABLE_ROW_HEIGHT, SKILL_TEXT_WIDTH, SKILL_TRIGGER_WIDTH,
        SKILL_QUEUE_TOOLTIP, START_MODE_ITEMS, START_MODE_TOOLTIP,
        TRIGGER_BUTTON_TOOLTIP,
        _add_combo_item, _make_line_edit, build_option_grid,
        build_helper_section_grid, build_page_header, build_section,
        build_toggle_grid, combo_value, set_combo_value, tune_combo_box,
        tune_skill_widget,
    )
    from config_schema import pd, skill_hotkey_default  # type: ignore[no-redef]
    from enums import MovingMethod, PotionMethod, QuickPauseMode, SkillAction, StartMethod, StartMode  # type: ignore[no-redef]

# Column weight ratios (pixels at baseline window size — distributed proportionally)
_SKILL_COL_WEIGHTS = [66, 84, 118, 60, 60, 54, 60, 60, 86, 84]
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

        self.widgets["name"] = _make_line_edit(section_name)
        self.widgets["profilehkmethod"] = self._combo(COMMON_METHOD_ITEMS, int(section.get("profilehkmethod", pd("profilehkmethod"))))
        self.widgets["profilehkkey"] = _make_line_edit(section.get("profilehkkey", pd("profilehkkey")))
        self.widgets["autostartmarco"] = self._check(section.get("autostartmarco", pd("autostartmarco")) == "1")
        self.widgets["lazymode"] = self._combo(START_MODE_ITEMS, int(section.get("lazymode", pd("lazymode"))))
        self.widgets["movingmethod"] = self._combo(MOVING_METHOD_ITEMS, int(section.get("movingmethod", pd("movingmethod"))))
        self.widgets["movinginterval"] = self._spin(20, 3000, int(section.get("movinginterval", pd("movinginterval"))))
        self.widgets["potionmethod"] = self._combo(POTION_METHOD_ITEMS, int(section.get("potionmethod", pd("potionmethod"))))
        self.widgets["potioninterval"] = self._spin(200, 30000, int(section.get("potioninterval", pd("potioninterval"))))
        self.widgets["useskillqueue"] = self._check(section.get("useskillqueue", pd("useskillqueue")) == "1")
        self.widgets["useskillqueueinterval"] = self._spin(50, 1000, int(section.get("useskillqueueinterval", pd("useskillqueueinterval"))))
        self.widgets["enablequickpause"] = self._check(section.get("enablequickpause", pd("enablequickpause")) == "1")
        self.widgets["quickpausemethod1"] = self._combo(QUICK_PAUSE_MODE_ITEMS, int(section.get("quickpausemethod1", pd("quickpausemethod1"))))
        self.widgets["quickpausemethod2"] = self._combo(QUICK_PAUSE_TRIGGER_ITEMS, int(section.get("quickpausemethod2", pd("quickpausemethod2"))))
        self.widgets["quickpausemethod3"] = self._combo(QUICK_PAUSE_ACTION_ITEMS, int(section.get("quickpausemethod3", pd("quickpausemethod3"))))
        self.widgets["quickpausedelay"] = self._spin(50, 5000, int(section.get("quickpausedelay", pd("quickpausedelay"))))

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
        self.skill_table = TableWidget()
        self.skill_table.setRowCount(6)
        self.skill_table.setColumnCount(10)
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
            row["hotkey"] = _make_line_edit(section.get(f"skill_{index}", skill_hotkey_default(index)))
            row["action"] = self._combo(SKILL_ACTION_ITEMS, int(section.get(f"action_{index}", "1")))
            row["interval"] = self._spin(20, 60000, int(section.get(f"interval_{index}", "300")))
            row["delay"] = self._spin(-30000, 30000, int(section.get(f"delay_{index}", "10")))
            row["random"] = self._check(section.get(f"random_{index}", "1") == "1")
            row["priority"] = self._spin(1, 10, int(section.get(f"priority_{index}", "1")))
            row["repeat"] = self._spin(1, 99, int(section.get(f"repeat_{index}", "1")))
            row["repeatinterval"] = self._spin(0, 1000, int(section.get(f"repeatinterval_{index}", "30")))
            row["triggerbutton"] = _make_line_edit(section.get(f"triggerbutton_{index}", "LButton"))
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
        self.skill_table.setColumnWidth(0, 72)   # 槽位
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

    def _combo(self, items, value: int) -> FluentComboBox:
        combo = FluentComboBox()
        tune_combo_box(combo)
        for data, text in items:
            _add_combo_item(combo, localize_text(text), data)
        set_combo_value(combo, value)
        return combo

    def _spin(self, minimum: int, maximum: int, value: int) -> SpinBox:
        widget = SpinBox()
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        widget.setSymbolVisible(False)
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        return widget

    def _check(self, checked: bool) -> CheckBox:
        widget = CheckBox()
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
        keyboard_only = method == StartMethod.KEYBOARD
        enabled = method != 1
        self.widgets["profilehkkey"].setEnabled(keyboard_only)
        self.widgets["autostartmarco"].setEnabled(enabled)

    def _sync_start_mode_state(self, *_args) -> None:
        start_mode = combo_value(self.widgets["lazymode"])
        if start_mode in {StartMode.HOLD_WHILE, StartMode.ONCE}:
            widget = self.widgets["enablequickpause"]
            old = widget.blockSignals(True)
            widget.setChecked(False)
            widget.blockSignals(old)
        if start_mode == StartMode.ONCE:
            for widget, value in [
                (self.widgets["useskillqueue"], False),
            ]:
                old = widget.blockSignals(True)
                widget.setChecked(value)
                widget.blockSignals(old)
            for widget, value in [
                (self.widgets["movingmethod"], MovingMethod.NONE),
                (self.widgets["potionmethod"], PotionMethod.NONE),
            ]:
                old = widget.blockSignals(True)
                set_combo_value(widget, value)
                widget.blockSignals(old)
        self.widgets["useskillqueue"].setEnabled(start_mode != StartMode.ONCE)
        self.widgets["movingmethod"].setEnabled(start_mode != StartMode.ONCE)
        self.widgets["potionmethod"].setEnabled(start_mode != StartMode.ONCE)
        self.widgets["enablequickpause"].setEnabled(start_mode == StartMode.TOGGLE)

    def _sync_moving_potion_state(self, *_args) -> None:
        self.widgets["movinginterval"].setEnabled(combo_value(self.widgets["movingmethod"]) == MovingMethod.FORCE_MOVE_SPAM and self.widgets["movingmethod"].isEnabled())
        self.widgets["potioninterval"].setEnabled(combo_value(self.widgets["potionmethod"]) > PotionMethod.NONE and self.widgets["potionmethod"].isEnabled())

    def _sync_skill_queue_state(self, *_args) -> None:
        enabled = self.widgets["useskillqueue"].isChecked() and self.widgets["useskillqueue"].isEnabled()
        self.widgets["useskillqueueinterval"].setEnabled(enabled)
        self._sync_skill_queue_warning()

    def _sync_quick_pause_state(self, *_args) -> None:
        enabled = self.widgets["enablequickpause"].isChecked() and self.widgets["enablequickpause"].isEnabled()
        for key in ["quickpausemethod1", "quickpausemethod2", "quickpausemethod3"]:
            self.widgets[key].setEnabled(enabled)
        self.widgets["quickpausedelay"].setEnabled(enabled and combo_value(self.widgets["quickpausemethod1"]) != QuickPauseMode.HOLD)

    def _sync_skill_row_state(self, index: int, row: dict[str, QWidget]) -> None:
        action = combo_value(row["action"])
        if index == 6 and self._start_method_conflict:
            row["action"].setEnabled(False)
            action = SkillAction.DISABLED
        else:
            row["action"].setEnabled(True)
        row["interval"].setEnabled(action in {SkillAction.SPAM, SkillAction.KEEP_BUFF})
        row["delay"].setEnabled(action in {SkillAction.SPAM, SkillAction.KEY_TRIGGER})
        row["random"].setEnabled(action in {SkillAction.SPAM, SkillAction.KEY_TRIGGER})
        row["priority"].setEnabled(action == SkillAction.KEEP_BUFF)
        row["repeat"].setEnabled(action in {SkillAction.SPAM, SkillAction.KEY_TRIGGER})
        row["repeatinterval"].setEnabled(action in {SkillAction.SPAM, SkillAction.KEY_TRIGGER})
        row["triggerbutton"].setEnabled(action == SkillAction.KEY_TRIGGER)

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
            if combo_value(row["action"]) == SkillAction.SPAM:
                queue_in += 1000.0 / max(row["interval"].value(), 20)
        if queue_in > queue_out:
            self.skill_queue_warning.setToolTip(
                f"当前按键配置每秒向队列中填入{queue_in:.2f}个“连点”技能，但却只取出{queue_out:.2f}个\n"
                "你应当把Buff类技能设置为“保持Buff”而不是“连点”，或者增加连点间隔，或者减少按键队列发送间隔"
            )
            self.skill_queue_warning.show()
        else:
            self.skill_queue_warning.hide()


