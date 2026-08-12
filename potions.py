import random

from config import pick

POTION_MAX = 3
POTION_USES = 3

POTION_DEFS = {
    "healing_draught": {
        "name": "Целебный Настой",
        "desc": "Восстанови 20 HP. · 3 использования",
        "color": (98, 214, 130),
        "price": 50,
    },
    "iron_brew": {
        "name": "Железный Отвар",
        "desc": "Получи 12 блока. · 3 использования",
        "color": (111, 168, 255),
        "price": 45,
    },
    "focus_tonic": {
        "name": "Тоник Фокуса",
        "desc": "+1 энергия, возьми 1 карту. · 3 использования",
        "color": (255, 204, 96),
        "price": 55,
    },
    "purify_flask": {
        "name": "Сосуд Очищения",
        "desc": "Сними слабость и яд. · 3 использования",
        "color": (180, 140, 255),
        "price": 48,
    },
    "fire_bomb": {
        "name": "Огненная Смесь",
        "desc": "12 урона всем врагам. · 3 использования",
        "color": (255, 120, 80),
        "price": 60,
    },
    "smoke_vial": {
        "name": "Дымовая Смесь",
        "desc": "8 блока и возьми 1 карту. · 3 использования",
        "color": (160, 170, 190),
        "price": 52,
    },
    "venom_phial": {
        "name": "Ядовитый Флакон",
        "desc": "Накладывает 5 Яда на цель. · 3 использования",
        "color": (140, 210, 90),
        "price": 50,
    },
    "frost_aegis": {
        "name": "Ледяной Эгида",
        "desc": "10 блока. Враги получают 1 Слабости. · 3 использования",
        "color": (130, 190, 240),
        "price": 54,
    },
    "void_tonic": {
        "name": "Тоник Пустоты",
        "desc": "8 урона всем врагам. · 3 использования",
        "color": (160, 100, 220),
        "price": 58,
    },
    "steel_draught": {
        "name": "Стальной Настой",
        "desc": "14 блока. · 3 использования",
        "color": (100, 180, 200),
        "price": 52,
    },
    "hunter_brew": {
        "name": "Настой Охотника",
        "desc": "6 урона + 3 яда. · 3 использования",
        "color": (220, 90, 100),
        "price": 56,
    },
}


def normalize_potion(entry):
    if isinstance(entry, str):
        return {"id": entry, "uses": POTION_USES}
    if isinstance(entry, dict):
        pid = entry.get("id") or entry.get("potion_id")
        if pid not in POTION_DEFS:
            return None
        uses = entry.get("uses", POTION_USES)
        if uses <= 0:
            return None
        return {"id": pid, "uses": uses}
    return None


def normalize_potions(potions):
    out = []
    for entry in potions or []:
        norm = normalize_potion(entry)
        if norm:
            out.append(norm)
    return out


def potion_id(entry):
    if isinstance(entry, str):
        return entry
    return entry.get("id") if isinstance(entry, dict) else None


def can_add_potion(run):
    return len(normalize_potions(run.get("potions", []))) < POTION_MAX


def add_potion(run, potion_id):
    if potion_id not in POTION_DEFS or not can_add_potion(run):
        return False
    potions = normalize_potions(run.get("potions", []))
    potions.append({"id": potion_id, "uses": POTION_USES})
    run["potions"] = potions
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
    potions = normalize_potions(combat.potions)
    combat.potions = potions
    if index < 0 or index >= len(potions):
        return False
    entry = potions[index]
    pid = entry["id"]
    info = POTION_DEFS.get(pid, {})
    combat.potion_used_this_turn = True
    entry["uses"] -= 1
    remaining = entry["uses"]
    if remaining > 0:
        combat.log(f"Зелье: {info.get('name', pid)} (осталось {remaining})")
    else:
        potions.pop(index)
        combat.log(f"Зелье: {info.get('name', pid)}")
    from relics import relic_on_potion_used
    relic_on_potion_used(combat.relics, combat)

    if pid == "healing_draught":
        heal = min(20, combat.player["max_hp"] - combat.player["hp"])
        combat.player["hp"] += heal
        combat.spawn_fx("heal", heal, "player")
    elif pid == "iron_brew":
        combat.add_player_block(12)
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
        combat.add_player_block(8)
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

        combat.add_player_block(10)
        combat.spawn_fx("block", 10, "player")
        for enemy in combat.living_enemies():
            add_status(enemy, "weak", 1)
    elif pid == "void_tonic":
        from enemies import apply_block_damage, check_boss_enrage
        for enemy in combat.living_enemies():
            hp_lost = apply_block_damage(enemy, 8)
            combat.spawn_fx("damage", hp_lost, enemy)
            check_boss_enrage(combat, enemy)
    elif pid == "steel_draught":
        combat.add_player_block(14)
        combat.spawn_fx("block", 14, "player")
    elif pid == "hunter_brew":
        from enemies import add_status, apply_block_damage, check_boss_enrage
        enemy = combat.target_enemy()
        if enemy:
            hp_lost = apply_block_damage(enemy, 6)
            add_status(enemy, "poison", 3)
            combat.spawn_fx("damage", hp_lost, enemy)
            check_boss_enrage(combat, enemy)

    if not combat.living_enemies():
        combat.won = True
    return True
