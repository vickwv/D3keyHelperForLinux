"""Shared integer enumerations for D3keyHelper configuration values.

These values correspond to the integer codes stored in the INI file.
"""
from __future__ import annotations
from enum import IntEnum


class SkillAction(IntEnum):
    DISABLED = 1
    HOLD = 2
    SPAM = 3
    KEEP_BUFF = 4
    KEY_TRIGGER = 5


class StartMode(IntEnum):
    TOGGLE = 1
    HOLD_WHILE = 2
    ONCE = 3


class StartMethod(IntEnum):
    RIGHT_CLICK = 1
    MIDDLE_CLICK = 2
    SCROLL_UP = 3
    SCROLL_DOWN = 4
    SIDE1 = 5
    SIDE2 = 6
    KEYBOARD = 7


class MovingMethod(IntEnum):
    NONE = 1
    FORCE_STAND = 2
    FORCE_MOVE_HOLD = 3
    FORCE_MOVE_SPAM = 4


class PotionMethod(IntEnum):
    NONE = 1
    TIMED = 2
    KEEP_CD = 3


class SalvageMethod(IntEnum):
    QUICK = 1
    ONE_CLICK = 2
    SMART = 3
    SMART_KEEP_ANCIENT = 4
    SMART_KEEP_PRIMAL = 5


class ReforgeMethod(IntEnum):
    ONCE = 1
    TO_ANCIENT = 2
    TO_PRIMAL = 3


class QuickPauseMode(IntEnum):
    DOUBLE_CLICK = 1
    SINGLE_CLICK = 2
    HOLD = 3


class QuickPauseTrigger(IntEnum):
    LEFT_CLICK = 1
    RIGHT_CLICK = 2
    MIDDLE_CLICK = 3
    SIDE1 = 4
    SIDE2 = 5


class QuickPauseAction(IntEnum):
    PAUSE_MACRO = 1
    PAUSE_AND_SPAM_LEFT = 2


class HelperSpeedPreset(IntEnum):
    VERY_FAST = 1
    FAST = 2
    MEDIUM = 3
    SLOW = 4
    CUSTOM = 5


class SendMode(IntEnum):
    """Maps to 'Event'/'Input' string values, but also used as index 1/2."""
    EVENT = 1
    INPUT = 2
