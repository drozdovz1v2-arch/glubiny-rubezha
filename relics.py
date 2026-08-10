"""Реликвии — пассивные артефакты забега."""

import random

import pygame

from config import pick
from enemies import add_status
RELIC_DEFS = {
    "border_shard": {
        "name": "Осколок Рубежа",
        "desc": "В начале каждого боя +3 блока.",
        "color": (72, 210, 200),
    },
    "guardian_blade": {
        "name": "Клинок Стража",
        "desc": "Атакующие карты наносят +2 урона.",
        "color": (255, 120, 100),
    },
    "iron_ring": {
        "name": "Железный Обод",
        "desc": "Навыки блока дают +2 блока.",
        "color": (120, 170, 220),
    },
    "scavenger_pouch": {
        "name": "Мешок Собирателя",
        "desc": "+12 золота после каждого боя.",
        "color": (255, 204, 96),
    },
    "pulse_core": {
        "name": "Импульсное Ядро",
        "desc": "+1 энергия в первый ход боя.",
        "color": (180, 140, 255),
    },
    "healing_salve": {
        "name": "Мазь Рубежа",
        "desc": "После боя восстанавливаешь 4 HP.",
        "color": (98, 214, 130),
    },
    "ember_charm": {
        "name": "Угольный Амулет",
        "desc": "Первая атака каждого хода наносит +4 урона.",
        "color": (255, 140, 80),
    },
    "void_lens": {
        "name": "Линза Пустоты",
        "desc": "В начале боя возьми 1 доп. карту.",
        "color": (160, 120, 255),
    },
    "thorn_badge": {
        "name": "Шипастый Знак",
        "desc": "Когда враг бьёт тебя, он получает 4 урона.",
        "color": (200, 90, 120),
    },
    "crown_shard": {
        "name": "Осколок Короны",
        "desc": "При получении +8 max HP и лечение.",
        "color": (255, 220, 120),
        "boss": True,
    },
    "abyss_heart": {
        "name": "Сердце Бездны",
        "desc": "+20 золота после элиты или босса.",
        "color": (140, 80, 200),
        "boss": True,
    },
    "storm_ring": {
        "name": "Кольцо Бури",
        "desc": "Первая защита каждого хода +3 блока.",
        "color": (100, 180, 255),
        "boss": True,
    },
    "void_crown": {
        "name": "Корона Пустоты",
        "desc": "В начале боя все враги получают 2 уязвимости.",
        "color": (180, 90, 240),
        "boss": True,
    },
    "venom_vial": {
        "name": "Флакон Яда",
        "desc": "Карты с ядом накладывают +1 яда.",
        "color": (120, 200, 80),
    },
    "sigil_mark": {
        "name": "Печать Метки",
        "desc": "Первая атака за ход +1 уязвимость.",
        "color": (255, 160, 90),
    },
    "war_banner": {
        "name": "Знамя Войны",
        "desc": "Каждый 3-й ход возьми 1 карту.",
        "color": (200, 80, 80),
    },
    "iron_heart": {
        "name": "Железное Сердце",
        "desc": "При падении ниже 30% HP — +10 блока (раз за бой).",
        "color": (200, 100, 100),
    },
    "curse_ward": {
        "name": "Оберег от Проклятий",
        "desc": "При розыгрыше проклятия — +6 блока.",
        "color": (140, 90, 180),
    },
    "void_mirror": {
        "name": "Зеркало Пустоты",
        "desc": "Когда враг крадёт блок — получи 6 блока.",
        "color": (160, 110, 220),
    },
    "runic_flask": {
        "name": "Рунический Сосуд",
        "desc": "Первое зелье за бой — возьми 1 карту.",
        "color": (120, 200, 180),
    },
    "sand_talisman": {
        "name": "Талисман Песков",
        "desc": "С акта II: +5 блока в начале боя.",
        "color": (230, 190, 90),
    },
    "wraith_cloak": {
        "name": "Плащ Призрака",
        "desc": "Первый полученный урон за бой — +8 блока.",
        "color": (150, 120, 200),
    },
    "bark_amulet": {
        "name": "Амулет Коры",
        "desc": "Первый навык каждого хода +3 блока.",
        "color": (100, 160, 90),
    },
}

