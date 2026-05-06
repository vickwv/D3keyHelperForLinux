from __future__ import annotations
import configparser
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from pynput import mouse as _mouse
except ImportError:
    _mouse = None

try:
    from .config_schema import (
        build_general_section, gd, pd, sd, skill_hotkey_default,
        default_profile_dict as _schema_default_profile_dict,
    )
    from .enums import (  # noqa: F401
        MovingMethod, PotionMethod, QuickPauseAction, QuickPauseMode,
        QueueReason, ReforgeMethod, SalvageMethod, SkillAction, StartMode,
    )
except ImportError:
    from config_schema import (  # type: ignore[no-redef]
        build_general_section, gd, pd, sd, skill_hotkey_default,
        default_profile_dict as _schema_default_profile_dict,
    )
    from enums import (  # type: ignore[no-redef]  # noqa: F401
        MovingMethod, PotionMethod, QuickPauseAction, QuickPauseMode,
        QueueReason, ReforgeMethod, SalvageMethod, SkillAction, StartMode,
    )

DEFAULT_VERSION = "260403"
CONFIG_DIR_NAME = "d3helperforlinux"
CONFIG_FILE_NAME = "d3oldsand.ini"
DEFAULT_PROFILE_NAMES = ["配置1"]
START_METHOD_MOUSE = {
    1: "mouse:right",
    2: "mouse:middle",
    3: "wheel_up",
    4: "wheel_down",
    5: "mouse:x1",
    6: "mouse:x2",
}
COMMON_METHOD_MOUSE = {
    2: "mouse:middle",
    3: "wheel_up",
    4: "wheel_down",
    5: "mouse:x1",
    6: "mouse:x2",
}
QUICK_PAUSE_MOUSE = {
    1: "mouse:left",
    2: "mouse:right",
    3: "mouse:middle",
    4: "mouse:x1",
    5: "mouse:x2",
}
HOTKEY_MODIFIER_PREFIX = {"^": "ctrl", "!": "alt", "+": "shift", "#": "cmd"}
HOTKEY_MODIFIER_NAMES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "lctrl": "ctrl",
    "rctrl": "ctrl",
    "alt": "alt",
    "lalt": "alt",
    "ralt": "alt",
    "altgr": "alt",
    "shift": "shift",
    "lshift": "shift",
    "rshift": "shift",
    "win": "cmd",
    "lwin": "cmd",
    "rwin": "cmd",
    "cmd": "cmd",
    "super": "cmd",
}
SPECIAL_KEY_ALIASES = {
    "esc": "esc",
    "escape": "esc",
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "bs": "backspace",
    "delete": "delete",
    "del": "delete",
    "insert": "insert",
    "ins": "insert",
    "home": "home",
    "end": "end",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "pgup": "page_up",
    "pgdn": "page_down",
    "pageup": "page_up",
    "pagedown": "page_down",
    "capslock": "caps_lock",
    "numlock": "num_lock",
    "scrolllock": "scroll_lock",
    "printscreen": "print_screen",
    "appskey": "menu",
    "browser_back": "browser_back",
    "browser_forward": "browser_forward",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "alt_l": "alt",
    "alt_r": "alt",
    "alt_gr": "alt",
    "shift_l": "shift",
    "shift_r": "shift",
    "cmd_l": "cmd",
    "cmd_r": "cmd",
    "super_l": "cmd",
    "super_r": "cmd",
}
MOUSE_EVENT_ALIASES = {
    "lbutton": "mouse:left",
    "rbutton": "mouse:right",
    "mbutton": "mouse:middle",
    "xbutton1": "mouse:x1",
    "xbutton2": "mouse:x2",
    "wheelup": "wheel_up",
    "wheeldown": "wheel_down",
}
MOUSE_BUTTONS = {
    "mouse:left": lambda: _mouse.Button.left,
    "mouse:right": lambda: _mouse.Button.right,
    "mouse:middle": lambda: _mouse.Button.middle,
    "mouse:x1": lambda: getattr(_mouse.Button, "x1"),
    "mouse:x2": lambda: getattr(_mouse.Button, "x2"),
}
SYNTHETIC_PHASE_PRESS = "press"
SYNTHETIC_PHASE_RELEASE = "release"

@dataclass(frozen=True)
class HotkeySpec:
    base: str
    modifiers: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SendSpec:
    base: str


@dataclass
class SkillConfig:
    hotkey: SendSpec | None
    action: int
    interval_ms: int
    delay_ms: int
    randomize_delay: bool
    priority: int
    repeat: int
    repeat_interval_ms: int
    trigger: HotkeySpec | None


