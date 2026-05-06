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

import d3keyhelper as runtime  # noqa: E402
import d3keyhelper_gui as gui  # noqa: E402
import runner_events  # noqa: E402


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

    def test_runner_event_format_and_parse_round_trip(self) -> None:
        line = runner_events.format_runner_event("profile_switched", "配置2")
        self.assertEqual(line, "EVENT:profile_switched:配置2")
        parsed = runner_events.parse_runner_event(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.kind, "profile_switched")
        self.assertEqual(parsed.profile, "配置2")
        self.assertIsNone(runner_events.parse_runner_event("已切换配置：配置2"))

    def test_create_default_config_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            general, profiles = runtime.load_config(config_path)
            parser = gui.load_parser(config_path)
            self.assertEqual(general.activated_profile, 1)
            self.assertEqual(len(profiles), 1)
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
        runtime.set_ui_language("zh")
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

    def test_kwin_window_detection_uses_process_commandline_fallback(self) -> None:
        samples = [
            "'pid': <352866>, 'x': <0.0>, 'y': <0.0>, 'width': <3440.0>, 'height': <1440.0>",
            "'pid': <uint32 352866>, 'x': <int32 0>, 'y': <int32 0>, 'width': <int32 3440>, 'height': <int32 1440>",
        ]
        for sample in samples:
            completed = subprocess.CompletedProcess(
                args=["gdbus"],
                returncode=0,
                stdout=f"({{'caption': <'?????III'>, 'resourceClass': <'steam_app_4238117006'>, {sample}}},)",
                stderr="",
            )
            with mock.patch.object(runtime.subprocess, "run", return_value=completed), mock.patch(
                "platform_compat.read_process_commandline", return_value=r"C:\Games\Diablo III\x64\Diablo III64.exe"
            ):
                matcher = runtime.KWinWindowMatcher(title_regex="Diablo III", class_regex=None)
                window = matcher.get_active_window()
                self.assertIsNotNone(window)
                self.assertEqual(window.pid, 352866)
                self.assertEqual(window.width, 3440)
                self.assertEqual(window.height, 1440)
                self.assertTrue(matcher.matches_active_window())

    def test_build_runner_command_for_source_gui(self) -> None:
        config_path = Path("/tmp/d3oldsand.ini")
        with mock.patch.object(gui.sys, "frozen", False, create=True):
            command = gui.build_runner_command(config_path, "配置1")
        self.assertEqual(command[0], gui.sys.executable)
        self.assertEqual(command[2], "--runner")
        self.assertIn(str(config_path), command)
        profile_idx = command.index("--profile")
        self.assertEqual(command[profile_idx + 1], "配置1")
        self.assertIn("--lang", command)

    def test_gui_language_environment_supports_en_and_traditional_chinese(self) -> None:
        probe = (
            "import d3keyhelper_gui as g; "
            "print(g.UI_LANGUAGE); "
            "print(g.localize_text('鼠标右键')); "
            "print(g.localize_text('安全格状态：格式错误'))"
        )
        english = subprocess.run(
            [sys.executable, "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "D3HELPER_LANG": "en"},
            cwd=REPO_ROOT,
        )
        self.assertIn("en\nRight mouse\nSafe slots: invalid format", english.stdout)
        traditional = subprocess.run(
            [sys.executable, "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "D3HELPER_LANG": "zh_TW"},
            cwd=REPO_ROOT,
        )
        self.assertIn("zh_TW\n鼠標右鍵\n安全格狀態：格式錯誤", traditional.stdout)

    def test_gui_language_environment_defaults_to_simplified_for_unknown_locale(self) -> None:
        probe = "import d3keyhelper_gui as g; print(g.UI_LANGUAGE)"
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "D3HELPER_LANG": "", "LC_ALL": "fr_FR.UTF-8", "LC_MESSAGES": "", "LANG": ""},
            cwd=REPO_ROOT,
        )
        self.assertEqual(completed.stdout.strip(), "zh")

    def test_cli_init_and_list_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "test.ini"
            init = subprocess.run(
                [sys.executable, str(REPO_ROOT / "d3keyhelper.py"), "--init-config", "--config", str(config_path), "--lang", "zh"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("已生成默认配置文件", init.stdout)
            listed = subprocess.run(
                [sys.executable, str(REPO_ROOT / "d3keyhelper.py"), "--list-profiles", "--config", str(config_path)],
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
            # Add a second profile so we can actually switch
            parser = gui.load_parser(config_path)
            parser["配置2"] = runtime.default_profile_dict()
            with config_path.open("w", encoding="utf-16") as fh:
                fh.write("; Linux native config for D3keyHelper\r\n")
                parser.write(fh)
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

    def test_stop_macro_drains_skill_queue(self) -> None:
        """After stop_macro(), _skill_queue must be empty."""
        from enums import QueueReason
        app = self._make_macro_app()
        with app._lock:
            app._running = True
        app._skill_queue.put((runtime.SendSpec("1"), QueueReason.SPAM))
        app._skill_queue.put((runtime.SendSpec("2"), QueueReason.KEEP_BUFF))
        self.assertFalse(app._skill_queue.empty())
        app.stop_macro(reason=None)
        self.assertTrue(app._skill_queue.empty())

    def test_skill_queue_worker_exits_on_stop(self) -> None:
        """The queue worker thread exits promptly when stop_event is set."""
        import threading
        app = self._make_macro_app()
        worker_fn = app._make_skill_queue_worker(interval_ms=20)
        t = threading.Thread(target=worker_fn, daemon=True)
        t.start()
        app._stop_event.set()
        t.join(timeout=2.0)
        self.assertFalse(t.is_alive(), "Queue worker should have exited after stop_event was set")

    def test_held_keys_released_on_stop(self) -> None:
        """stop_macro() releases all held keys even if workers are still running."""
        app = self._make_macro_app()
        key_a = runtime.SendSpec("a")
        key_b = runtime.SendSpec("b")
        with app._lock:
            app._held_keys = [key_a, key_b]
            app._running = True
        released = []
        app.sender.release = lambda spec: released.append(spec)
        app.stop_macro(reason=None)
        self.assertIn(key_a, released)
        self.assertIn(key_b, released)
        self.assertEqual(app._held_keys, [])


class GuiParityTests(unittest.TestCase):
    def test_main_window_has_tooltips_and_speed_presets(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["General"]["language"] = "zh"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
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
                self.assertIn(gui.localize_text("安全格状态：未设置"), window.general_widgets["safezonestatus"].text())
                gui.set_combo_value(window.general_widgets["startmethod"], 1)
                window._refresh_general_state()
                self.assertFalse(window.general_widgets["starthotkey"].isEnabled())
                self.assertFalse(window.profile_tabs[0].widgets["skills"][5]["action"].isEnabled())
                window.general_widgets["safezone"].setText("1,2,3")
                window._refresh_general_state()
                self.assertTrue(window.general_widgets["safezone"].isEnabled())
                self.assertTrue(window.general_widgets["safezonestatus"].isVisible())
                self.assertIn(gui.localize_text("安全格状态：已设置"), window.general_widgets["safezonestatus"].text())
                window.general_widgets["safezone"].setText("bad")
                window._refresh_general_state()
                self.assertEqual(window.general_widgets["safezonestatus"].text(), gui.localize_text("安全格状态：格式错误"))
            finally:
                window.close()
                app.processEvents()

    def test_gui_loads_invalid_numeric_values_with_defaults(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["General"]["gamegamma"] = "bad"
            parser["配置1"]["movinginterval"] = "bad"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
            window = gui.MainWindow(config_path)
            try:
                self.assertAlmostEqual(window.general_widgets["gamegamma"].value(), 1.0, places=5)
                self.assertEqual(window.profile_tabs[0].widgets["movinginterval"].value(), 100)
            finally:
                window.close()
                app.processEvents()

    def test_save_config_preserves_unknown_ini_keys(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["General"]["futurekey"] = "keepme"
            parser["配置1"]["futureprofilekey"] = "keepme"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
            window = gui.MainWindow(config_path)
            try:
                self.assertTrue(window.save_config(log_message=""))
                saved = gui.load_parser(config_path)
                self.assertEqual(saved["General"]["futurekey"], "keepme")
                self.assertEqual(saved["配置1"]["futureprofilekey"], "keepme")
            finally:
                window.close()
                app.processEvents()

    def test_duplicate_profile_names_do_not_overwrite_sections(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["配置2"] = runtime.default_profile_dict()
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
            window = gui.MainWindow(config_path)
            try:
                window.profile_tabs[0].widgets["name"].setText("same")
                window.profile_tabs[1].widgets["name"].setText("same")
                with mock.patch.object(gui.QMessageBox, "warning"):
                    self.assertFalse(window.save_config(log_message=""))
                saved = gui.load_parser(config_path)
                self.assertEqual([s for s in saved.sections() if s.lower() != "general"], ["配置1", "配置2"])
            finally:
                window.close()
                app.processEvents()

    def test_compact_mode_and_profile_state_sync(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["General"]["language"] = "zh"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
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
                self.assertEqual(window.navigation.item(0).text(), gui.tr("通用", "General"))
                self.assertNotIn("statusconfig", window.general_widgets)
                self.assertNotIn("compactmode", window.general_widgets)
                original_size = (window.width(), window.height())
                window._set_log_expanded(True)
                app.processEvents()
                self.assertTrue(window.log.isVisible())
                self.assertTrue(window.log_panel.isVisible())
                self.assertTrue(window.status_strip.isVisible())
                self.assertIn(gui.tr("已载入配置", "Loaded config"), window.status_log_value.toolTip())
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
            parser = gui.load_parser(config_path)
            parser["General"]["language"] = "zh"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
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

    def test_stop_runner_logs_stop_message(self) -> None:
        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            window = gui.MainWindow(config_path)
            try:
                process = mock.Mock()
                process.state.return_value = gui.QProcess.ProcessState.Running
                process.waitForFinished.return_value = True
                window.process = process
                window.stop_runner()
                self.assertIn(gui.localize_text("已停止运行器。"), window.log.toPlainText())
                process.terminate.assert_called_once()
                self.assertIsNone(window.process)
            finally:
                window.close()
                app.processEvents()

    def test_language_selection_persists_and_rebuilds_gui(self) -> None:
        app = get_qt_app()
        previous_language = gui.UI_LANGUAGE
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "d3oldsand.ini"
            runtime.create_default_config(config_path)
            parser = gui.load_parser(config_path)
            parser["General"]["language"] = "zh"
            with config_path.open("w", encoding="utf-16") as handle:
                handle.write("; Linux GUI config for D3keyHelper\r\n")
                parser.write(handle)
            window = gui.MainWindow(config_path)
            try:
                window._lang_btns["en"].click()
                app.processEvents()
                parser = gui.load_parser(config_path)
                self.assertEqual(parser["General"]["language"], "en")
                self.assertEqual(gui.UI_LANGUAGE, "en")
                self.assertEqual(window.navigation.item(0).text(), "General")
                self.assertEqual(window.toolbar_profile_combo.itemText(0), "1 - Profile 1")
                self.assertTrue(window._lang_btns["en"].isChecked())
            finally:
                window.close()
                app.processEvents()
                gui.set_ui_language(previous_language)

    def test_config_round_trip_no_field_loss(self) -> None:
        """Default config -> GUI save -> runtime load: no INI key is lost.

        Reads the raw keys before and after GUI save and asserts the set of
        keys only grows (never shrinks).  GUI-only keys like ``language`` are
        allowed as new additions; runtime-required keys must all survive.
        """
        import configparser as _cp

        def _ini_keys(path: Path) -> dict[str, set[str]]:
            """Return {section_lower: {key, ...}} for every section."""
            p = _cp.ConfigParser(interpolation=None)
            p.optionxform = str.lower
            for enc in ("utf-16", "utf-8-sig", "utf-8"):
                try:
                    with path.open("r", encoding=enc) as f:
                        p.read_file(f)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            return {s.lower(): set(p.options(s)) for s in p.sections()}

        app = get_qt_app()
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "rt.ini"
            runtime.create_default_config(cfg)
            keys_before = _ini_keys(cfg)

            w = gui.MainWindow(cfg)
            try:
                w.save_config()
            finally:
                w.close()
            app.processEvents()
            keys_after = _ini_keys(cfg)

        # Every section present before must still exist
        for section in keys_before:
            self.assertIn(section, keys_after, f"Section [{section}] disappeared after GUI save")
            missing = keys_before[section] - keys_after[section]
            self.assertFalse(
                missing,
                f"Keys lost in [{section}] after GUI save: {missing}",
            )

        # Runtime load must succeed and produce sane values
        with tempfile.TemporaryDirectory() as tmpdir2:
            cfg2 = Path(tmpdir2) / "rt2.ini"
            runtime.create_default_config(cfg2)
            w2 = gui.MainWindow(cfg2)
            try:
                w2.save_config()
            finally:
                w2.close()
            app.processEvents()
            general, profiles = runtime.load_config(cfg2)

        self.assertGreater(len(profiles), 0)
        self.assertEqual(general.game_resolution, "Auto")
        self.assertAlmostEqual(general.game_gamma, 1.0, places=5)
        p = profiles[0]
        self.assertEqual(len(p.skills), 6)
        self.assertEqual(p.skills[0].interval_ms, 300)
        self.assertEqual(p.skills[4].interval_ms, 300)


class PackageImportTests(unittest.TestCase):
    """Verify that the modules import cleanly when used as a package."""

    def test_package_import_runtime(self) -> None:
        """d3keyhelper must be importable from its parent directory."""
        parent = str(REPO_ROOT.parent)
        result = subprocess.run(
            [sys.executable, "-c", "import D3keyHelperForLinux.d3keyhelper"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": parent},
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Package import failed:\n{result.stderr}",
        )

    def test_package_import_gui(self) -> None:
        """d3keyhelper_gui must be importable from its parent directory."""
        parent = str(REPO_ROOT.parent)
        env = {**os.environ, "PYTHONPATH": parent, "QT_QPA_PLATFORM": "offscreen"}
        result = subprocess.run(
            [sys.executable, "-c", "import D3keyHelperForLinux.d3keyhelper_gui"],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Package GUI import failed:\n{result.stderr}",
        )


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

    def test_scan_inventory_safezone_overflow_protection(self) -> None:
        width, height = 2560, 1440
        # BGRA [8, 12, 15, 255] → RGB [15, 12, 8]: dark, R>B and G>B → detected as empty
        pixels = np.full((height, width, 4), [8, 12, 15, 255], dtype=np.uint8)
        # BGRA [50, 50, 50, 255] → RGB [50, 50, 50]: R≥22 → detected as has-item
        item_pixel = np.array([50, 50, 50, 255], dtype=np.uint8)
        detection_points = [(0.65625, 0.71429), (0.375, 0.36508), (0.725, 0.251)]

        def mark_slot_as_item(slot_id: int) -> None:
            _, _, x0, y0 = runtime.get_inventory_space_xy(width, height, slot_id, "bag")
            for px, py in detection_points:
                x = round(x0 + 64 * px * height / 1440.0)
                y = round(y0 + 63 * py * height / 1440.0)
                pixels[y, x] = item_pixel

        # Safezone covers row 2 (slots 11–13). Place items in those safezone slots AND
        # directly below them (slots 21–23) to simulate 2-tall items overflowing into row 3.
        for slot in [11, 12, 13, 21, 22, 23]:
            mark_slot_as_item(slot)

        image = runtime.GameImage(
            runtime.WindowInfo(0, "", "", 0, 0, width, height), pixels, 1.0
        )
        safezone = {11, 12, 13}
        bag_zone, _ = runtime.scan_inventory_space(image, width, height, safezone)

        # Safezone slots must be 0
        self.assertEqual(bag_zone[11], 0)
        self.assertEqual(bag_zone[12], 0)
        self.assertEqual(bag_zone[13], 0)
        # Overflow slots directly below safezone item slots must also be protected (0)
        self.assertEqual(bag_zone[21], 0, "overflow below safezone slot 11 must be protected")
        self.assertEqual(bag_zone[22], 0, "overflow below safezone slot 12 must be protected")
        self.assertEqual(bag_zone[23], 0, "overflow below safezone slot 13 must be protected")
        # Unrelated empty slots remain 1
        self.assertEqual(bag_zone[1], 1)
        self.assertEqual(bag_zone[60], 1)


if __name__ == "__main__":
    unittest.main()
