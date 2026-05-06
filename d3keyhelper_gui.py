#!/usr/bin/env python3
from __future__ import annotations

import configparser
import os
import sys
import uuid
from pathlib import Path

try:
    from .config_schema import gd
    from .config_io import parse_float, parse_int, write_config_parser_atomic
    from .runner_events import parse_runner_event
except ImportError:
    from config_schema import gd  # type: ignore[no-redef]
    from config_io import parse_float, parse_int, write_config_parser_atomic  # type: ignore[no-redef]
    from runner_events import parse_runner_event  # type: ignore[no-redef]

from PySide6.QtCore import QProcess, QTimer, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

import io as _io
_stdout_backup = sys.stdout
sys.stdout = _io.StringIO()
from qfluentwidgets import (  # noqa: E402
    setTheme,
    Theme,
    setThemeColor,
    ComboBox as FluentComboBox,
    SpinBox,
    DoubleSpinBox,
    CheckBox,
    PushButton as FluentPushButton,
    PrimaryPushButton,
    PlainTextEdit,
    ListWidget,
    SmoothScrollArea,
    FluentIcon as FIF,
)
sys.stdout = _stdout_backup
del _stdout_backup, _io

try:
    from .d3keyhelper import DEFAULT_VERSION, create_default_config, default_config_path, default_profile_dict, main as runtime_main
except ImportError:
    try:
        from linux_port.d3keyhelper import DEFAULT_VERSION, create_default_config, default_config_path, default_profile_dict, main as runtime_main
    except ImportError:
        from d3keyhelper import DEFAULT_VERSION, create_default_config, default_config_path, default_profile_dict, main as runtime_main



try:
    from .gui_i18n import (  # noqa: F401
        UI_LANGUAGE_ENV, LANGUAGE_TOOLBAR_ITEMS,
        normalize_ui_language, resolve_ui_language, set_ui_language,
        configured_ui_language, UI_LANGUAGE, EN_TEXT, ZH_TW_MAP,
        zh_to_tw, localize_text, tr, load_parser,
    )
    from .gui_widgets import (  # noqa: F401
        app_icon_path, APP_STYLE_SHEET,
        START_METHOD_ITEMS, COMMON_METHOD_ITEMS, SKILL_ACTION_ITEMS,
        START_MODE_ITEMS, MOVING_METHOD_ITEMS, POTION_METHOD_ITEMS,
        SALVAGE_METHOD_ITEMS, REFORGE_METHOD_ITEMS, QUICK_PAUSE_MODE_ITEMS,
        QUICK_PAUSE_TRIGGER_ITEMS, QUICK_PAUSE_ACTION_ITEMS,
        HELPER_SPEED_PRESET_ITEMS, HELPER_SPEED_PRESET_VALUES, SEND_MODE_ITEMS,
        FULL_WINDOW_SIZE, DEFAULT_SKILLS, FORM_LABEL_WIDTH, FORM_FIELD_MIN_WIDTH,
        FORM_FIELD_MAX_WIDTH, FORM_CONTROL_HEIGHT, TOGGLE_TEXT_WIDTH,
        INLINE_LABEL_WIDTH, TOOLBAR_PATH_MIN_WIDTH, TOOLBAR_PATH_MAX_WIDTH,
        NAV_WIDTH, NAV_ACTION_MARGIN, SKILL_TEXT_WIDTH, SKILL_TRIGGER_WIDTH,
        SKILL_ACTION_WIDTH, SKILL_NUMBER_WIDTH, SKILL_TABLE_ROW_HEIGHT,
        SKILL_TABLE_HEADER_HEIGHT,
        AUTOSTART_TOOLTIP, START_MODE_TOOLTIP, SKILL_QUEUE_TOOLTIP,
        SKILL_QUEUE_INTERVAL_TOOLTIP, POTION_TOOLTIP, DELAY_TOOLTIP,
        RANDOM_TOOLTIP, SKILL_ACTION_TOOLTIP, PRIORITY_TOOLTIP, REPEAT_TOOLTIP,
        REPEAT_INTERVAL_TOOLTIP, TRIGGER_BUTTON_TOOLTIP, RUN_ON_START_TOOLTIP,
        SMART_PAUSE_TOOLTIP, GAME_GAMMA_TOOLTIP, BUFF_PERCENT_TOOLTIP,
        GAME_RESOLUTION_TOOLTIP, HELPER_HOTKEY_TOOLTIP, HELPER_SPEED_TOOLTIP,
        HELPER_SPEED_PRESET_TOOLTIP, SAFEZONE_TOOLTIP, GAMBLE_TOOLTIP,
        LOOT_TOOLTIP, SALVAGE_ENABLE_TOOLTIP, SALVAGE_METHOD_TOOLTIP,
        UPGRADE_TOOLTIP, CONVERT_TOOLTIP, ABANDON_TOOLTIP,
        CUSTOM_STANDING_TOOLTIP, CUSTOM_MOVING_TOOLTIP, CUSTOM_POTION_TOOLTIP,
        PROFILE_HOTKEY_TOOLTIP, SEND_MODE_TOOLTIP, SOUND_ON_SWITCH_TOOLTIP,
        make_reforge_method_tooltip, set_combo_value, _make_line_edit,
        _add_combo_item, tune_combo_box, combo_value, combo_data,
        classify_safezone_text, helper_speed_preset_from_values,
        SafeZonePickerDialog,
        build_profile_selector, build_form_layout, build_settings_grid,
        add_form_rows, build_section, build_sub_header, build_two_column_form,
        build_inline_field, build_checkbox_field, build_toggle_grid,
        build_option_grid, build_helper_grid, build_helper_list,
        build_helper_section_grid, build_parameter_section_grid,
        build_page_header, tune_form_widget, tune_skill_widget,
        build_runner_command,
    )
    from .gui_profile_page import ProfileTab, _SkillColumnDistributor  # noqa: F401
