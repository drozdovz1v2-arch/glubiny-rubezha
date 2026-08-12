"""Благословения Рубежа — пассивные бонусы забега после победы над боссом."""

from config import pick

BLESSING_DEFS = {
    "frontier_bounty": {
        "name": "Дар Рубежа",
        "desc": "+18% золота с боёв.",
        "color": (255, 204, 96),
    },
    "iron_resolve": {
        "name": "Железная Стойкость",
        "desc": "В начале каждого боя +4 HP.",
        "color": (98, 214, 130),
    },
    "swift_hand": {
        "name": "Быстрая Рука",
        "desc": "В первый ход боя возьми +1 карту.",
        "color": (120, 200, 255),
    },
    "ember_soul": {
        "name": "Пламенная Душа",
        "desc": "Ожог накладывается на +1 сильнее.",
        "color": (255, 140, 60),
    },
    "void_ward": {
        "name": "Покров Пустоты",
        "desc": "Первый урон за бой −4.",
        "color": (160, 120, 220),
    },
    "hunter_instinct": {
        "name": "Инстинкт Охотника",
        "desc": "+12 золота после победы над охотником.",
        "color": (220, 80, 90),
    },
    "restful_echo": {
        "name": "Эхо Привала",
        "desc": "На привале лечение +4 HP.",
        "color": (255, 150, 70),
    },
    "treasure_sense": {
        "name": "Чутьё Сокровищ",
        "desc": "Узлы «Сокровище» дают +20 золота.",
        "color": (255, 210, 80),
    },
}


def roll_blessing_choices(owned=None, count=3):
    owned = set(owned or [])
    pool = [bid for bid in BLESSING_DEFS if bid not in owned]
    if not pool:
        return []
    import random
    random.shuffle(pool)
    return pool[: min(count, len(pool))]


def blessing_label(bid):
    return BLESSING_DEFS.get(bid, {}).get("name", bid)


def blessing_desc(bid):
    return BLESSING_DEFS.get(bid, {}).get("desc", "")


def blessing_gold_mult(run):
    mult = 1.0
    if "frontier_bounty" in run.get("blessings", []):
        mult *= 1.18
    return mult


def treasure_gold_mult(run):
    mult = 1.0
    if "treasure_sense" in run.get("blessings", []):
        mult += 0.35
    return mult


def hunter_gold_bonus(run):
    if "hunter_instinct" in run.get("blessings", []):
        return 12
    return 0


def rest_heal_bonus(run):
    if "restful_echo" in run.get("blessings", []):
        return 4
    return 0


def apply_blessing_combat_start(combat):
    blessings = combat.run.get("blessings", [])
    if "iron_resolve" in blessings:
        heal = min(4, combat.player["max_hp"] - combat.player["hp"])
        if heal > 0:
            combat.player["hp"] += heal
            combat.spawn_fx("heal", heal, "player")
            combat.log(f"Благословение: +{heal} HP")
    if "swift_hand" in blessings and combat.turn == 1:
        combat.draw_cards(1)
        combat.spawn_fx("draw", 1, "player")
        combat.log("Благословение: +1 карта")


def blessing_burn_bonus(run, amount):
    if "ember_soul" in run.get("blessings", []):
        return amount + 1
    if run.get("guardian") == "flame":
        return amount + 1
    return amount


def blessing_first_hit_reduction(combat, hp_lost):
    blessings = combat.run.get("blessings", [])
    if "void_ward" not in blessings or combat.blessing_ward_used:
        return hp_lost
    if hp_lost <= 0:
        return hp_lost
    combat.blessing_ward_used = True
    reduced = max(0, hp_lost - 4)
    if reduced < hp_lost:
        combat.log("Покров Пустоты: −4 урона")
    return reduced
