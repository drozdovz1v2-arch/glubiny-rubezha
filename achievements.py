"""Достижения — мета-прогресс между забегами."""

from config import save_meta

_achievement_listener = None


def set_achievement_listener(callback):
    global _achievement_listener
    _achievement_listener = callback


ACHIEVEMENT_DEFS = {
    "first_win": {
        "name": "Страж Рубежа",
        "desc": "Одержи первую победу над тьмой.",
        "color": (255, 204, 96),
    },
    "harsh_win": {
        "name": "Суровость",
        "desc": "Победи на сложности «Суровый Рубеж».",
        "color": (255, 88, 88),
    },
    "reach_act3": {
        "name": "До Предела",
        "desc": "Дойди до 3-го акта в забеге.",
        "color": (112, 178, 210),
    },
    "reach_act4": {
        "name": "В Самое Сердце",
        "desc": "Дойди до финального акта — Руин Предела.",
        "color": (160, 100, 220),
    },
    "relics_5": {
        "name": "Собиратель",
        "desc": "Открой 5 артефактов в кодексе.",
        "color": (180, 140, 255),
    },
    "relics_all": {
        "name": "Архивариус",
        "desc": "Открой все артефакты.",
        "color": (72, 210, 200),
    },
    "combats_15": {
        "name": "Мастер Боя",
        "desc": "Выиграй 15+ боёв за один забег.",
        "color": (255, 120, 100),
    },
    "rest_upgrade": {
        "name": "Кузнец",
        "desc": "Улучши карту на привале.",
        "color": (255, 176, 72),
    },
    "boss_relic": {
        "name": "Добыча Босса",
        "desc": "Получи босс-артефакт.",
        "color": (255, 204, 96),
    },
    "cards_10": {
        "name": "Картограф",
        "desc": "Открой 10 карт в коллекции.",
        "color": (120, 180, 255),
    },
    "cards_all": {
        "name": "Полная Колода",
        "desc": "Открой все карты в коллекции.",
        "color": (98, 214, 130),
    },
    "shop_remove": {
        "name": "Чистка Колода",
        "desc": "Удали карту в лавке за золото.",
        "color": (255, 160, 96),
    },
    "daily_win": {
        "name": "Ежедневный Страж",
        "desc": "Победи в ежедневном забеге.",
        "color": (255, 220, 120),
    },
    "nightmare_win": {
        "name": "Кошмар Рубежа",
        "desc": "Победи на сложности «Кошмар».",
        "color": (180, 60, 120),
    },
    "potion_healer": {
        "name": "Алхимик",
        "desc": "Используй 3 зелья за один забег.",
        "color": (120, 200, 160),
    },
    "potions_all": {
        "name": "Мастер Настоев",
        "desc": "Открой все зелья в кодексе.",
        "color": (140, 220, 180),
    },
    "oath_win": {
        "name": "Клятвенный Страж",
        "desc": "Победи, приняв клятву перед забегом.",
        "color": (200, 120, 255),
    },
    "full_belt": {
        "name": "Пояс Алхимика",
        "desc": "Победи с полным поясом зелий (3/3).",
        "color": (100, 200, 160),
    },
    "curse_survivor": {
        "name": "Проклятый Страж",
        "desc": "Победи с 3+ проклятиями в колоде.",
        "color": (160, 100, 180),
    },
    "rest_brew": {
        "name": "Настойщик",
        "desc": "Свари зелье на привале.",
        "color": (120, 200, 160),
    },
    "cleanse_self": {
        "name": "Очищение",
        "desc": "Сними с себя яд или слабость.",
        "color": (140, 210, 255),
    },
}


def unlock_achievement(meta, ach_id):
    if ach_id not in ACHIEVEMENT_DEFS:
        return False
    unlocked = meta.setdefault("achievements", [])
    if ach_id in unlocked:
        return False
    unlocked.append(ach_id)
    save_meta(meta)
    if _achievement_listener:
        _achievement_listener(ach_id)
    return True


def check_card_achievements(meta):
    from cards import all_card_ids

    found = len(meta.get("cards_found", []))
    if found >= 10:
        unlock_achievement(meta, "cards_10")
    if found >= len(all_card_ids()):
        unlock_achievement(meta, "cards_all")