@dataclass
class QuickPauseConfig:
    enabled: bool
    mode: int
    trigger: HotkeySpec | None
    action: int
    delay_ms: int


@dataclass
class ProfileConfig:
    name: str
    skills: list[SkillConfig]
    profile_hotkey: HotkeySpec | None
    autostart_macro: bool
    start_mode: int
    moving_method: int
    moving_interval_ms: int
    potion_method: int
    potion_interval_ms: int
    use_skill_queue: bool
    use_skill_queue_interval_ms: int
    quick_pause: QuickPauseConfig


@dataclass
class HelperConfig:
    hotkey: HotkeySpec | None
    gamble_enabled: bool
    gamble_times: int
    loot_enabled: bool
    loot_times: int
    salvage_enabled: bool
    salvage_method: int
    reforge_enabled: bool
    reforge_method: int
    upgrade_enabled: bool
    convert_enabled: bool
    abandon_enabled: bool
    mouse_speed: int
    animation_delay_ms: int
    max_reforge: int
    safezone: set[int]


@dataclass
class GeneralConfig:
    activated_profile: int
    start_hotkey: HotkeySpec | None
    run_on_start: bool
    d3only: bool
    smart_pause: bool
    sound_on_profile_switch: bool
    custom_standing_enabled: bool
    custom_standing_key: SendSpec
    custom_moving_enabled: bool
    custom_moving_key: SendSpec
    custom_potion_enabled: bool
    custom_potion_key: SendSpec
    game_gamma: float
    buff_percent: float
    game_resolution: str
    helper: HelperConfig


@dataclass
class WindowInfo:
    window_id: int
    title: str
    wm_class: str
    x: int
    y: int
    width: int
    height: int
    pid: int = 0
    commandline: str = ""


class ConfigError(RuntimeError):
    pass
def normalize_token(raw: str) -> str:
    return raw.strip().replace(" ", "").lower()


def parse_hotkey_expression(expr: str) -> HotkeySpec | None:
    expr = expr.strip()
    if not expr:
        return None
    modifiers: set[str] = set()
    while expr and expr[0] in HOTKEY_MODIFIER_PREFIX:
        modifiers.add(HOTKEY_MODIFIER_PREFIX[expr[0]])
        expr = expr[1:]
    expr = expr.strip()
    if not expr:
        return None
    if "+" in expr:
        parts = [part.strip() for part in expr.split("+") if part.strip()]
        if len(parts) > 1:
            maybe_modifiers = [normalize_token(part) for part in parts[:-1]]
            if all(part in HOTKEY_MODIFIER_NAMES for part in maybe_modifiers):
                modifiers.update(HOTKEY_MODIFIER_NAMES[part] for part in maybe_modifiers)
                expr = parts[-1]
    base = normalize_hotkey_base(expr)
    if base is None:
        return None
    return HotkeySpec(base=base, modifiers=frozenset(modifiers))


def normalize_hotkey_base(raw: str) -> str | None:
    token = normalize_token(raw)
    if not token:
        return None
    if token in MOUSE_EVENT_ALIASES:
        return MOUSE_EVENT_ALIASES[token]
    if token in HOTKEY_MODIFIER_NAMES:
        return HOTKEY_MODIFIER_NAMES[token]
    if token in SPECIAL_KEY_ALIASES:
        return SPECIAL_KEY_ALIASES[token]
    if re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", token):
        return token
    if re.fullmatch(r"[a-z0-9]", token):
        return token
    numpad_match = re.fullmatch(r"numpad([0-9])", token)
    if numpad_match:
        return numpad_match.group(1)
    numpad_alias = {
        "numpaddot": ".",
        "numpaddiv": "/",
        "numpadmult": "*",
        "numpadsub": "-",
        "numpadadd": "+",
    }
    if token in numpad_alias:
        return numpad_alias[token]
    punctuation = {
        "`": "`",
        "~": "`",
        "-": "-",
        "=": "=",
        "[": "[",
        "]": "]",
        "\\": "\\",
        ";": ";",
        "'": "'",
        ",": ",",
        ".": ".",
        "/": "/",
    }
    if token in punctuation:
        return punctuation[token]
    return None


def parse_send_spec(expr: str) -> SendSpec | None:
    base = normalize_hotkey_base(expr)
    if base is None:
        return None
    if base in {"wheel_up", "wheel_down"}:
        return None
    return SendSpec(base=base)


