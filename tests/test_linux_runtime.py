from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path
from unittest import mock

import numpy as np
from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import d3keyhelper_linux as runtime
import d3keyhelper_linux_gui as gui


def get_qt_app() -> QApplication:
    app = QApplication.instance()
    if app is not None:
        return app
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication(["test", "-platform", "offscreen"])


class ConfigTests(unittest.TestCase):
    def _make_macro_app(self) -> runtime.MacroApp:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        config_path = Path(tmp_dir.name) / "d3oldsand.ini"
        runtime.create_default_config(config_path)
        general, profiles = runtime.load_config(config_path)
        sender = mock.Mock()
        sender._filter = runtime.SyntheticEventFilter()
        return runtime.MacroApp(general, profiles, 0, sender, matcher=None, capture_backend="x11")

    def test_parse_safezone(self) -> None:
        self.assertEqual(runtime.parse_safezone("1, 2, 60, 61, foo"), {1, 2, 60})

    def test_create_default_config_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            general, profiles = runtime.load_config(config_path)
            parser = gui.load_parser(config_path)
            self.assertEqual(general.activated_profile, 1)
            self.assertEqual(len(profiles), 4)
            self.assertEqual(profiles[0].name, "配置1")
            self.assertEqual(profiles[0].skills[0].hotkey.base, "1")
            self.assertEqual(general.helper.max_reforge, 10)
            self.assertTrue(general.sound_on_profile_switch)
            self.assertEqual(parser["General"]["sendmode"], "Event")
            self.assertEqual(parser["General"]["compactmode"], "0")

    def test_default_config_path_uses_xdg_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp_dir}, clear=False):
            config_path = runtime.default_config_path()
            self.assertEqual(config_path, Path(tmp_dir) / "d3helperforlinux" / "d3oldsand.ini")
            runtime.create_default_config(config_path)
            self.assertTrue(config_path.exists())

    def test_describe_enabled_helpers(self) -> None:
        helper = runtime.HelperConfig(
            hotkey=runtime.HotkeySpec("f5"),
            gamble_enabled=False,
            gamble_times=15,
            loot_enabled=True,
            loot_times=30,
            salvage_enabled=True,
            salvage_method=1,
            reforge_enabled=False,
            reforge_method=1,
            upgrade_enabled=True,
            convert_enabled=False,
            abandon_enabled=False,
            mouse_speed=2,
            animation_delay_ms=150,
            max_reforge=10,
            safezone=set(),
        )
        self.assertEqual(runtime.describe_enabled_helpers(helper), ["拾取", "分解", "升级"])

    def test_proton_window_detection_uses_process_commandline(self) -> None:
        window = runtime.WindowInfo(
            window_id=1,
            title="?????III",
            wm_class="steam_app_4238117006 steam_app_4238117006",
            x=0,
            y=0,
            width=3840,
            height=2160,
            pid=352866,
            commandline=r"C:\Program Files (x86)\Diablo III\x64\Diablo III64.exe OnlineService.SSO=true -launch -uid d3cn",
        )
        self.assertTrue(runtime.looks_like_proton_diablo_window(window))

    def test_build_runner_command_for_source_gui(self) -> None:
        config_path = Path("/tmp/d3oldsand.ini")
        with mock.patch.object(gui.sys, "frozen", False, create=True):
            command = gui.build_runner_command(config_path, "配置1")
        self.assertEqual(command[0], gui.sys.executable)
        self.assertEqual(command[2], "--runner")
        self.assertIn(str(config_path), command)
        self.assertEqual(command[-1], "配置1")

    def test_cli_init_and_list_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test.ini"
            init = subprocess.run(
                [sys.executable, str(REPO_ROOT / "d3keyhelper_linux.py"), "--init-config", "--config", str(config_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("已生成默认配置文件", init.stdout)
            listed = subprocess.run(
                [sys.executable, str(REPO_ROOT / "d3keyhelper_linux.py"), "--list-profiles", "--config", str(config_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("1. 配置1", listed.stdout)

    def test_helper_speed_preset_mapping(self) -> None:
        self.assertEqual(gui.helper_speed_preset_from_values(0, 50), 1)
        self.assertEqual(gui.helper_speed_preset_from_values(1, 100), 2)
        self.assertEqual(gui.helper_speed_preset_from_values(2, 150), 3)
        self.assertEqual(gui.helper_speed_preset_from_values(3, 200), 4)
        self.assertEqual(gui.helper_speed_preset_from_values(4, 175), 5)

    def test_classify_safezone_text_supports_legacy_default(self) -> None:
        self.assertEqual(gui.classify_safezone_text("61,62,63")[0], "legacy-default")
        self.assertEqual(gui.classify_safezone_text("1,2,3"), ("set", {1, 2, 3}))
        self.assertEqual(gui.classify_safezone_text("0,99"), ("unset", set()))
        self.assertEqual(gui.classify_safezone_text("1,bad")[0], "invalid")

    def test_switch_profile_plays_sound_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            general, profiles = runtime.load_config(config_path)
            sender = mock.Mock()
            sender._filter = mock.Mock()
            app = runtime.MacroApp(general, profiles, 0, sender, matcher=None, capture_backend="x11")
            with mock.patch.object(runtime, "play_notification_sound") as play_sound:
                app.switch_profile(1)
            play_sound.assert_called_once()

    def test_default_profile_does_not_require_mouse_listener(self) -> None:
        app = self._make_macro_app()
        self.assertTrue(app.needs_keyboard_listener())
        self.assertFalse(app.needs_mouse_listener())

    def test_mouse_listener_enabled_for_mouse_hotkeys(self) -> None:
        app = self._make_macro_app()
        app.general.helper.hotkey = runtime.HotkeySpec("mouse:x1")
        app._refresh_input_watch()
        self.assertTrue(app.needs_mouse_listener())

    def test_irrelevant_mouse_press_is_ignored(self) -> None:
        app = self._make_macro_app()
        app.on_key_press("mouse:left")
        self.assertEqual(app._pressed_bases, set())
        app.on_key_press("f2")
        self.assertIn("f2", app._pressed_bases)

    def test_live_buff_check_uses_region_capture(self) -> None:
        app = self._make_macro_app()
        window = runtime.WindowInfo(1, "Diablo III", "class", 0, 0, 3440, 1440)

        class FakeCapture:
            def __init__(self):
                self.calls = []

            def get_active_window(self):
                return window

            def capture_region(self, point_x, point_y, width, height):
                self.calls.append((point_x, point_y, width, height))
                pixels = np.zeros((1, 1, 4), dtype=np.uint8)
                pixels[0, 0] = [10, 120, 10, 255]
                return window, pixels

        fake_capture = FakeCapture()
        app._capture = fake_capture
        self.assertTrue(app._is_buff_active_live(3440, 1440, 1))
        self.assertEqual(len(fake_capture.calls), 1)
        self.assertEqual(fake_capture.calls[0][2:], (1, 1))

    def test_region_rgb_converts_small_capture_without_full_frame(self) -> None:
        app = self._make_macro_app()
        window = runtime.WindowInfo(1, "Diablo III", "class", 0, 0, 3440, 1440)

        class FakeCapture:
            def get_active_window(self):
                return window

            def capture_region(self, point_x, point_y, width, height):
                pixels = np.zeros((2, 2, 4), dtype=np.uint8)
                pixels[:, :] = [30, 20, 10, 255]
                return window, pixels

        app._capture = FakeCapture()
        region = app._capture_region_rgb(10, 20, 2, 2)
        self.assertEqual(region, [[10, 10, 10, 10], [20, 20, 20, 20], [30, 30, 30, 30]])


class GuiParityTests(unittest.TestCase):
    def test_main_window_has_tooltips_and_speed_presets(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                self.assertFalse(window.log_panel.isVisible())
                self.assertIn("升级页面", window.general_widgets["enableupgradehelper"].toolTip())
                self.assertIn("智能分解", window.general_widgets["salvagehelpermethod"].toolTip())
                self.assertEqual(
                    window.general_widgets["helpermousespeed"].buttonSymbols(),
                    gui.QAbstractSpinBox.ButtonSymbols.NoButtons,
                )
                self.assertEqual(
                    window.general_widgets["gamegamma"].buttonSymbols(),
                    gui.QAbstractSpinBox.ButtonSymbols.NoButtons,
                )
                self.assertEqual(gui.combo_value(window.general_widgets["helperspeed"]), 3)
                window.general_widgets["helperspeed"].setCurrentIndex(0)
                self.assertEqual(window.general_widgets["helpermousespeed"].value(), 0)
                self.assertEqual(window.general_widgets["helperanimationdelay"].value(), 50)
                window.general_widgets["helperanimationdelay"].setValue(175)
                self.assertEqual(gui.combo_value(window.general_widgets["helperspeed"]), 5)
            finally:
                window.close()
                app.processEvents()

    def test_general_dynamic_controls_and_safezone_status(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                window.show()
                app.processEvents()
                self.assertTrue(window.general_widgets["starthotkey"].isEnabled())
                self.assertTrue(window.general_widgets["oldsandhelperhk"].isEnabled())
                self.assertFalse(window.general_widgets["safezonestatus"].isVisible())
                window.general_widgets["enableupgradehelper"].setChecked(True)
                window._refresh_general_state()
                self.assertIn("原版默认值", window.general_widgets["safezonestatus"].text())
                gui.set_combo_value(window.general_widgets["startmethod"], 1)
                window._refresh_general_state()
                self.assertFalse(window.general_widgets["starthotkey"].isEnabled())
                self.assertFalse(window.profile_tabs[0].widgets["skills"][5]["action"].isEnabled())
                window.general_widgets["safezone"].setText("1,2,3")
                window._refresh_general_state()
                self.assertTrue(window.general_widgets["safezone"].isEnabled())
                self.assertTrue(window.general_widgets["safezonestatus"].isVisible())
                self.assertIn("已设置", window.general_widgets["safezonestatus"].text())
                window.general_widgets["safezone"].setText("bad")
                window._refresh_general_state()
                self.assertEqual(window.general_widgets["safezonestatus"].text(), "安全格状态：格式错误")
            finally:
                window.close()
                app.processEvents()

    def test_compact_mode_and_profile_state_sync(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                window.show()
                app.processEvents()
                profile = window.profile_tabs[0]
                gui.set_combo_value(profile.widgets["lazymode"], 3)
                profile.refresh_dynamic_state()
                self.assertFalse(profile.widgets["useskillqueue"].isEnabled())
                self.assertFalse(profile.widgets["movingmethod"].isEnabled())
                self.assertFalse(profile.widgets["potionmethod"].isEnabled())
                self.assertFalse(profile.widgets["enablequickpause"].isEnabled())
                gui.set_combo_value(profile.widgets["lazymode"], 1)
                profile.widgets["useskillqueue"].setChecked(True)
                profile.widgets["useskillqueueinterval"].setValue(400)
                row = profile.widgets["skills"][0]
                gui.set_combo_value(row["action"], 3)
                row["interval"].setValue(100)
                profile.refresh_dynamic_state()
                app.processEvents()
                self.assertFalse(profile.skill_queue_warning.isHidden())
                self.assertEqual(window.navigation.item(0).text(), "通用")
                self.assertNotIn("statusconfig", window.general_widgets)
                self.assertNotIn("compactmode", window.general_widgets)
                original_size = (window.width(), window.height())
                window._set_log_expanded(True)
                app.processEvents()
                self.assertTrue(window.log.isVisible())
                self.assertTrue(window.log_panel.isVisible())
                self.assertTrue(window.status_strip.isVisible())
                self.assertIn("已载入配置", window.status_log_value.toolTip())
                self.assertEqual(window.path_label.toolTip(), str(config_path))
                self.assertEqual((window.width(), window.height()), original_size)
            finally:
                window.close()
                app.processEvents()

    def test_save_config_preserves_linux_gui_parity_fields(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                gui.set_combo_value(window.general_widgets["sendmode"], "Input")
                window.general_widgets["enablesoundplay"].setChecked(False)
                window.save_config(log_message="")
                parser = gui.load_parser(config_path)
                self.assertEqual(parser["General"]["sendmode"], "Input")
                self.assertEqual(parser["General"]["enablesoundplay"], "0")
                self.assertEqual(parser["General"]["compactmode"], "0")
            finally:
                window.close()
                app.processEvents()

    def test_live_config_change_saves_when_idle(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                with mock.patch.object(window, "save_config") as save_config, mock.patch.object(
                    window, "_launch_runner"
                ) as launch_runner:
                    window._apply_live_config_change()
                save_config.assert_called_once_with(log_message="已自动保存配置。")
                launch_runner.assert_not_called()
            finally:
                window.close()
                app.processEvents()

    def test_live_config_change_restarts_when_running(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                window.process = mock.Mock()
                window.process.state.return_value = gui.QProcess.ProcessState.Running
                with mock.patch.object(window, "save_config") as save_config, mock.patch.object(
                    window, "_launch_runner"
                ) as launch_runner:
                    window._apply_live_config_change()
                save_config.assert_called_once_with(log_message="已自动保存配置。")
                launch_runner.assert_called_once_with(save_first=False, log_message="检测到配置变更，已自动重启运行器。")
            finally:
                window.close()
                app.processEvents()


class GeometryTests(unittest.TestCase):
    def test_parse_resolution(self) -> None:
        self.assertEqual(runtime.parse_resolution("1920x1080"), (1920, 1080))
        self.assertIsNone(runtime.parse_resolution("Auto"))

    def test_inventory_slot_positions(self) -> None:
        center_x, center_y, _, _ = runtime.get_inventory_space_xy(2560, 1440, 1, "bag")
        self.assertGreater(center_x, 0)
        self.assertGreater(center_y, 0)
        self.assertEqual(len(runtime.get_kanai_cube_button_pos(1440)), 4)
        self.assertEqual(len(runtime.get_salvage_icon_xy(1440, "center")), 4)


class ImageTests(unittest.TestCase):
    def test_game_image_pixel_access(self) -> None:
        pixels = np.zeros((10, 10, 4), dtype=np.uint8)
        pixels[2, 3] = [10, 20, 30, 255]
        image = runtime.GameImage(
            runtime.WindowInfo(0, "title", "class", 0, 0, 10, 10),
            pixels,
            1.0,
        )
        self.assertEqual(image.get_pixel_rgb((3, 2)), [30, 20, 10])

    def test_arrays_equal(self) -> None:
        self.assertTrue(runtime.arrays_equal([1, 2, 3], [1, 2, 3], 0))
        self.assertTrue(runtime.arrays_equal([1, 2, 3], [1, 3, 3], 1))
        self.assertFalse(runtime.arrays_equal([1, 2, 3], [1, 4, 3], 1))

    def test_kanai_upgrade_page_detects_without_title_or_shell(self) -> None:
        width = 3440
        height = 1440
        pixels = np.zeros((height, width, 4), dtype=np.uint8)
        pixels[406, 799] = [150, 200, 240, 255]
        pixels[592, 795] = [100, 180, 230, 255]
        image = runtime.GameImage(
            runtime.WindowInfo(0, "", "steam_app_4238117006 steam_app_4238117006", 0, 0, width, height),
            pixels,
            1.0,
        )
        self.assertEqual(runtime.is_kanai_cube_open(image, width, height, ""), 3)

    def test_salvage_mode_is_armed_detection(self) -> None:
        self.assertTrue(runtime.salvage_mode_is_armed([2, [220, 220, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]))
        self.assertFalse(runtime.salvage_mode_is_armed([2, [120, 120, 20], [0, 0, 0], [0, 0, 0], [0, 0, 0]]))

    def test_salvage_bulk_buttons_from_state(self) -> None:
        salvage_state = [2, [0, 0, 0], [80, 10, 10], [10, 20, 100], [80, 30, 10]]
        self.assertEqual(runtime.salvage_bulk_buttons_from_state(salvage_state), [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