BOSS_RELICS = {"crown_shard", "abyss_heart", "storm_ring", "void_crown"}


def roll_shop_relic(owned=None):
    owned = owned or set()
    pool = [rid for rid in RELIC_DEFS if rid not in owned and rid not in BOSS_RELICS]
    if not pool:
        return None
    return pick(pool)


def shop_relic_price():
    from difficulty import shop_price
    return shop_price(200)


def shop_inventory(act=0, owned_relics=None):
    from cards import roll_card_rewards
    from difficulty import shop_price
    from potions import roll_shop_potions

    owned = set(owned_relics or [])
    prices = {"rare": 150, "uncommon": 100, "common": 60}
    items = [
        {"type": "card", "card": c, "price": shop_price(prices.get(c["rarity"], 60))}
        for c in roll_card_rewards(3, act)
    ]
    items.extend(roll_shop_potions(2))
    relic_id = roll_shop_relic(owned)
    if relic_id:
        items.append({"type": "relic", "relic_id": relic_id, "price": shop_relic_price()})
    return items


def roll_relic_rewards(count=3, owned=None, boss=False):
    owned = owned or set()
    if boss:
        pool = [rid for rid in BOSS_RELICS if rid not in owned]
        if len(pool) < count:
            pool += [rid for rid in RELIC_DEFS if rid not in owned and rid not in BOSS_RELICS]
    else:
        pool = [rid for rid in RELIC_DEFS if rid not in owned and rid not in BOSS_RELICS]
    if not pool:
        return []
    random.shuffle(pool)
    return pool[: min(count, len(pool))]


def discover_relic(meta, relic_id, save=True):
    if relic_id not in RELIC_DEFS:
        return False
    found = meta.setdefault("relics_found", [])
    if relic_id in found:
        return False
    found.append(relic_id)
    if save:
        from config import save_meta
        save_meta(meta)
    return True


def sync_discovered_relics(meta, relic_ids):
    changed = False
    for rid in relic_ids:
        if discover_relic(meta, rid, save=False):
            changed = True
    if changed:
        from config import save_meta
        save_meta(meta)


def add_relic(run, relic_id):
    relics = run.setdefault("relics", [])
    if relic_id not in relics and relic_id in RELIC_DEFS:
        relics.append(relic_id)
        if relic_id == "crown_shard":
            run["max_hp"] = run.get("max_hp", 58) + 8
            run["hp"] = min(run["max_hp"], run.get("hp", 0) + 8)


def grant_random_relic(run):
    choices = roll_relic_rewards(1, set(run.get("relics", [])))
    if choices:
        add_relic(run, choices[0])


def relic_bonus_damage(relics, card, amount, combat=None):
    if "guardian_blade" in relics and card and card.get("type") == "attack":
        amount += 2
    if (
        "ember_charm" in relics
        and card
        and card.get("type") == "attack"
        and combat
        and not combat.ember_used_this_turn
    ):
        amount += 4
        combat.ember_used_this_turn = True
    return amount


def relic_on_attack_hit(relics, combat, enemy):
    if (
        "sigil_mark" in relics
        and combat
        and enemy
        and enemy["hp"] > 0
        and not combat.mark_used_this_turn
    ):
        add_status(enemy, "vulnerable", 1)
        combat.mark_used_this_turn = True
        combat.log(f"Печать: +1 уязвимость -> {enemy['name']}")


def relic_bonus_poison(relics, amount):
    if "venom_vial" in relics:
        amount += 1
    return amount


def relic_bonus_block(relics, card, amount, combat=None):
    if "iron_ring" in relics and card and card.get("type") == "skill":
        amount += 2
    if (
        "storm_ring" in relics
        and card
        and card.get("type") == "skill"
        and combat
        and not combat.storm_used_this_turn
    ):
        amount += 3
        combat.storm_used_this_turn = True
    if (
        "bark_amulet" in relics
        and card
        and card.get("type") == "skill"
        and combat
        and not combat.bark_used_this_turn
    ):
        amount += 3
        combat.bark_used_this_turn = True
    return amount


