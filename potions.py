import random

from config import pick

POTION_MAX = 3

POTION_DEFS = {
    "healing_draught": {
        "name": "Целебный Настой",
        "desc": "Восстанови 20 HP.",
        "color": (98, 214, 130),
        "price": 50,
    },
    "iron_brew": {
        "name": "Железный Отвар",
        "desc": "Получи 12 блока.",
        "color": (111, 168, 255),
        "price": 45,
    },
    "focus_tonic": {
        "name": "Тоник Фокуса",
        "desc": "+1 энергия, возьми 1 карту.",
        "color": (255, 204, 96),
        "price": 55,
    },
    "purify_flask": {
        "name": "Сосуд Очищения",
        "desc": "Сними слабость и яд.",
        "color": (180, 140, 255),
        "price": 48,
    },
    "fire_bomb": {
        "name": "Огненная Смесь",
        "desc": "12 урона всем врагам.",
        "color": (255, 120, 80),
        "price": 60,
    },
    "smoke_vial": {
        "name": "Дымовая Смесь",
        "desc": "8 блока и возьми 1 карту.",
        "color": (160, 170, 190),
        "price": 52,
    },
    "venom_phial": {
        "name": "Ядовитый Флакон",
        "desc": "Накладывает 5 Яда на цель.",
        "color": (140, 210, 90),
        "price": 50,
    },
    "frost_aegis": {
        "name": "Ледяной Эгида",
        "desc": "10 блока. Враги получают 1 Слабости.",
        "color": (130, 190, 240),
        "price": 54,
    },
}


def can_add_potion(run):
    return len(run.get("potions", [])) < POTION_MAX


def add_potion(run, potion_id):
    if potion_id not in POTION_DEFS or not can_add_potion(run):
        return False
    run.setdefault("potions", []).append(potion_id)
    return True


def discover_potion(meta, potion_id, save=True):
    if potion_id not in POTION_DEFS:
        return False
    found = meta.setdefault("potions_found", [])
    if potion_id in found:
        return False
    found.append(potion_id)
    if save:
        from config import save_meta
        save_meta(meta)
        from achievements import check_potion_achievements
        check_potion_achievements(meta)
    return True


def sync_discovered_potions(meta, potion_ids):
    changed = False
    for pid in potion_ids:
        if discover_potion(meta, pid, save=False):
            changed = True
    if changed:
        from config import save_meta
        save_meta(meta)


def roll_rest_potion():
    return pick(list(POTION_DEFS.keys()))


def roll_shop_potions(count=2):
    from difficulty import shop_price

    pool = list(POTION_DEFS.keys())
    random.shuffle(pool)
    return [
        {"type": "potion", "potion_id": pid, "price": shop_price(POTION_DEFS[pid]["price"])}
        for pid in pool[:count]
    ]


def roll_elite_potion():
    return pick(list(POTION_DEFS.keys()))


def use_potion_in_combat(combat, index):
    if not combat.is_player_turn or combat.potion_used_this_turn:
        return False
    potions = combat.potions
    if index < 0 or index >= len(potions):
        return False
    pid = potions.pop(index)
    info = POTION_DEFS.get(pid, {})
    combat.potion_used_this_turn = True
    combat.log(f"Зелье: {info.get('name', pid)}")
    from relics import relic_on_potion_used
    relic_on_potion_used(combat.relics, combat)

    if pid == "healing_draught":
        heal = min(20, combat.player["max_hp"] - combat.player["hp"])
        combat.player["hp"] += heal
        combat.spawn_fx("heal", heal, "player")
    elif pid == "iron_brew":
        combat.player["block"] += 12
        combat.spawn_fx("block", 12, "player")
    elif pid == "focus_tonic":
        combat.player["energy"] += 1
        combat.draw_cards(1)
        combat.spawn_fx("draw", 1, "player")
    elif pid == "purify_flask":
        for key in ("weak", "poison"):
            combat.player["statuses"].pop(key, None)
        combat.spawn_fx("block", 0, "player")
    elif pid == "fire_bomb":
        from enemies import apply_block_damage, check_boss_enrage

        for enemy in combat.living_enemies():
            hp_lost = apply_block_damage(enemy, 12)
            combat.spawn_fx("damage", hp_lost, enemy)
            check_boss_enrage(combat, enemy)
        combat.shake = max(combat.shake, 4)
    elif pid == "smoke_vial":
        combat.player["block"] += 8
        combat.spawn_fx("block", 8, "player")
        combat.draw_cards(1)
        combat.spawn_fx("draw", 1, "player")
    elif pid == "venom_phial":
        from enemies import add_status

        enemy = combat.target_enemy()
        if enemy:
            add_status(enemy, "poison", 5)
            combat.spawn_fx("damage", 5, enemy)
    elif pid == "frost_aegis":
        from enemies import add_status

        combat.player["block"] += 10
        combat.spawn_fx("block", 10, "player")
        for enemy in combat.living_enemies():
            add_status(enemy, "weak", 1)

    if not combat.living_enemies():
        combat.won = True
    return True