def check_potion_achievements(meta):
    from potions import POTION_DEFS

    found = len(meta.get("potions_found", []))
    if found >= len(POTION_DEFS):
        unlock_achievement(meta, "potions_all")


def check_meta_achievements(meta):
    found = len(meta.get("relics_found", []))
    from relics import RELIC_DEFS

    if found >= 5:
        unlock_achievement(meta, "relics_5")
    if found >= len(RELIC_DEFS):
        unlock_achievement(meta, "relics_all")
    check_card_achievements(meta)
    check_potion_achievements(meta)
    if meta.get("best_act", 0) >= 3:
        unlock_achievement(meta, "reach_act3")
    if meta.get("best_act", 0) >= 4:
        unlock_achievement(meta, "reach_act4")
    if meta.get("wins", 0) >= 1:
        unlock_achievement(meta, "first_win")


def on_victory(meta, difficulty_id, run=None):
    unlock_achievement(meta, "first_win")
    if difficulty_id == "harsh":
        unlock_achievement(meta, "harsh_win")
    if difficulty_id == "nightmare":
        unlock_achievement(meta, "nightmare_win")
    if run and run.get("oath") and run.get("oath") != "none":
        unlock_achievement(meta, "oath_win")
    if run and len(run.get("potions", [])) >= 3:
        unlock_achievement(meta, "full_belt")
    if run:
        curses = sum(1 for c in run.get("deck", []) if c.get("type") == "curse")
        if curses >= 3:
            unlock_achievement(meta, "curse_survivor")
    if meta.get("best_combats", 0) >= 15:
        unlock_achievement(meta, "combats_15")
    check_meta_achievements(meta)


def on_rest_upgrade(meta):
    unlock_achievement(meta, "rest_upgrade")


def on_rest_brew(meta):
    unlock_achievement(meta, "rest_brew")


def on_cleanse(meta):
    unlock_achievement(meta, "cleanse_self")


def on_boss_relic(meta):
    unlock_achievement(meta, "boss_relic")


def on_shop_remove(meta):
    unlock_achievement(meta, "shop_remove")


def on_daily_win(meta):
    unlock_achievement(meta, "daily_win")
    today = __import__("datetime").date.today().isoformat()
    meta["daily_win_date"] = today
    save_meta(meta)


def on_potion_used(meta, run):
    if run.get("potions_used", 0) >= 3:
        unlock_achievement(meta, "potion_healer")


def achievement_progress(meta, ach_id):
    from cards import all_card_ids
    from relics import RELIC_DEFS

    if ach_id in meta.get("achievements", []):
        return None
    if ach_id == "first_win":
        wins = meta.get("wins", 0)
        return f"Побед: {wins}/1"
    if ach_id == "harsh_win":
        return "Нужна победа на «Суровый Рубеж»"
    if ach_id == "nightmare_win":
        return "Нужна победа на «Кошмар»"
    if ach_id == "reach_act3":
        return f"Рекорд: акт {meta.get('best_act', 0)}/3"
    if ach_id == "reach_act4":
        return f"Рекорд: акт {meta.get('best_act', 0)}/4"
    if ach_id == "relics_5":
        return f"Артефактов: {len(meta.get('relics_found', []))}/5"
    if ach_id == "relics_all":
        return f"Артефактов: {len(meta.get('relics_found', []))}/{len(RELIC_DEFS)}"
    if ach_id == "combats_15":
        return f"Рекорд: {meta.get('best_combats', 0)}/15 боёв"
    if ach_id == "cards_10":
        return f"Карт: {len(meta.get('cards_found', []))}/10"
    if ach_id == "cards_all":
        return f"Карт: {len(meta.get('cards_found', []))}/{len(all_card_ids())}"
    if ach_id == "potions_all":
        from potions import POTION_DEFS
        return f"Зелий: {len(meta.get('potions_found', []))}/{len(POTION_DEFS)}"
    if ach_id == "oath_win":
        return "Нужна победа с активной клятвой"
    if ach_id == "full_belt":
        return "Нужна победа с 3 зельями на поясе"
    if ach_id == "curse_survivor":
        return "Нужна победа с 3+ проклятиями в колоде"
    return None