except ImportError:
    from gui_i18n import (  # type: ignore[no-redef]  # noqa: F401
        UI_LANGUAGE_ENV, LANGUAGE_TOOLBAR_ITEMS,
        normalize_ui_language, resolve_ui_language, set_ui_language,
        configured_ui_language, UI_LANGUAGE, EN_TEXT, ZH_TW_MAP,
        zh_to_tw, localize_text, tr, load_parser,
    )
    from gui_widgets import (  # type: ignore[no-redef]  # noqa: F401
        app_icon_path, APP_STYLE_SHEET,
        START_METHOD_ITEMS, COMMON_METHOD_ITEMS, SKILL_ACTION_ITEMS,
        START_MODE_ITEMS, MOVING_METHOD_ITEMS, POTION_METHOD_ITEMS,
        SALVAGE_METHOD_ITEMS, REFORGE_METHOD_ITEMS, QUICK_PAUSE_MODE_ITEMS,
        QUICK_PAUSE_TRIGGER_ITEMS, QUICK_PAUSE_ACTION_ITEMS,
        HELPER_SPEED_PRESET_ITEMS, HELPER_SPEED_PRESET_VALUES, SEND_MODE_ITEMS,
        FULL_WINDOW_SIZE, DEFAULT_SKILLS, FORM_LABEL_WIDTH, FORM_FIELD_MIN_WIDTH,
        FORM_FIELD_MAX_WIDTH, FORM_CONTROL_HEIGHT, TOGGLE_TEXT_WIDTH,
        INLINE_LABEL_WIDTH, TOOLBAR_PATH_MIN_WIDTH, TOOLBAR_PATH_MAX_WIDTH,
        NAV_WIDTH, NAV_ACTION_MARGIN, SKILL_TEXT_WIDTH, SKILL_TRIGGER_WIDTH,
        SKILL_ACTION_WIDTH, SKILL_NUMBER_WIDTH, SKILL_TABLE_ROW_HEIGHT,
        SKILL_TABLE_HEADER_HEIGHT,
        AUTOSTART_TOOLTIP, START_MODE_TOOLTIP, SKILL_QUEUE_TOOLTIP,
        SKILL_QUEUE_INTERVAL_TOOLTIP, POTION_TOOLTIP, DELAY_TOOLTIP,
        RANDOM_TOOLTIP, SKILL_ACTION_TOOLTIP, PRIORITY_TOOLTIP, REPEAT_TOOLTIP,
        REPEAT_INTERVAL_TOOLTIP, TRIGGER_BUTTON_TOOLTIP, RUN_ON_START_TOOLTIP,
        SMART_PAUSE_TOOLTIP, GAME_GAMMA_TOOLTIP, BUFF_PERCENT_TOOLTIP,
        GAME_RESOLUTION_TOOLTIP, HELPER_HOTKEY_TOOLTIP, HELPER_SPEED_TOOLTIP,
        HELPER_SPEED_PRESET_TOOLTIP, SAFEZONE_TOOLTIP, GAMBLE_TOOLTIP,
        LOOT_TOOLTIP, SALVAGE_ENABLE_TOOLTIP, SALVAGE_METHOD_TOOLTIP,
        UPGRADE_TOOLTIP, CONVERT_TOOLTIP, ABANDON_TOOLTIP,
        CUSTOM_STANDING_TOOLTIP, CUSTOM_MOVING_TOOLTIP, CUSTOM_POTION_TOOLTIP,
        PROFILE_HOTKEY_TOOLTIP, SEND_MODE_TOOLTIP, SOUND_ON_SWITCH_TOOLTIP,
        make_reforge_method_tooltip, set_combo_value, _make_line_edit,
        _add_combo_item, tune_combo_box, combo_value, combo_data,
        classify_safezone_text, helper_speed_preset_from_values,
        SafeZonePickerDialog,
        build_profile_selector, build_form_layout, build_settings_grid,
        add_form_rows, build_section, build_sub_header, build_two_column_form,
        build_inline_field, build_checkbox_field, build_toggle_grid,
        build_option_grid, build_helper_grid, build_helper_list,
        build_helper_section_grid, build_parameter_section_grid,
        build_page_header, tune_form_widget, tune_skill_widget,
        build_runner_command,
    )
    from gui_profile_page import ProfileTab, _SkillColumnDistributor  # type: ignore[no-redef]  # noqa: F401

try:
    from . import gui_i18n as _gui_i18n
except ImportError:
    import gui_i18n as _gui_i18n  # type: ignore[no-redef]


def set_ui_language(language: str) -> str:
    """Keep the module-level UI_LANGUAGE binding in sync with gui_i18n after each call."""
    global UI_LANGUAGE
    result = _gui_i18n.set_ui_language(language)
    UI_LANGUAGE = result
    return result


