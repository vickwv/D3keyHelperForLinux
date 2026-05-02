"""Single source of truth for INI config field defaults.

Both the runtime (load_config, create_default_config) and the GUI
use these values so that adding a new field only requires one edit here.
"""
from __future__ import annotations

# ── General section defaults ─────────────────────────────────────────────────
GENERAL_DEFAULTS: dict[str, str] = {
    "version": "1",               # filled in at write time
    "activatedprofile": "1",
    "startmethod": "7",
    "starthotkey": "F2",
    "sendmode": "Event",
    "runonstart": "1",
    "d3only": "1",
    "enablesmartpause": "1",
    "enablesoundplay": "1",
    "gamegamma": "1.000000",
    "buffpercent": "0.050000",
    "gameresolution": "Auto",
    "oldsandhelpermethod": "7",
    "oldsandhelperhk": "F5",
    "enablegamblehelper": "1",
    "gamblehelpertimes": "15",
    "enableloothelper": "0",
    "loothelpertimes": "30",
    "enablesalvagehelper": "0",
    "salvagehelpermethod": "1",
    "enablereforgehelper": "0",
    "reforgehelpermethod": "1",
    "enableupgradehelper": "0",
    "enableconverthelper": "0",
    "enableabandonhelper": "0",
    "helperspeed": "3",
    "helpermousespeed": "2",
    "helperanimationdelay": "150",
    "safezone": "61,62,63",
    "maxreforge": "10",
    "compactmode": "0",
    "custommoving": "0",
    "custommovinghk": "e",
    "customstanding": "0",
    "customstandinghk": "LShift",
    "custompotion": "0",
    "custompotionhk": "q",
}

# ── Profile section defaults ──────────────────────────────────────────────────
_SKILL_HOTKEY_DEFAULTS: dict[int, str] = {1: "1", 2: "2", 3: "3", 4: "4", 5: "LButton", 6: "RButton"}

PROFILE_DEFAULTS: dict[str, str] = {
    "profilehkmethod": "1",
    "profilehkkey": "",
    "movingmethod": "1",
    "movinginterval": "100",
    "potionmethod": "1",
    "potioninterval": "500",
    "lazymode": "1",
    "enablequickpause": "0",
    "quickpausemethod1": "1",
    "quickpausemethod2": "1",
    "quickpausemethod3": "1",
    "quickpausedelay": "1500",
    "useskillqueue": "0",
    "useskillqueueinterval": "200",
    "autostartmarco": "0",
}


def default_profile_dict() -> dict[str, str]:
    """Return the default key/value pairs for a new profile section."""
    values = dict(PROFILE_DEFAULTS)
    for index in range(1, 7):
        values[f"skill_{index}"] = _SKILL_HOTKEY_DEFAULTS[index]
        values[f"action_{index}"] = "1"
        values[f"interval_{index}"] = "300"
        values[f"delay_{index}"] = "10"
        values[f"random_{index}"] = "1"
        values[f"priority_{index}"] = "1"
        values[f"repeat_{index}"] = "1"
        values[f"repeatinterval_{index}"] = "30"
        values[f"triggerbutton_{index}"] = "LButton"
    return values


# ── Per-skill field defaults (same for all slots except hotkey) ───────────────
SKILL_FIELD_DEFAULTS: dict[str, str] = {
    "action": "1",
    "interval": "300",
    "delay": "10",
    "random": "1",
    "priority": "1",
    "repeat": "1",
    "repeatinterval": "30",
    "triggerbutton": "LButton",
}


# ── Convenience accessor helpers ──────────────────────────────────────────────

def gd(key: str) -> str:
    """Return the default INI string value for a General section field."""
    return GENERAL_DEFAULTS[key]


def pd(key: str) -> str:
    """Return the default INI string value for a Profile section field."""
    return PROFILE_DEFAULTS[key]


def sd(key: str) -> str:
    """Return the default INI string value for a per-skill field (not the hotkey)."""
    return SKILL_FIELD_DEFAULTS[key]


def skill_hotkey_default(index: int) -> str:
    """Return the default hotkey string for skill slot *index* (1-based)."""
    return _SKILL_HOTKEY_DEFAULTS[index]


def build_general_section(version: str) -> dict[str, str]:
    """Return a complete General section dict with the given version string."""
    values = dict(GENERAL_DEFAULTS)
    values["version"] = version
    return values