def relic_on_curse_played(relics, combat):
    if "curse_ward" not in relics:
        return
    combat.player["block"] += 6
    combat.spawn_fx("block", 6, "player")
    combat.log("Оберег: +6 блока")


def relic_on_block_stolen(relics, combat, stolen):
    if "void_mirror" not in relics or stolen <= 0:
        return
    bonus = min(6, stolen)
    combat.player["block"] += bonus
    combat.spawn_fx("block", bonus, "player")
    combat.log("Зеркало Пустоты: +6 блока")


def relic_on_potion_used(relics, combat):
    if "runic_flask" not in relics or combat.runic_flask_used:
        return
    combat.runic_flask_used = True
    combat.draw_cards(1)
    combat.spawn_fx("draw", 1, "player")
    combat.log("Рунический Сосуд: +1 карта")


def apply_combat_start(combat):
    relics = combat.relics
    if "border_shard" in relics:
        combat.player["block"] += 3
        combat.spawn_fx("block", 3, "player")
    if "sand_talisman" in relics and combat.run_act >= 1:
        combat.player["block"] += 5
        combat.spawn_fx("block", 5, "player")
    if "pulse_core" in relics:
        combat.player["energy"] += 1
    if "void_lens" in relics:
        combat.draw_cards(1)
        combat.spawn_fx("draw", 1, "player")
    if "war_banner" in relics and combat.turn > 0 and combat.turn % 3 == 0:
        combat.draw_cards(1)
        combat.spawn_fx("draw", 1, "player")
        combat.log("Знамя: +1 карта")
    if "void_crown" in relics and combat.turn == 1:
        for enemy in combat.living_enemies():
            add_status(enemy, "vulnerable", 2)
        combat.log("Корона Пустоты: враги уязвимы")


def apply_enemy_thorns(combat, enemy, hp_lost):
    if "thorn_badge" not in combat.relics or hp_lost <= 0 or enemy["hp"] <= 0:
        return
    thorns = min(4, enemy["hp"])
    enemy["hp"] -= thorns
    combat.spawn_fx("damage", thorns, enemy)
    combat.log(f"Шипы: {thorns} урона -> {enemy['name']}")


def check_wraith_cloak(combat, hp_lost):
    if hp_lost <= 0 or "wraith_cloak" not in combat.relics or combat.wraith_cloak_used:
        return
    combat.wraith_cloak_used = True
    combat.player["block"] += 8
    combat.spawn_fx("block", 8, "player")
    combat.log("Плащ Призрака: +8 блока")


def check_iron_heart(combat, hp_lost):
    if hp_lost <= 0 or "iron_heart" not in combat.relics or combat.iron_heart_used:
        return
    if combat.player["hp"] / max(1, combat.player["max_hp"]) > 0.3:
        return
    combat.iron_heart_used = True
    combat.player["block"] += 10
    combat.spawn_fx("block", 10, "player")
    combat.log("Железное Сердце: +10 блока")


def apply_combat_end(run, relics, node_type="battle"):
    if "scavenger_pouch" in relics:
        run["gold"] = run.get("gold", 0) + 12
    if "healing_salve" in relics:
        run["hp"] = min(run["max_hp"], run.get("hp", 0) + 4)
    if "abyss_heart" in relics and node_type in ("elite", "boss"):
        run["gold"] = run.get("gold", 0) + 20