NAV_FONT_FAMILIES = [
    "Noto Sans CJK SC",
    "Source Han Sans SC",
    "Microsoft YaHei",
    "WenQuanYi Micro Hei",
    "DejaVu Sans",
]


def _section_int(section: configparser.SectionProxy, key: str, default: str) -> int:
    return parse_int(section.get(key, default), parse_int(default, 0))


def _section_float(section: configparser.SectionProxy, key: str, default: str) -> float:
    return parse_float(section.get(key, default), parse_float(default, 0.0))


def apply_navigation_font_family(font: QFont) -> None:
    if hasattr(font, "setFamilies"):
        font.setFamilies(NAV_FONT_FAMILIES)
    else:
        font.setFamily(NAV_FONT_FAMILIES[0])
    font.setStyleHint(QFont.StyleHint.SansSerif)


class MainWindow(QMainWindow):
    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path
        if not self.config_path.exists():
            create_default_config(self.config_path)
        set_ui_language(configured_ui_language(self.config_path) or resolve_ui_language())
        self.process: QProcess | None = None
        self.general_widgets: dict[str, object] = {}
        self.profile_tabs: list[ProfileTab] = []
        self.profile_nav_items: list[QListWidgetItem] = []
        self._toolbar_profile_synced = False
        self._toolbar_language_synced = False
        self._last_log_line = tr("尚无日志。", "No log messages yet.")
        self._path_text = str(self.config_path)
        self._log_expanded = False
        self._suspend_config_watch = False
        self._config_apply_timer = QTimer(self)
        self._config_apply_timer.setSingleShot(True)
        self._config_apply_timer.setInterval(500)
        self._config_apply_timer.timeout.connect(self._apply_live_config_change)
        self._init_shell_widgets()
        self.setWindowTitle("D3Macro")
        self.setStyleSheet(APP_STYLE_SHEET)
        self.resize(*FULL_WINDOW_SIZE)
        self.setMinimumSize(960, 620)
        self._build_shell()
        self.reload_config()
        self._build_tray_icon()

    def _init_shell_widgets(self) -> None:
        self.navigation = ListWidget()
        self.page_stack = QStackedWidget()
        self.log = PlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)

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
        reload_button = FluentPushButton(FIF.SYNC, tr("重新载入", "Reload"))
        reload_button.clicked.connect(self.reload_config)
        save_button = FluentPushButton(FIF.SAVE, tr("保存配置", "Save"))
        save_button.clicked.connect(self.save_config)
        start_button = PrimaryPushButton(FIF.PLAY, tr("启动", "Start"))
        start_button.clicked.connect(self.start_runner)
        stop_button = FluentPushButton(FIF.POWER_BUTTON, tr("停止", "Stop"))
        stop_button.clicked.connect(lambda _checked=False: self.stop_runner())
        lang_frame = QFrame()
        lang_frame.setObjectName("langSwitcher")
        lang_layout = QHBoxLayout(lang_frame)
        lang_layout.setContentsMargins(2, 2, 2, 2)
        lang_layout.setSpacing(1)
        self._lang_btn_group = QButtonGroup(lang_frame)
        self._lang_btn_group.setExclusive(True)
        self._lang_btns: dict[str, QPushButton] = {}
        for i, (code, label) in enumerate(LANGUAGE_TOOLBAR_ITEMS):
            btn = QPushButton(label)
            btn.setObjectName("langButton")
            btn.setCheckable(True)
            btn.setChecked(code == UI_LANGUAGE)
            btn.setToolTip(tr("界面语言", "Interface language"))
            btn.clicked.connect(self._apply_language_selection)
            self._lang_btn_group.addButton(btn, i)
            self._lang_btns[code] = btn
            lang_layout.addWidget(btn)
        toolbar.addWidget(lang_frame)
        toolbar.addStretch(1)
        profile_label = QLabel(tr("激活配置:", "Profile:"))
        profile_label.setObjectName("toolbarLabel")
        self.toolbar_profile_combo = FluentComboBox()
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
        nav_font = QFont()
        apply_navigation_font_family(nav_font)
        nav_font.setPointSize(10)
        nav_font.setWeight(QFont.Weight.Normal)
        self.navigation.setFont(nav_font)
        self.navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.navigation.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.navigation.setSpacing(2)
        self.navigation.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.navigation.currentRowChanged.connect(self._select_page)
        self.navigation.currentRowChanged.connect(lambda _: self._refresh_profile_buttons())
        self.navigation.itemSelectionChanged.connect(self._refresh_profile_buttons)
        self.add_profile_btn = FluentPushButton(FIF.ADD, tr("添加", "Add"))
        self.add_profile_btn.setObjectName("navActionButton")
        self.add_profile_btn.setFixedHeight(32)
        self.add_profile_btn.setToolTip(tr("添加新配置", "Add profile"))
        self.add_profile_btn.clicked.connect(self._add_profile)
        self.remove_profile_btn = FluentPushButton(FIF.REMOVE, tr("删除", "Remove"))
        self.remove_profile_btn.setObjectName("navActionButton")
        self.remove_profile_btn.setFixedHeight(32)
        self.remove_profile_btn.setToolTip(tr("删除选中配置（可多选）", "Remove selected profiles (multi-select supported)"))
        self.remove_profile_btn.clicked.connect(self._remove_profile)
        sidebar = QWidget()
        sidebar.setObjectName("navSidebar")
        sidebar.setFixedWidth(NAV_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        nav_actions = QFrame()
        nav_actions.setObjectName("navActions")
        nav_actions.setFixedHeight(82)
        nav_actions_layout = QVBoxLayout(nav_actions)
        nav_actions_layout.setContentsMargins(NAV_ACTION_MARGIN, 4, NAV_ACTION_MARGIN, 8)
        nav_actions_layout.setSpacing(4)
        nav_actions_layout.addWidget(self.add_profile_btn)
        nav_actions_layout.addWidget(self.remove_profile_btn)
        sidebar_layout.addWidget(self.navigation)
        sidebar_layout.addWidget(nav_actions)
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
        splitter.addWidget(sidebar)
        splitter.addWidget(content_widget)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([NAV_WIDTH, FULL_WINDOW_SIZE[0] - NAV_WIDTH])
        self.body_splitter = splitter
        layout.addWidget(splitter, 1)
        self.status_strip = QFrame()
        self.status_strip.setObjectName("statusStrip")
        self.status_strip.setFixedHeight(40)
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
        self.log_toggle_button = FluentPushButton(tr("展开日志", "Show Log"))
        self.log_toggle_button.setCheckable(True)
        self.log_toggle_button.setMinimumWidth(100)
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
        self.navigation.addItem(self._navigation_item(tr("通用", "General")))
        self.page_stack.addWidget(self._build_general_tab(parser[general_name], profile_names))
        for name in profile_names:
            tab = ProfileTab(name, parser[name])
            self.profile_tabs.append(tab)
            item = self._navigation_item(name)
            self.profile_nav_items.append(item)
            self.navigation.addItem(item)
            self.page_stack.addWidget(self._wrap_scroll_tab(tab))
        self.navigation.setCurrentRow(0)
        self._refresh_general_state()
        self._connect_config_change_watchers()
        self._suspend_config_watch = False
        self._update_runtime_status_widgets()
        self._sync_toolbar_profile_combo(profile_names)
        self._refresh_profile_buttons()
        self._update_tray_menu()

    def _navigation_item(self, text: str) -> QListWidgetItem:
        item = QListWidgetItem(text)
        font = item.font()
        apply_navigation_font_family(font)
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Normal)
        item.setFont(font)
        return item


    def _sync_toolbar_profile_combo(self, profile_names: list[str]) -> None:
        """Populate toolbar profile combo and wire it to the General tab's activatedprofile widget."""
        general_combo = self.general_widgets.get("activatedprofile")
        combo = self.toolbar_profile_combo
        combo.blockSignals(True)
        combo.clear()
        count = max(len(profile_names), 1)
        for index in range(1, count + 1):
            name = profile_names[index - 1] if index <= len(profile_names) else tr(f"配置{index}", f"Profile {index}")
            combo.addItem(f"{index} - {localize_text(name)}", userData=index)
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

    def _refresh_profile_buttons(self) -> None:
        count = len(self.profile_tabs)
        selected_profile_rows = [self.navigation.row(i) for i in self.navigation.selectedItems() if self.navigation.row(i) > 0]
        self.add_profile_btn.setEnabled(True)
        self.remove_profile_btn.setEnabled(count > 1 and len(selected_profile_rows) > 0)

    def _new_profile_id(self, existing: list[str]) -> str:
        existing_lower = {s.lower() for s in existing}
        while True:
            new_id = "p-" + uuid.uuid4().hex[:6]
            if new_id not in existing_lower:
                return new_id

    def _write_parser(self, parser: configparser.ConfigParser) -> None:
        write_config_parser_atomic(self.config_path, parser, "; D3Macro config\r\n")

    def _add_profile(self) -> None:
        if not self.save_config(log_message=""):
            return
        parser = load_parser(self.config_path)
        profile_names = [s for s in parser.sections() if s.lower() != "general"]
        new_name = self._new_profile_id(profile_names)
        parser[new_name] = default_profile_dict()
        self._write_parser(parser)
        new_row = 1 + len(profile_names)  # 1-based after General
        self.reload_config()
        self.navigation.setCurrentRow(new_row)
        self._append_log(tr(f"已添加配置：{new_name}", f"Added profile: {new_name}"))

    def _remove_profile(self) -> None:
        # Collect selected profile rows (exclude row 0 = General)
        selected_rows = sorted(
            {self.navigation.row(i) for i in self.navigation.selectedItems() if self.navigation.row(i) > 0},
            reverse=True,
        )
        if not selected_rows or len(self.profile_tabs) <= 1:
            return
        # Resolve display names before save (same key save_config will write)
        names_to_delete = []
        for row in sorted(selected_rows):
            tab = self.profile_tabs[row - 1]
            names_to_delete.append(tab.widgets["name"].text().strip() or tab.section_name)
        # Enforce: cannot delete all profiles
        if len(names_to_delete) >= len(self.profile_tabs):
            QMessageBox.warning(
                self,
                tr("无法删除", "Cannot delete"),
                tr("至少需要保留一个配置。", "At least one profile must remain."),
            )
            return
        if len(names_to_delete) == 1:
            msg = tr(f'确定要删除配置「{names_to_delete[0]}」？此操作不可撤销。',
                     f'Delete profile "{names_to_delete[0]}"? This cannot be undone.')
        else:
            joined = "、".join(f'「{n}」' for n in names_to_delete)
            msg = tr(f'确定要删除 {len(names_to_delete)} 个配置：{joined}？此操作不可撤销。',
                     f'Delete {len(names_to_delete)} profiles: {", ".join(names_to_delete)}? This cannot be undone.')
        reply = QMessageBox.question(
            self,
            tr("删除配置", "Remove profile"),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if not self.save_config(log_message=""):
            return
        parser = load_parser(self.config_path)
        profile_names = [s for s in parser.sections() if s.lower() != "general"]
        general_key = next(s for s in parser.sections() if s.lower() == "general")
        old_active = parse_int(parser[general_key].get("activatedprofile", "1"), 1)
        # Remove all sections and compute new activatedprofile
        removed_indices = sorted(
            [profile_names.index(n) + 1 for n in names_to_delete if n in profile_names]
        )
        for name in names_to_delete:
            if name in profile_names:
                parser.remove_section(name)
        new_profile_names = [s for s in parser.sections() if s.lower() != "general"]
        new_count = len(new_profile_names)
        # Shift activatedprofile: count how many removed indices are <= old_active
        shift = sum(1 for idx in removed_indices if idx <= old_active)
        new_active = max(1, min(old_active - shift, new_count))
        parser[general_key]["activatedprofile"] = str(new_active)
        self._write_parser(parser)
        # Navigate to the profile just above the first deleted row
        first_deleted_row = min(r for r in selected_rows)
        target_row = max(1, min(first_deleted_row - 1, new_count)) if first_deleted_row > new_count else min(first_deleted_row, new_count)
        self.reload_config()
        self.navigation.setCurrentRow(target_row)
        label = "、".join(names_to_delete)
        self._append_log(tr(f"已删除配置：{label}", f"Removed profiles: {', '.join(names_to_delete)}"))

    def _build_general_tab(self, section: configparser.SectionProxy, profile_names: list[str]) -> QWidget:
        container = QWidget()
        container.setObjectName("pageContainer")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        helper_speed_preset = helper_speed_preset_from_values(
            _section_int(section, "helpermousespeed", gd("helpermousespeed")),
            _section_int(section, "helperanimationdelay", gd("helperanimationdelay")),
            _section_int(section, "helperspeed", gd("helperspeed")),
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

        self.general_widgets["activatedprofile"] = build_profile_selector(profile_names, _section_int(section, "activatedprofile", gd("activatedprofile")))
        self.general_widgets["startmethod"] = self._combo(START_METHOD_ITEMS, _section_int(section, "startmethod", gd("startmethod")))
        self.general_widgets["starthotkey"] = _make_line_edit(section.get("starthotkey", gd("starthotkey")))
        self.general_widgets["oldsandhelpermethod"] = self._combo(COMMON_METHOD_ITEMS, _section_int(section, "oldsandhelpermethod", gd("oldsandhelpermethod")))
        self.general_widgets["oldsandhelperhk"] = _make_line_edit(section.get("oldsandhelperhk", gd("oldsandhelperhk")))
        self.general_widgets["sendmode"] = self._combo(SEND_MODE_ITEMS, section.get("sendmode", gd("sendmode")))
        self.general_widgets["runonstart"] = self._check(section.get("runonstart", gd("runonstart")) == "1")
        self.general_widgets["d3only"] = self._check(section.get("d3only", gd("d3only")) == "1")
        self.general_widgets["enablesmartpause"] = self._check(section.get("enablesmartpause", gd("enablesmartpause")) == "1")
        self.general_widgets["enablesoundplay"] = self._check(section.get("enablesoundplay", gd("enablesoundplay")) == "1")
        self.general_widgets["gameresolution"] = _make_line_edit(section.get("gameresolution", gd("gameresolution")))
        self.general_widgets["gamegamma"] = self._float_spin(0.5, 1.5, _section_float(section, "gamegamma", gd("gamegamma")), 6)
        self.general_widgets["buffpercent"] = self._float_spin(0.0, 1.0, _section_float(section, "buffpercent", gd("buffpercent")), 6)
        for key, value in [
            ("customstanding", section.get("customstanding", gd("customstanding")) == "1"),
            ("custommoving", section.get("custommoving", gd("custommoving")) == "1"),
            ("custompotion", section.get("custompotion", gd("custompotion")) == "1"),
            ("enablegamblehelper", section.get("enablegamblehelper", gd("enablegamblehelper")) == "1"),
            ("enableloothelper", section.get("enableloothelper", gd("enableloothelper")) == "1"),
            ("enablesalvagehelper", section.get("enablesalvagehelper", gd("enablesalvagehelper")) == "1"),
            ("enablereforgehelper", section.get("enablereforgehelper", gd("enablereforgehelper")) == "1"),
            ("enableupgradehelper", section.get("enableupgradehelper", gd("enableupgradehelper")) == "1"),
            ("enableconverthelper", section.get("enableconverthelper", gd("enableconverthelper")) == "1"),
            ("enableabandonhelper", section.get("enableabandonhelper", gd("enableabandonhelper")) == "1"),
        ]:
            self.general_widgets[key] = self._check(value)
        self.general_widgets["customstandinghk"] = _make_line_edit(section.get("customstandinghk", gd("customstandinghk")))
        self.general_widgets["custommovinghk"] = _make_line_edit(section.get("custommovinghk", gd("custommovinghk")))
        self.general_widgets["custompotionhk"] = _make_line_edit(section.get("custompotionhk", gd("custompotionhk")))
        self.general_widgets["gamblehelpertimes"] = self._spin(1, 60, _section_int(section, "gamblehelpertimes", gd("gamblehelpertimes")))
        self.general_widgets["loothelpertimes"] = self._spin(1, 99, _section_int(section, "loothelpertimes", gd("loothelpertimes")))
        self.general_widgets["salvagehelpermethod"] = self._combo(SALVAGE_METHOD_ITEMS, _section_int(section, "salvagehelpermethod", gd("salvagehelpermethod")))
        self.general_widgets["reforgehelpermethod"] = self._combo(REFORGE_METHOD_ITEMS, _section_int(section, "reforgehelpermethod", gd("reforgehelpermethod")))
        self.general_widgets["helperspeed"] = self._combo(HELPER_SPEED_PRESET_ITEMS, helper_speed_preset)
        self.general_widgets["helpermousespeed"] = self._spin(0, 10, _section_int(section, "helpermousespeed", gd("helpermousespeed")))
        self.general_widgets["helperanimationdelay"] = self._spin(1, 1000, _section_int(section, "helperanimationdelay", gd("helperanimationdelay")))
        self.general_widgets["safezone"] = _make_line_edit(section.get("safezone", gd("safezone")))
        safezone_pick_btn = QPushButton(tr("选择", "Pick"))
        safezone_pick_btn.setFixedWidth(50)
        safezone_pick_btn.setFixedHeight(FORM_CONTROL_HEIGHT)
        safezone_pick_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.general_widgets["safezone_pick_btn"] = safezone_pick_btn
        safezone_row = QWidget()
        safezone_row.setFixedHeight(FORM_CONTROL_HEIGHT)
        safezone_row.setMinimumWidth(FORM_FIELD_MIN_WIDTH)
        safezone_row.setMaximumWidth(FORM_FIELD_MAX_WIDTH)
        _sz_layout = QHBoxLayout(safezone_row)
        _sz_layout.setContentsMargins(0, 0, 0, 0)
        _sz_layout.setSpacing(4)
        _sz_layout.addWidget(self.general_widgets["safezone"], 1)
        _sz_layout.addWidget(safezone_pick_btn, 0)
        self.general_widgets["safezone_row"] = safezone_row
        self.general_widgets["maxreforge"] = self._spin(1, 999, _section_int(section, "maxreforge", gd("maxreforge")))
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
                    ("安全格", self.general_widgets["safezone_row"], SAFEZONE_TOOLTIP),
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

    def _wrap_scroll_tab(self, widget: QWidget) -> SmoothScrollArea:
        tab = SmoothScrollArea()
        tab.setWidgetResizable(True)
        tab.setFrameShape(QFrame.Shape.NoFrame)
        tab.setWidget(widget)
        tab.viewport().setAutoFillBackground(False)
        return tab

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

    def _float_spin(self, minimum: float, maximum: float, value: float, decimals: int) -> DoubleSpinBox:
        widget = DoubleSpinBox()
        widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        widget.setSymbolVisible(False)
        widget.setRange(minimum, maximum)
        widget.setDecimals(decimals)
        widget.setSingleStep(0.01)
        widget.setValue(value)
        return widget

    def _check(self, checked: bool) -> CheckBox:
        widget = CheckBox()
        widget.setChecked(checked)
        return widget

    def _bool_text(self, widget: QCheckBox) -> str:
        return "1" if widget.isChecked() else "0"

    def _current_selected_language(self) -> str:
        for code, btn in self._lang_btns.items():
            if btn.isChecked():
                return normalize_ui_language(code) or "zh"
        return "zh"

    def _apply_language_selection(self, *_args) -> None:
        if self._suspend_config_watch:
            return
        selected = self._current_selected_language()
        if selected == UI_LANGUAGE:
            return
        self._config_apply_timer.stop()
        if not self.save_config(log_message=""):
            return
        set_ui_language(selected)
        self._rebuild_shell()

    def _rebuild_shell(self) -> None:
        self._suspend_config_watch = True
        self._toolbar_profile_synced = False
        self._toolbar_language_synced = False
        old_central = self.centralWidget()
        if old_central is not None:
            old_central.deleteLater()
        self.general_widgets.clear()
        self.profile_tabs.clear()
        self.profile_nav_items.clear()
        self._last_log_line = tr("尚无日志。", "No log messages yet.")
        self._init_shell_widgets()
        self._build_shell()
        self.reload_config()

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
        self.general_widgets["safezone_pick_btn"].clicked.connect(self._open_safezone_picker)
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
        self.general_widgets["safezone_pick_btn"].setEnabled(needs_safezone)
        if not needs_safezone:
            status.hide()
            return
        text = self.general_widgets["safezone"].text().strip()
        state, values = classify_safezone_text(text)
        if state == "set":
            status.setText(localize_text("安全格状态：已设置"))
            status.setStyleSheet("color: #1f7a3f; font-weight: 400;")
            slots = ",".join(str(value) for value in sorted(values))
            status.setToolTip(tr(f"当前安全格：{slots}", f"Current safe slots: {slots}"))
        elif state == "legacy-default":
            status.setText(localize_text("安全格状态：未设置（沿用原版默认值 61,62,63）"))
            status.setStyleSheet("color: #536173; font-weight: 400;")
            status.setToolTip(tr("原版 AHK 默认把 safezone 写成 61,62,63，用来提示格式；这三个格子并不存在。", "The original AHK version used 61,62,63 as a format placeholder; those slots do not exist."))
        elif state == "unset":
            status.setText(localize_text("安全格状态：未设置"))
            status.setStyleSheet("color: #536173; font-weight: 400;")
            status.setToolTip(tr("当前没有启用任何 1-60 的安全格。", "No 1-60 safe slots are enabled."))
        else:
            status.setText(localize_text("安全格状态：格式错误"))
            status.setStyleSheet("color: #b42318; font-weight: 400;")
            status.setToolTip(tr("请填写 1-60 之间的格子编号，使用英文逗号分隔，例如：1,2,3", "Use slot numbers from 1 to 60, separated by commas, for example: 1,2,3"))
        status.show()

    def _open_safezone_picker(self) -> None:
        text = self.general_widgets["safezone"].text().strip()
        _, current_slots = classify_safezone_text(text)
        dlg = SafeZonePickerDialog(current_slots, parent=self)
        if dlg.exec() == SafeZonePickerDialog.DialogCode.Accepted:
            selected = dlg.selected_slots()
            if selected:
                self.general_widgets["safezone"].setText(",".join(str(s) for s in sorted(selected)))
            else:
                self.general_widgets["safezone"].setText("")
            self._refresh_general_state()

    def _append_log(self, text: str) -> None:
        message = localize_text(text.rstrip())
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
        # path_label is no longer shown in the toolbar; update window title instead
        filename = Path(self._path_text).name if self._path_text else ""
        self.setWindowTitle(f"D3Macro — {filename}" if filename else "D3Macro")
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
        self._update_tray_menu()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_path_label()
        self._update_runtime_status_widgets()

    def _profile_save_names(self) -> list[str] | None:
        names: list[str] = []
        seen: set[str] = set()
        duplicates: list[str] = []
        for tab in self.profile_tabs:
            name = tab.widgets["name"].text().strip() or tab.section_name
            normalized = name.lower()
            if not name or normalized == "general":
                QMessageBox.warning(
                    self,
                    tr("配置名无效", "Invalid profile name"),
                    tr("配置名不能为空，也不能使用 General。", "Profile names cannot be empty or General."),
                )
                self._append_log(tr("配置未保存：配置名无效。", "Config was not saved: invalid profile name."))
                return None
            if normalized in seen:
                duplicates.append(name)
            seen.add(normalized)
            names.append(name)
        if duplicates:
            duplicate_text = "、".join(duplicates)
            QMessageBox.warning(
                self,
                tr("配置名重复", "Duplicate profile name"),
                tr(
                    f"存在重复配置名：{duplicate_text}。请先改成唯一名称。",
                    f"Duplicate profile names: {duplicate_text}. Rename them before saving.",
                ),
            )
            self._append_log(tr("配置未保存：存在重复配置名。", "Config was not saved: duplicate profile names."))
            return None
        return names

    def _load_parser_for_save(self) -> configparser.ConfigParser:
        try:
            return load_parser(self.config_path)
        except Exception:
            parser = configparser.ConfigParser(interpolation=None)
            parser.optionxform = str.lower
            return parser

    def _update_section_values(self, parser: configparser.ConfigParser, section: str, values: dict[str, str]) -> None:
        if not parser.has_section(section):
            parser.add_section(section)
        for key, value in values.items():
            parser[section][key] = value

    def save_config(self, log_message: str = "已保存配置。") -> bool:
        profile_names = self._profile_save_names()
        if profile_names is None:
            return False
        parser = self._load_parser_for_save()
        general_name = next((name for name in parser.sections() if name.lower() == "general"), "General")
        general_values = {
            "version": DEFAULT_VERSION,
            "language": self._current_selected_language(),
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
        self._update_section_values(parser, general_name, general_values)

        profile_payloads: list[tuple[str, dict[str, str]]] = []
        for tab, name in zip(self.profile_tabs, profile_names):
            values = dict(parser[tab.section_name].items()) if parser.has_section(tab.section_name) else {}
            values.update({
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
            })
            for index, row in enumerate(tab.widgets["skills"], start=1):
                values[f"skill_{index}"] = row["hotkey"].text().strip() or DEFAULT_SKILLS[index]
                values[f"action_{index}"] = str(combo_value(row["action"]))
                values[f"interval_{index}"] = str(row["interval"].value())
                values[f"delay_{index}"] = str(row["delay"].value())
                values[f"random_{index}"] = "1" if row["random"].isChecked() else "0"
                values[f"priority_{index}"] = str(row["priority"].value())
                values[f"repeat_{index}"] = str(row["repeat"].value())
                values[f"repeatinterval_{index}"] = str(row["repeatinterval"].value())
                values[f"triggerbutton_{index}"] = row["triggerbutton"].text().strip() or "LButton"
            profile_payloads.append((name, values))

        for tab in self.profile_tabs:
            if parser.has_section(tab.section_name):
                parser.remove_section(tab.section_name)
        for name, values in profile_payloads:
            if parser.has_section(name):
                parser.remove_section(name)
            parser.add_section(name)
            for key, value in values.items():
                parser[name][key] = value

        self._write_parser(parser)
        if log_message:
            self._append_log(log_message)
        for item, tab in zip(self.profile_nav_items, self.profile_tabs):
            title = tab.widgets["name"].text().strip() or tab.section_name
            item.setText(title)
            if hasattr(tab, "page_header") and hasattr(tab.page_header, "title_label"):
                tab.page_header.title_label.setText(title)
            tab.section_name = title
        return True

    def start_runner(self) -> None:
        self._launch_runner(save_first=True, log_message="已启动运行器。")

    def _launch_runner(self, save_first: bool, log_message: str) -> None:
        self._config_apply_timer.stop()
        if save_first:
            if not self.save_config():
                return
        self.stop_runner(log_message=None)
        command = build_runner_command(self.config_path, "")
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_process_output)
        self.process.finished.connect(self._runner_finished)
        self.process.start(command[0], command[1:])
        if not self.process.waitForStarted(5000):
            QMessageBox.critical(self, tr("启动失败", "Start failed"), tr("无法启动运行器。", "Failed to start the runner."))
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
        if not text:
            return
        display_lines: list[str] = []
        beep = "\a" in text
        text = text.replace("\a", "")
        for line in text.splitlines(keepends=True):
            event = parse_runner_event(line)
            if event is not None:
                if event.kind == "profile_switched" and self.general_widgets["enablesoundplay"].isChecked():
                    beep = True
                # Don't show raw EVENT: lines in the user log
                continue
            display_lines.append(line)
        if beep:
            QApplication.beep()
        if display_lines:
            self._append_log("".join(display_lines))

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
        elif isinstance(widget, (QComboBox, FluentComboBox)):
            widget.currentIndexChanged.connect(self._schedule_live_config_change)
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(self._schedule_live_config_change)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self._schedule_live_config_change)

    def _connect_config_change_watchers(self) -> None:
        for key, widget in self.general_widgets.items():
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
        if not self.save_config(log_message="已自动保存配置。"):
            return
        if was_running:
            self._launch_runner(save_first=False, log_message="检测到配置变更，已自动重启运行器。")

    # ------------------------------------------------------------------ #
    #  System tray icon                                                    #
    # ------------------------------------------------------------------ #

    def _build_tray_icon(self) -> None:
        """Create the system tray icon and its context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = app_icon_path()
        if icon_path is not None:
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("D3Macro")
        self._tray_menu = QMenu()
        self.tray_icon.setContextMenu(self._tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self._update_tray_menu()
        self.tray_icon.show()

    def _update_tray_menu(self) -> None:
        """Rebuild the tray right-click context menu."""
        if not hasattr(self, "_tray_menu"):
            return
        menu = self._tray_menu
        menu.clear()

        action_toggle = menu.addAction(tr("显示/隐藏窗口", "Show/Hide Window"))
        action_toggle.triggered.connect(self._tray_toggle_window)

        action_general = menu.addAction(tr("打开通用设置", "Open General Settings"))
        action_general.triggered.connect(self._tray_open_general)

        menu.addSeparator()

        if self.profile_tabs:
            active_idx = 1
            general_combo = self.general_widgets.get("activatedprofile")
            if general_combo is not None:
                active_idx = combo_value(general_combo)
            profile_menu = menu.addMenu(tr("切换配置", "Switch Profile"))
            for i, tab in enumerate(self.profile_tabs, start=1):
                name = tab.widgets["name"].text().strip() or tab.section_name
                display = f"{i} - {localize_text(name)}"
                action = profile_menu.addAction(display)
                action.setCheckable(True)
                action.setChecked(i == active_idx)

                def _make_switcher(idx: int):
                    return lambda _checked=False: self._tray_switch_profile(idx)

                action.triggered.connect(_make_switcher(i))
            menu.addSeparator()

        running = self._runner_is_active()
        action_start = menu.addAction(tr("启动运行器", "Start Runner"))
        action_start.triggered.connect(self.start_runner)
        action_start.setEnabled(not running)
        action_stop = menu.addAction(tr("停止运行器", "Stop Runner"))
        action_stop.triggered.connect(lambda _checked=False: self.stop_runner())
        action_stop.setEnabled(running)

        menu.addSeparator()

        action_quit = menu.addAction(tr("退出", "Quit"))
        action_quit.triggered.connect(QApplication.quit)

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._tray_toggle_window()

    def _tray_toggle_window(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _tray_open_general(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self.navigation.setCurrentRow(0)

    def _tray_switch_profile(self, index: int) -> None:
        set_combo_value(self.toolbar_profile_combo, index)
        self._update_tray_menu()

    def closeEvent(self, event) -> None:
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            super().closeEvent(event)


def main() -> int:
    if "--runner" in sys.argv[1:]:
        original_argv = sys.argv[:]
        try:
            sys.argv = [sys.argv[0]] + [arg for arg in sys.argv[1:] if arg != "--runner"]
            return runtime_main()
        finally:
            sys.argv = original_argv
    config_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else default_config_path().resolve()
    # When running from a PyInstaller bundle the Qt plugin directory is
    # isolated to the bundle.  Add system Qt6 plugin directories so Qt can
    # find the fcitx5/ibus platform-input-context plugin for CJK input.
    for _p in (
        "/usr/lib/x86_64-linux-gnu/qt6/plugins",
        "/usr/lib/aarch64-linux-gnu/qt6/plugins",
        "/usr/lib/qt6/plugins",
        "/usr/lib64/qt6/plugins",
        "/usr/lib/qt/plugins",
    ):
        if os.path.isdir(_p):
            QApplication.addLibraryPath(_p)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setTheme(Theme.LIGHT)
    setThemeColor('#2f72c4')
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