def parse_boolean(value: str, default: bool) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def parse_int(value: str, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_float(value: str, default: float) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_safezone(value: str) -> set[int]:
    out: set[int] = set()
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            number = int(part)
        except ValueError:
            continue
        if 1 <= number <= 60:
            out.add(number)
    return out


def method_to_hotkey(method: int, keyboard_expr: str, mapping: dict[int, str]) -> HotkeySpec | None:
    if method in mapping:
        return HotkeySpec(mapping[method])
    if method == 7:
        return parse_hotkey_expression(keyboard_expr)
    return None


def load_config(config_path: Path) -> tuple[GeneralConfig, list[ProfileConfig]]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower

    encodings = ["utf-16", "utf-8-sig", "utf-8"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with config_path.open("r", encoding=encoding) as handle:
                parser.read_file(handle)
            break
        except FileNotFoundError as exc:
            raise ConfigError(f"配置文件不存在：{config_path}") from exc
        except Exception as exc:
            last_error = exc
    else:
        raise ConfigError(f"无法读取配置文件：{config_path} ({last_error})")

    general_name = next((name for name in parser.sections() if name.lower() == "general"), None)
    if general_name is None:
        raise ConfigError("配置文件缺少 [General] 区块。")
    general_section = parser[general_name]
    profile_names = [name for name in parser.sections() if name.lower() != "general"]
    if not profile_names:
        raise ConfigError("配置文件中没有任何技能配置区块。")

    general = GeneralConfig(
        activated_profile=max(parse_int(general_section.get("activatedprofile", gd("activatedprofile")), 1), 1),
        start_hotkey=method_to_hotkey(
            parse_int(general_section.get("startmethod", gd("startmethod")), 7),
            general_section.get("starthotkey", gd("starthotkey")),
            START_METHOD_MOUSE,
        ),
        run_on_start=parse_boolean(general_section.get("runonstart", gd("runonstart")), True),
        d3only=parse_boolean(general_section.get("d3only", gd("d3only")), True),
        smart_pause=parse_boolean(general_section.get("enablesmartpause", gd("enablesmartpause")), True),
        sound_on_profile_switch=parse_boolean(general_section.get("enablesoundplay", gd("enablesoundplay")), True),
        custom_standing_enabled=parse_boolean(general_section.get("customstanding", gd("customstanding")), False),
        custom_standing_key=parse_send_spec(general_section.get("customstandinghk", gd("customstandinghk"))) or SendSpec("shift"),
        custom_moving_enabled=parse_boolean(general_section.get("custommoving", gd("custommoving")), False),
        custom_moving_key=parse_send_spec(general_section.get("custommovinghk", gd("custommovinghk"))) or SendSpec("e"),
        custom_potion_enabled=parse_boolean(general_section.get("custompotion", gd("custompotion")), False),
        custom_potion_key=parse_send_spec(general_section.get("custompotionhk", gd("custompotionhk"))) or SendSpec("q"),
        game_gamma=parse_float(general_section.get("gamegamma", gd("gamegamma")), 1.0),
        buff_percent=parse_float(general_section.get("buffpercent", gd("buffpercent")), 0.05),
        game_resolution=general_section.get("gameresolution", gd("gameresolution")),
        helper=HelperConfig(
            hotkey=method_to_hotkey(
                parse_int(general_section.get("oldsandhelpermethod", gd("oldsandhelpermethod")), 7),
                general_section.get("oldsandhelperhk", gd("oldsandhelperhk")),
                COMMON_METHOD_MOUSE,
            ),
            gamble_enabled=parse_boolean(general_section.get("enablegamblehelper", gd("enablegamblehelper")), True),
            gamble_times=max(parse_int(general_section.get("gamblehelpertimes", gd("gamblehelpertimes")), 15), 1),
            loot_enabled=parse_boolean(general_section.get("enableloothelper", gd("enableloothelper")), False),
            loot_times=max(parse_int(general_section.get("loothelpertimes", gd("loothelpertimes")), 30), 1),
            salvage_enabled=parse_boolean(general_section.get("enablesalvagehelper", gd("enablesalvagehelper")), False),
            salvage_method=parse_int(general_section.get("salvagehelpermethod", gd("salvagehelpermethod")), 1),
            reforge_enabled=parse_boolean(general_section.get("enablereforgehelper", gd("enablereforgehelper")), False),
            reforge_method=parse_int(general_section.get("reforgehelpermethod", gd("reforgehelpermethod")), 1),
            upgrade_enabled=parse_boolean(general_section.get("enableupgradehelper", gd("enableupgradehelper")), False),
            convert_enabled=parse_boolean(general_section.get("enableconverthelper", gd("enableconverthelper")), False),
            abandon_enabled=parse_boolean(general_section.get("enableabandonhelper", gd("enableabandonhelper")), False),
            mouse_speed=max(parse_int(general_section.get("helpermousespeed", gd("helpermousespeed")), 2), 0),
            animation_delay_ms=max(parse_int(general_section.get("helperanimationdelay", gd("helperanimationdelay")), 150), 1),
            max_reforge=max(parse_int(general_section.get("maxreforge", gd("maxreforge")), 10), 1),
            safezone=parse_safezone(general_section.get("safezone", gd("safezone"))),
        ),
    )

    profiles: list[ProfileConfig] = []
    for section_name in profile_names:
        section = parser[section_name]
        skills: list[SkillConfig] = []
        for index in range(1, 7):
            action = parse_int(section.get(f"action_{index}", sd("action")), 1)
            skills.append(
                SkillConfig(
                    hotkey=parse_send_spec(section.get(f"skill_{index}", skill_hotkey_default(index))),
                    action=action,
                    interval_ms=max(parse_int(section.get(f"interval_{index}", sd("interval")), 300), 20),
                    delay_ms=parse_int(section.get(f"delay_{index}", sd("delay")), 10),
                    randomize_delay=parse_boolean(section.get(f"random_{index}", sd("random")), True),
                    priority=max(parse_int(section.get(f"priority_{index}", sd("priority")), 1), 1),
                    repeat=max(parse_int(section.get(f"repeat_{index}", sd("repeat")), 1), 1),
                    repeat_interval_ms=max(parse_int(section.get(f"repeatinterval_{index}", sd("repeatinterval")), 30), 0),
                    trigger=parse_hotkey_expression(section.get(f"triggerbutton_{index}", sd("triggerbutton"))),
                )
            )

        profiles.append(
            ProfileConfig(
                name=section_name,
                skills=skills,
                profile_hotkey=method_to_hotkey(
                    parse_int(section.get("profilehkmethod", pd("profilehkmethod")), 1),
                    section.get("profilehkkey", pd("profilehkkey")),
                    COMMON_METHOD_MOUSE,
                ),
                autostart_macro=parse_boolean(section.get("autostartmarco", pd("autostartmarco")), False),
                start_mode=parse_int(section.get("lazymode", pd("lazymode")), 1),
                moving_method=parse_int(section.get("movingmethod", pd("movingmethod")), 1),
                moving_interval_ms=max(parse_int(section.get("movinginterval", pd("movinginterval")), 100), 20),
                potion_method=parse_int(section.get("potionmethod", pd("potionmethod")), 1),
                potion_interval_ms=max(parse_int(section.get("potioninterval", pd("potioninterval")), 500), 200),
                use_skill_queue=parse_boolean(section.get("useskillqueue", pd("useskillqueue")), False),
                use_skill_queue_interval_ms=max(parse_int(section.get("useskillqueueinterval", pd("useskillqueueinterval")), 200), 50),
                quick_pause=QuickPauseConfig(
                    enabled=parse_boolean(section.get("enablequickpause", pd("enablequickpause")), False),
                    mode=parse_int(section.get("quickpausemethod1", pd("quickpausemethod1")), 1),
                    trigger=method_to_hotkey(
                        parse_int(section.get("quickpausemethod2", pd("quickpausemethod2")), 1),
                        "",
                        QUICK_PAUSE_MOUSE,
                    ),
                    action=parse_int(section.get("quickpausemethod3", pd("quickpausemethod3")), 1),
                    delay_ms=max(parse_int(section.get("quickpausedelay", pd("quickpausedelay")), 1500), 50),
                ),
            )
        )

    return general, profiles


def default_skill_hotkey(index: int) -> str:
    return skill_hotkey_default(index)


def default_profile_dict() -> dict[str, str]:
    """Return the default key/value pairs for a new profile section."""
    return _schema_default_profile_dict()


def default_config_dir() -> Path:
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", "").strip()
        if app_data:
            return Path(app_data) / CONFIG_DIR_NAME
        return Path.home() / "AppData" / "Roaming" / CONFIG_DIR_NAME
    base_dir = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if base_dir:
        return Path(base_dir).expanduser() / CONFIG_DIR_NAME
    return Path.home() / ".config" / CONFIG_DIR_NAME


def default_config_path() -> Path:
    return default_config_dir() / CONFIG_FILE_NAME


def create_default_config(config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    parser["General"] = build_general_section(DEFAULT_VERSION)
    for name in DEFAULT_PROFILE_NAMES:
        parser[name] = default_profile_dict()

    write_config_parser_atomic(config_path, parser, "; Linux native config for D3keyHelper\r\n")


def write_config_parser_atomic(config_path: Path, parser: configparser.ConfigParser, header: str) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-16",
            dir=config_path.parent,
            prefix=f".{config_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(header)
            parser.write(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, config_path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
