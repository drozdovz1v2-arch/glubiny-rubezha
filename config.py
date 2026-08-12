import json
import os
import random
from datetime import date

GAME_TITLE = "Глубины Рубежа"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BASE_WIDTH = 1280
BASE_HEIGHT = 720
FPS = 60


def sx(value):
    return int(value * SCREEN_WIDTH / BASE_WIDTH)


def sy(value):
    return int(value * SCREEN_HEIGHT / BASE_HEIGHT)


def daily_seed():
    return int(date.today().strftime("%Y%m%d"))

DISPLAY_PRESETS = [
    {"id": "1280x720", "label": "1280×720", "width": 1280, "height": 720},
    {"id": "1600x900", "label": "1600×900", "width": 1600, "height": 900},
    {"id": "1920x1080", "label": "1920×1080", "width": 1920, "height": 1080},
]


def get_display_preset(meta):
    preset_id = meta.get("display_preset", "1280x720")
    for preset in DISPLAY_PRESETS:
        if preset["id"] == preset_id:
            return preset
    return DISPLAY_PRESETS[0]

SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.json")

COLORS = {
    "bg_top": (8, 10, 18),
    "bg_bottom": (16, 22, 36),
    "panel": (16, 22, 34),
    "panel_border": (52, 68, 98),
    "accent": (72, 210, 200),
    "accent_warm": (255, 176, 72),
    "danger": (255, 88, 88),
    "success": (98, 214, 130),
    "text": (236, 240, 248),
    "text_dim": (128, 140, 162),
    "gold": (255, 204, 96),
    "card_attack": (128, 48, 52),
    "card_skill": (36, 82, 118),
    "card_power": (88, 52, 118),
    "card_curse": (72, 48, 68),
    "forest": (38, 132, 68),
    "desert": (188, 146, 52),
    "snow": (112, 178, 210),
    "ruins": (140, 90, 180),
    "void": (100, 60, 160),
}

ACTS = [
    {"name": "Лесной Рубеж", "biome": "forest", "color": COLORS["forest"]},
    {"name": "Пустынные Глубины", "biome": "desert", "color": COLORS["desert"]},
    {"name": "Ледяной Предел", "biome": "snow", "color": COLORS["snow"]},
    {"name": "Руины Предела", "biome": "ruins", "color": COLORS["ruins"]},
    {"name": "Сердце Пустоты", "biome": "void", "color": COLORS["void"]},
]

NODE_TYPES = {
    "battle": "Бой",
    "elite": "Элита",
    "rest": "Привал",
    "shop": "Лавка",
    "event": "Событие",
    "boss": "Босс",
    "treasure": "Сокровище",
}

NODE_COLORS = {
    "battle": (255, 110, 95),
    "elite": (255, 185, 80),
    "rest": (255, 150, 70),
    "shop": (120, 200, 255),
    "event": (180, 140, 255),
    "boss": (255, 80, 100),
    "treasure": (255, 210, 80),
}

CARD_TYPE_COLORS = {
    "attack": COLORS["card_attack"],
    "skill": COLORS["card_skill"],
    "power": COLORS["card_power"],
    "curse": COLORS["card_curse"],
}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rand_int(a, b):
    return random.randint(a, b)


def pick(items):
    return random.choice(items)


def shuffle(items):
    copy = list(items)
    random.shuffle(copy)
    return copy


def load_meta():
    defaults = {
        "wins": 0,
        "runs": 0,
        "tutorial_done": False,
        "music_volume": 0.7,
        "sfx_volume": 0.85,
        "display_preset": "1280x720",
        "fullscreen": False,
        "difficulty": "harsh",
        "achievements": [],
        "cards_found": [],
        "relics_found": [],
        "potions_found": [],
        "oath": "none",
        "guardian": "steel",
        "ascension": 0,
        "best_act": 0,
        "best_combats": 0,
    }
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
                return defaults
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_meta(meta):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def has_run_save(meta):
    return bool(meta.get("run_save"))


def save_run_state(meta, payload):
    meta["run_save"] = payload
    save_meta(meta)


def clear_run_save(meta):
    if "run_save" in meta:
        del meta["run_save"]
        save_meta(meta)
