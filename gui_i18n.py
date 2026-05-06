from __future__ import annotations
import configparser
import locale
import os
from pathlib import Path


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


UI_LANGUAGE_ENV = "D3HELPER_LANG"
LANGUAGE_TOOLBAR_ITEMS = [("zh", "简"), ("en", "EN"), ("zh_TW", "繁")]


def normalize_ui_language(value: str | None) -> str | None:
    normalized = (value or "").strip().lower().replace(".", "_")
    if not normalized:
        return None
    if normalized.startswith("en"):
        return "en"
    if normalized in {"zh_tw", "zh-tw", "zh_hk", "zh-hk", "zh_hant", "zh-hant", "tw", "hk", "traditional"}:
        return "zh_TW"
    if normalized.startswith("zh"):
        return "zh"
    return None


def resolve_ui_language() -> str:
    env_language = normalize_ui_language(os.environ.get(UI_LANGUAGE_ENV))
    if env_language is not None:
        return env_language
    candidates = [
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
        locale.getlocale()[0],
    ]
    for candidate in candidates:
        detected = normalize_ui_language(candidate)
        if detected is not None:
            return detected
    return "zh"


def set_ui_language(language: str) -> str:
    global UI_LANGUAGE
    UI_LANGUAGE = normalize_ui_language(language) or "zh"
    return UI_LANGUAGE


def configured_ui_language(config_path: Path) -> str | None:
    if not config_path.exists():
        return None
    try:
        parser = load_parser(config_path)
    except Exception:
        return None
    for section_name in parser.sections():
        if section_name.lower() == "general":
            return normalize_ui_language(parser[section_name].get("language", ""))
    return None


UI_LANGUAGE = resolve_ui_language()

EN_TEXT = {
    "鼠标右键": "Right mouse",
    "鼠标中键": "Middle mouse",
    "滚轮向上": "Wheel up",
    "滚轮向下": "Wheel down",
    "侧键1": "Side button 1",
    "侧键2": "Side button 2",
    "键盘按键": "Keyboard key",
    "鼠标左键": "Left mouse",
    "无": "None",
    "禁用": "Disabled",
    "按住不放": "Hold",
    "连点": "Repeat tap",
    "保持Buff": "Keep buff",
    "按键触发": "Key trigger",
    "懒人模式": "Toggle mode",
    "仅按住时": "Hold to run",
    "仅按一次": "One-shot",
    "强制站立": "Force stand still",
    "强制走位（按住）": "Force move (hold)",
    "强制走位（连点）": "Force move (tap)",
    "定时连点": "Timed tap",
    "保持药水CD": "Keep potion cooldown",
    "快速分解": "Fast salvage",
    "一键分解": "One-click salvage",
    "智能分解": "Smart salvage",
    "智能分解（留神圣/无形/太古）": "Smart salvage (keep sacred/ethereal/primal)",
    "智能分解（只留太古）": "Smart salvage (keep primal only)",
    "重铸一次": "Reforge once",
    "重铸到远古/太古": "Reforge until ancient/primal",
    "重铸到太古": "Reforge until primal",
    "双击": "Double click",
    "单击": "Single click",
    "按住": "Hold",
    "暂停宏": "Pause macro",
    "暂停宏并连点左键": "Pause and tap left mouse",
    "非常快": "Very fast",
    "快速": "Fast",
    "中等": "Medium",
    "慢速": "Slow",
    "自定义": "Custom",
    "配置": "Profile",
    "配置名": "Profile name",
    "宏启动方式": "Macro start mode",
    "切换类型": "Switch method",
    "切换按键": "Switch key",
    "切换后自动启动宏": "Auto-start macro after switch",
    "走位辅助": "Movement helper",
    "走位间隔": "Movement interval",
    "药水辅助": "Potion helper",
    "药水间隔": "Potion interval",
    "单线程按键队列": "Single-thread skill queue",
    "间隔": "Interval",
    "启用快速暂停": "Enable quick pause",
    "暂停触发": "Pause trigger",
    "暂停按键": "Pause button",
    "暂停动作": "Pause action",
    "暂停时长": "Pause duration",
    "当前激活配置": "Active profile",
    "界面语言": "Interface language",
    "战斗宏启动方式": "Macro start method",
    "战斗宏启动热键": "Macro start hotkey",
    "助手启动方式": "Helper start method",
    "助手启动热键": "Helper hotkey",
    "发送模式": "Send mode",
    "游戏分辨率": "Game resolution",
    "游戏 Gamma": "Game Gamma",
    "Buff 续按阈值": "Buff refresh threshold",
    "宏启动瞬间执行一次": "Run once when macro starts",
    "只作用于 Diablo III 前台窗口": "Only affect foreground Diablo III window",
    "智能暂停": "Smart pause",
    "切换配置提示音": "Profile switch sound",
    "自定义强制站立": "Custom stand-still key",
    "自定义强制移动": "Custom force-move key",
    "自定义药水按键": "Custom potion key",
    "按键": "Key",
    "赌博助手": "Gamble helper",
    "点击次数": "Click count",
    "拾取助手": "Loot helper",
    "分解助手": "Salvage helper",
    "分解策略": "Salvage strategy",
    "重铸助手": "Reforge helper",
    "重铸策略": "Reforge strategy",
    "升级助手": "Upgrade helper",
    "转化助手": "Convert helper",
    "丢装助手": "Drop/store helper",
    "动画速度预设": "Animation speed preset",
    "辅助鼠标速度": "Helper mouse speed",
    "辅助动画延迟": "Helper animation delay",
    "安全格": "Safe slots",
    "最大重铸次数": "Max reforges",
    "安全格状态：已设置": "Safe slots: set",
    "安全格状态：未设置（沿用原版默认值 61,62,63）": "Safe slots: unset (using legacy default 61,62,63)",
    "安全格状态：未设置": "Safe slots: unset",
    "安全格状态：格式错误": "Safe slots: invalid format",
    "选择安全格": "Select Safe Slots",
    "点击格子以切换是否为安全格（蓝色 = 已选中）。\n左上角为第1格，右上角为第10格，依次排列。": "Click a slot to toggle it as safe (blue = selected).\nTop-left is slot 1, top-right is slot 10.",
    "选择…": "Pick…",
    "选择": "Pick",
    "确认": "OK",
    "取消": "Cancel",
    "已保存配置。": "Config saved.",
    "已启动运行器。": "Runner started.",
    "已停止运行器。": "Runner stopped.",
    "已自动保存配置。": "Config auto-saved.",
    "检测到配置变更，已自动重启运行器。": "Config changed; runner restarted.",
    "基础": "Basics",
    "走位与药水": "Movement & Potion",
    "按键队列": "Skill Queue",
    "快速暂停": "Quick Pause",
    "技能表": "Skill table",
}

