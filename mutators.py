"""Модификаторы ежедневного забега и клятвы обычного забега."""

import random

MUTATOR_DEFS = {
    "iron_frontier": {
        "name": "Железный Рубеж",
        "desc": "Враги +14% HP.",
        "enemy_hp": 0.14,
    },
    "bounty_haze": {
        "name": "Щедрый Туман",
        "desc": "+30% золота, враги +8% HP.",
        "gold_mult": 1.30,
        "enemy_hp": 0.08,
    },
    "hunter_moon": {
        "name": "Охотничья Луна",
        "desc": "Шанс охотника +10%.",
        "hunter_bonus": 0.10,
    },
    "pressure_surge": {
        "name": "Всплеск Давления",
        "desc": "Давление Рубежа с 3-го хода.",
        "pressure_turn": 3,
    },
    "elite_swarm": {
        "name": "Рой Элит",
        "desc": "Элиты всегда с соратником.",
    },
    "thin_blood": {
        "name": "Тонкая Кровь",
        "desc": "−8 max HP, +25% золота.",
        "gold_mult": 1.25,
        "player_hp": -8,
    },
    "bleak_horizon": {
        "name": "Мрачный Горизонт",
        "desc": "+15% золота, чаще двойные бои.",
        "gold_mult": 1.15,
        "double_spawn": 0.10,
    },
    "void_whispers": {
        "name": "Шёпот Пустоты",
        "desc": "Враги +10% HP, +12% золота.",
        "gold_mult": 1.12,
        "enemy_hp": 0.10,
    },
}

OATH_DEFS = {
    "oath_greed": {
        "name": "Клятва Жадности",
        "desc": "+25% золота, враги +12% HP.",
        "gold_mult": 1.25,
        "enemy_hp": 0.12,
    },
    "oath_blood": {
        "name": "Клятва Крови",
        "desc": "−8 max HP, +1 энергия в боях.",
        "player_hp": -8,
        "bonus_energy": 1,
    },
    "oath_void": {
        "name": "Клятва Пустоты",
        "desc": "Давление с 2-го хода, +15% золота.",
        "pressure_turn": 2,
        "gold_mult": 1.15,
    },
    "oath_steel": {
        "name": "Клятва Стали",
        "desc": "+10 max HP, враги +10% HP.",
        "player_hp": 10,
        "enemy_hp": 0.10,
    },
    "oath_hunter": {
        "name": "Клятва Охоты",
        "desc": "Шанс охотника +12%, +18% золота.",
        "hunter_bonus": 0.12,
        "gold_mult": 1.18,
    },
}


def modifier_def(mod_id):
    return MUTATOR_DEFS.get(mod_id) or OATH_DEFS.get(mod_id)


def run_modifiers(run):
    if not run:
        return []
    ids = list(run.get("mutators", []))
    oath = run.get("oath")
    if oath and oath != "none":
        ids.append(oath)
    return ids


def roll_daily_mutators(seed, count=1):
    rng = random.Random(seed)
    pool = list(MUTATOR_DEFS.keys())
    rng.shuffle(pool)
    return pool[: min(count, len(pool))]


def mutator_labels(mutator_ids):
    return [modifier_def(mid)["name"] for mid in mutator_ids if modifier_def(mid)]


def oath_label(oath_id):
    if not oath_id or oath_id == "none":
        return "Без клятвы"
    return OATH_DEFS.get(oath_id, {}).get("name", oath_id)


def oath_desc(oath_id):
    if not oath_id or oath_id == "none":
        return "Обычный забег без дополнительных модификаторов."
    return OATH_DEFS.get(oath_id, {}).get("desc", "")


def cycle_oath(meta):
    ids = ["none"] + list(OATH_DEFS.keys())
    cur = meta.get("oath", "none")
    nxt = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else ids[0]
    meta["oath"] = nxt
    return nxt


def apply_start_modifiers(run):
    ids = run_modifiers(run)
    delta = player_hp_delta(ids)
    if delta:
        run["max_hp"] = max(20, run["max_hp"] + delta)
        run["hp"] = max(1, min(run["max_hp"], run["hp"] + delta))
    bonus = sum(modifier_def(m).get("bonus_energy", 0) for m in ids if modifier_def(m))
    if bonus:
        run["bonus_energy"] = run.get("bonus_energy", 0) + bonus


def enemy_hp_bonus(modifier_ids):
    bonus = 0.0
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info:
            bonus += info.get("enemy_hp", 0.0)
    return bonus


def gold_mult(modifier_ids):
    mult = 1.0
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info:
            mult *= info.get("gold_mult", 1.0)
    return mult


def hunter_bonus(modifier_ids):
    bonus = 0.0
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info:
            bonus += info.get("hunter_bonus", 0.0)
    return bonus


def pressure_turn(modifier_ids, default=5, act=0):
    turn = default
    if act >= 3:
        turn = min(turn, max(3, default - 1))
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info and info.get("pressure_turn") is not None:
            turn = min(turn, info["pressure_turn"])
    return turn


def player_hp_delta(modifier_ids):
    delta = 0
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info:
            delta += info.get("player_hp", 0)
    return delta


def double_spawn_bonus(modifier_ids):
    bonus = 0.0
    for mid in modifier_ids or []:
        info = modifier_def(mid)
        if info:
            bonus += info.get("double_spawn", 0.0)
    return bonus