def draw_relic_icon(screen, x, y, size, relic_id):
    info = RELIC_DEFS.get(relic_id, {})
    color = info.get("color", (140, 150, 170))
    glow = pygame.Surface((size + 8, size + 8), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, 40), (size // 2 + 4, size // 2 + 4), size // 2 + 3)
    screen.blit(glow, (x - 4, y - 4))
    pygame.draw.circle(screen, (16, 20, 30), (x + size // 2, y + size // 2), size // 2)
    pygame.draw.circle(screen, color, (x + size // 2, y + size // 2), size // 2 - 2)
    cx, cy = x + size // 2, y + size // 2
    if relic_id == "guardian_blade":
        pygame.draw.line(screen, (255, 255, 255), (cx - size // 4, cy + size // 5), (cx + size // 4, cy - size // 4), max(2, size // 8))
    elif relic_id == "iron_ring":
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), size // 3, max(1, size // 10))
    elif relic_id == "pulse_core":
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(2, size // 7))
    elif relic_id == "thorn_badge":
        pygame.draw.polygon(screen, (255, 200, 210), [(cx, cy - size // 4), (cx + size // 5, cy + size // 5), (cx - size // 5, cy + size // 5)])
    elif relic_id == "void_lens":
        pygame.draw.ellipse(screen, (220, 210, 255), (cx - size // 4, cy - size // 5, size // 2, size // 3), max(1, size // 10))
    elif relic_id == "venom_vial":
        pygame.draw.rect(screen, (200, 255, 180), (cx - size // 6, cy - size // 4, size // 3, size // 2), border_radius=2)
    elif relic_id == "sigil_mark":
        pygame.draw.polygon(screen, (255, 220, 180), [(cx, cy - size // 4), (cx + size // 4, cy + size // 5), (cx - size // 4, cy + size // 5)])
    elif relic_id == "war_banner":
        pygame.draw.line(screen, (255, 200, 200), (cx, cy - size // 3), (cx, cy + size // 4), max(2, size // 8))
        pygame.draw.polygon(screen, (255, 120, 120), [(cx, cy - size // 3), (cx + size // 3, cy - size // 6), (cx, cy)])
    elif relic_id == "iron_heart":
        pygame.draw.circle(screen, (255, 160, 160), (cx, cy), size // 4)
        pygame.draw.circle(screen, (255, 220, 220), (cx - 2, cy - 2), max(2, size // 8))
    elif relic_id == "curse_ward":
        pygame.draw.polygon(screen, (200, 160, 255), [(cx, cy - size // 4), (cx + size // 4, cy + size // 6), (cx - size // 4, cy + size // 6)])
        pygame.draw.line(screen, (255, 220, 255), (cx, cy - size // 5), (cx, cy + size // 5), max(1, size // 10))
    elif relic_id == "void_crown":
        pygame.draw.polygon(screen, (200, 140, 255), [(cx - size // 4, cy + size // 6), (cx - size // 6, cy - size // 4), (cx, cy - size // 6), (cx + size // 6, cy - size // 4), (cx + size // 4, cy + size // 6)])
    elif relic_id == "void_mirror":
        pygame.draw.ellipse(screen, (180, 140, 255), (cx - size // 3, cy - size // 4, size * 2 // 3, size // 2), 2)
        pygame.draw.line(screen, (220, 200, 255), (cx - size // 5, cy - size // 6), (cx + size // 5, cy + size // 6), 2)
    elif relic_id == "runic_flask":
        pygame.draw.rect(screen, (140, 220, 200), (cx - size // 6, cy - size // 5, size // 3, size // 2), border_radius=3)
        pygame.draw.circle(screen, (180, 255, 230), (cx, cy - size // 4), size // 8)
    elif relic_id == "sand_talisman":
        pygame.draw.polygon(screen, (255, 230, 160), [(cx, cy - size // 4), (cx + size // 4, cy + size // 6), (cx - size // 4, cy + size // 6)])
    elif relic_id == "wraith_cloak":
        pygame.draw.polygon(screen, (180, 150, 230), [(cx, cy - size // 4), (cx + size // 3, cy + size // 5), (cx, cy + size // 3), (cx - size // 3, cy + size // 5)])
    elif relic_id == "bark_amulet":
        pygame.draw.polygon(screen, (140, 200, 110), [(cx, cy - size // 4), (cx + size // 4, cy + size // 6), (cx - size // 4, cy + size // 6)])
        pygame.draw.circle(screen, (200, 240, 180), (cx, cy - size // 8), size // 10)
    else:
        pygame.draw.circle(screen, (255, 255, 255), (cx - size // 5, cy - size // 5), max(2, size // 6))