ZH_TW_MAP = str.maketrans({
    "载": "載", "设": "設", "置": "置", "档": "檔", "项": "項", "键": "鍵", "击": "擊",
    "启": "啟", "动": "動", "运": "運", "行": "行", "器": "器", "状": "狀", "态": "態",
    "数": "數", "错": "錯", "误": "誤", "认": "認", "为": "為", "开": "開",
    "关": "關", "闭": "閉", "选": "選", "择": "擇", "发": "發", "送": "送", "标": "標",
    "签": "籤", "页": "頁", "图": "圖", "显": "顯", "示": "示", "栏": "欄", "导": "導",
    "览": "覽", "码": "碼", "热": "熱", "缩": "縮", "复": "複", "制": "製", "药": "藥",
    "剂": "劑", "补": "補", "优": "優", "迟": "遲", "队": "隊",
    "列": "列", "触": "觸", "单": "單", "随": "隨", "机": "機", "强": "強",
    "滚": "滾", "轮": "輪", "侧": "側", "暂": "暫", "停": "停", "战": "戰", "斗": "鬥",
    "宏": "宏", "懒": "懶", "仅": "僅", "时": "時", "连": "連", "点": "點", "换": "換",
    "间": "間", "帮": "幫", "助": "助", "赌": "賭", "博": "博", "拾": "拾", "取": "取",
    "分": "分", "解": "解", "铸": "鑄", "远": "遠", "古": "古", "太": "太", "圣": "聖",
    "形": "形", "升": "升", "级": "級", "转": "轉", "化": "化", "丢": "丟", "装": "裝",
    "储": "儲", "仓": "倉", "入": "入", "输": "輸", "出": "出", "读": "讀",
    "写": "寫", "应": "應", "该": "該", "并": "並", "线": "線", "实": "實", "际": "際",
    "阈": "閾", "值": "值", "请": "請", "填": "填", "处": "處", "过": "過", "滤": "濾",
})


def zh_to_tw(text: str) -> str:
    return text.translate(ZH_TW_MAP)


def localize_text(text: str) -> str:
    if UI_LANGUAGE == "en":
        if text.startswith("配置") and text[2:].isdigit():
            return f"Profile {text[2:]}"
        return EN_TEXT.get(text, text)
    if UI_LANGUAGE == "zh_TW":
        return zh_to_tw(text)
    return text


def tr(chinese: str, english: str, traditional: str | None = None) -> str:
    if UI_LANGUAGE == "en":
        return english
    if UI_LANGUAGE == "zh_TW":
        return traditional if traditional is not None else zh_to_tw(chinese)
    return chinese


