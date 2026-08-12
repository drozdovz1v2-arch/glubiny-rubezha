"""Вознесение — дополнительная сложность после первой победы."""

MAX_ASCENSION = 5

ASCENSION_DEFS = {
    0: {"name": "Без вознесения", "desc": "Обычный забег без доп. модификаторов."},
    1: {"name": "Вознесение I", "desc": "Враги +8% HP. Меньше золота с боёв."},
    2: {"name": "Вознесение II", "desc": "Враги +16% HP, +5% урона. Давление с 4-го хода."},
    3: {"name": "Вознесение III", "desc": "Враги +24% HP. Элиты чаще. −1 привал на карте."},
    4: {"name": "Вознесение IV", "desc": "Враги +32% HP, +10% урона. Охотники чаще."},
    5: {"name": "Вознесение V", "desc": "Враги +40% HP, +15% урона. Боссы яростнее. Максимальный вызов."},
}


def ascension_level(meta):
    if meta.get("wins", 0) < 1:
        return 0
    return max(0, min(MAX_ASCENSION, int(meta.get("ascension", 0))))


def ascension_label(level=None, meta=None):
    if level is None:
        level = ascension_level(meta or {})
    return ASCENSION_DEFS.get(level, ASCENSION_DEFS[0])["name"]


def ascension_desc(level=None, meta=None):
    if level is None:
        level = ascension_level(meta or {})
    return ASCENSION_DEFS.get(level, ASCENSION_DEFS[0])["desc"]


def cycle_ascension(meta):
    if meta.get("wins", 0) < 1:
        return 0
    cur = ascension_level(meta)
    nxt = (cur + 1) % (MAX_ASCENSION + 1)
    meta["ascension"] = nxt
    return nxt


def ascension_enemy_hp_mult(level):
    return 1.0 + level * 0.08


def ascension_enemy_dmg_mult(level):
    if level >= 2:
        return 1.0 + (level - 1) * 0.05
    return 1.0


def ascension_pressure_offset(level):
    if level >= 2:
        return 1
    return 0


def ascension_hunter_bonus(level):
    return level * 0.02 if level >= 4 else 0.0


def ascension_gold_mult(level):
    if level >= 1:
        return max(0.75, 1.0 - level * 0.03)
    return 1.0


def ascension_elite_bonus(level):
    return level * 0.015 if level >= 3 else 0.0
