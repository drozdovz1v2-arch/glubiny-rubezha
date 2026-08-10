import random
import uuid

from config import pick, shuffle
from difficulty import shop_price

REWARD_POOL = {
    "common": ["heavy_blow", "shield_wall", "rally", "quick_slash", "crushing_mark", "desperate_guard"],
    "uncommon": ["piercing_strike", "frost_edge", "venom_dagger", "battle_cry", "expose", "shatter_strike", "toxic_bloom", "phantom_cut", "void_lance", "warding_pulse", "sand_barrier", "cinder_strike", "root_snare"],
    "rare": ["iron_will", "whirlwind", "execute", "frontier_pulse", "ruin_strike", "blood_pact", "soul_siphon", "mirror_blow", "shatter_guard"],
}

CARD_DEFS = {
    "strike": {"name": "Удар", "type": "attack", "cost": 1, "rarity": "starter", "desc": "Наносит 5 урона.", "effect": "strike"},
    "defend": {"name": "Защита", "type": "skill", "cost": 1, "rarity": "starter", "desc": "Даёт 4 блока.", "effect": "defend"},
    "quick_slash": {"name": "Быстрый Рез", "type": "attack", "cost": 0, "rarity": "common", "desc": "Наносит 4 урона. Возьми 1 карту.", "effect": "quick_slash"},
    "heavy_blow": {"name": "Сокрушительный Удар", "type": "attack", "cost": 2, "rarity": "common", "desc": "Наносит 14 урона.", "effect": "heavy_blow"},
    "shield_wall": {"name": "Стена Щитов", "type": "skill", "cost": 2, "rarity": "common", "desc": "Даёт 12 блока.", "effect": "shield_wall"},
    "rally": {"name": "Сбор", "type": "skill", "cost": 1, "rarity": "common", "desc": "Возьми 2 карты.", "effect": "rally"},
    "piercing_strike": {"name": "Пронзающий Удар", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 8 урона. Игнорирует блок.", "effect": "piercing_strike"},
    "frost_edge": {"name": "Ледяной Клинок", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 7 урона. Накладывает 2 Слабости.", "effect": "frost_edge"},
    "venom_dagger": {"name": "Ядовитый Кинжал", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 5 урона. Накладывает 3 Яда.", "effect": "venom_dagger"},
    "battle_cry": {"name": "Боевой Клич", "type": "power", "cost": 1, "rarity": "uncommon", "desc": "В начале хода получай 1 Силы.", "effect": "battle_cry"},
    "iron_will": {"name": "Железная Воля", "type": "power", "cost": 2, "rarity": "rare", "desc": "В начале хода получай 4 блока.", "effect": "iron_will"},
    "whirlwind": {"name": "Вихрь", "type": "attack", "cost": 1, "rarity": "rare", "desc": "Наносит 3 урона 3 раза.", "effect": "whirlwind"},
    "execute": {"name": "Казнь", "type": "attack", "cost": 2, "rarity": "rare", "desc": "Наносит 10 урона. +8 если враг ниже 50% HP.", "effect": "execute"},
    "frontier_pulse": {"name": "Импульс Рубежа", "type": "skill", "cost": 0, "rarity": "rare", "desc": "Даёт 3 блока. Возьми 1. Сбрось 1.", "effect": "frontier_pulse"},
    "ruin_strike": {"name": "Удар Руин", "type": "attack", "cost": 2, "rarity": "rare", "desc": "Наносит 18 урона. Теряешь 3 HP.", "effect": "ruin_strike"},
    "crushing_mark": {"name": "Сокрушающая Метка", "type": "attack", "cost": 1, "rarity": "common", "desc": "Наносит 4 урона. Накладывает 2 Уязвимости.", "effect": "crushing_mark"},
    "expose": {"name": "Разоблачение", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "Накладывает 3 Уязвимости. Возьми 1 карту.", "effect": "expose"},
    "shatter_strike": {"name": "Удар Раскола", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 8 урона. +6 если цель уязвима.", "effect": "shatter_strike"},
    "toxic_bloom": {"name": "Ядовитый Цветок", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "Даёт 5 блока. Накладывает 3 Яда.", "effect": "toxic_bloom"},
    "desperate_guard": {"name": "Отчаянная Защита", "type": "skill", "cost": 1, "rarity": "common", "desc": "Даёт 8 блока. 14 если HP ниже 50%.", "effect": "desperate_guard"},
    "blood_pact": {"name": "Кровавый Пакт", "type": "power", "cost": 1, "rarity": "rare", "desc": "В начале хода: +1 сила, −2 HP.", "effect": "blood_pact"},
    "phantom_cut": {"name": "Призрачный Разрез", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 7 урона. +5 если у врага есть эффект.", "effect": "phantom_cut"},
    "soul_siphon": {"name": "Вампирский Удар", "type": "attack", "cost": 1, "rarity": "rare", "desc": "Наносит 6 урона. Восстанавливает 3 HP.", "effect": "soul_siphon"},
    "void_lance": {"name": "Копьё Пустоты", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 9 урона. Игнорирует блок.", "effect": "void_lance"},
    "warding_pulse": {"name": "Импульс Защиты", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "Даёт 7 блока. Возьми 1 карту.", "effect": "warding_pulse"},
    "sand_barrier": {"name": "Песчаный Барьер", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "Даёт 8 блока. Накладывает 1 Слабости.", "effect": "sand_barrier"},
    "cinder_strike": {"name": "Удар Угля", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 7 урона. Накладывает 3 Яда.", "effect": "cinder_strike"},
    "mirror_blow": {"name": "Зеркальный Удар", "type": "attack", "cost": 1, "rarity": "rare", "desc": "6 урона + до 10 от твоего блока.", "effect": "mirror_blow"},
    "root_snare": {"name": "Корневая Петля", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "5 блока, 2 Уязвимости, возьми 1.", "effect": "root_snare"},
    "shatter_guard": {"name": "Удар по Стражу", "type": "attack", "cost": 2, "rarity": "rare", "desc": "10 урона. +8 если у цели есть блок.", "effect": "shatter_guard"},
    "curse_wound": {"name": "Рана", "type": "curse", "cost": -1, "rarity": "curse", "unplayable": True, "desc": "Проклятие. Нельзя разыграть.", "effect": "curse_none"},
    "curse_doubt": {"name": "Сомнение", "type": "curse", "cost": 1, "rarity": "curse", "desc": "Сбрось 1 случайную карту.", "effect": "curse_doubt"},
    "curse_hex": {"name": "Сглаз", "type": "curse", "cost": 0, "rarity": "curse", "unplayable": True, "desc": "Проклятие. Занимает руку.", "effect": "curse_none"},
}

CURSE_IDS = ("curse_wound", "curse_doubt", "curse_hex")

CARD_UPGRADES = {
    "strike": {"effect": "strike_up", "desc": "Наносит 7 урона."},
    "defend": {"effect": "defend_up", "desc": "Даёт 6 блока."},
    "quick_slash": {"effect": "quick_slash_up", "desc": "Наносит 6 урона. Возьми 1 карту."},
    "heavy_blow": {"effect": "heavy_blow_up", "desc": "Наносит 18 урона."},
    "shield_wall": {"effect": "shield_wall_up", "desc": "Даёт 16 блока."},
    "rally": {"effect": "rally_up", "desc": "Возьми 3 карты."},
    "battle_cry": {"effect": "battle_cry_up", "desc": "В начале хода получай 2 Силы."},
    "iron_will": {"effect": "iron_will_up", "desc": "В начале хода получай 6 блока."},
    "piercing_strike": {"effect": "piercing_strike_up", "desc": "Наносит 11 урона. Игнорирует блок."},
    "frost_edge": {"effect": "frost_edge_up", "desc": "Наносит 10 урона. Накладывает 3 Слабости."},
    "venom_dagger": {"effect": "venom_dagger_up", "desc": "Наносит 7 урона. Накладывает 5 Яда."},
    "whirlwind": {"effect": "whirlwind_up", "desc": "Наносит 4 урона 3 раза."},
    "execute": {"effect": "execute_up", "desc": "Наносит 13 урона. +10 если враг ниже 50% HP."},
    "frontier_pulse": {"effect": "frontier_pulse_up", "desc": "Даёт 5 блока. Возьми 1. Сбрось 1."},
    "ruin_strike": {"effect": "ruin_strike_up", "desc": "Наносит 22 урона. Теряешь 3 HP."},
    "crushing_mark": {"effect": "crushing_mark_up", "desc": "Наносит 6 урона. Накладывает 3 Уязвимости."},
    "expose": {"effect": "expose_up", "desc": "Накладывает 4 Уязвимости. Возьми 1 карту."},
    "shatter_strike": {"effect": "shatter_strike_up", "desc": "Наносит 11 урона. +8 если цель уязвима."},
    "toxic_bloom": {"effect": "toxic_bloom_up", "desc": "Даёт 7 блока. Накладывает 4 Яда."},
    "desperate_guard": {"effect": "desperate_guard_up", "desc": "Даёт 10 блока. 18 если HP ниже 50%."},
    "blood_pact": {"effect": "blood_pact_up", "desc": "В начале хода: +2 силы, −2 HP."},
    "phantom_cut": {"effect": "phantom_cut_up", "desc": "Наносит 10 урона. +7 если у врага есть эффект."},
    "soul_siphon": {"effect": "soul_siphon_up", "desc": "Наносит 9 урона. Восстанавливает 5 HP."},
    "void_lance": {"effect": "void_lance_up", "desc": "Наносит 12 урона. Игнорирует блок."},
    "warding_pulse": {"effect": "warding_pulse_up", "desc": "Даёт 10 блока. Возьми 1 карту."},
    "sand_barrier": {"effect": "sand_barrier_up", "desc": "Даёт 11 блока. Накладывает 2 Слабости."},
    "cinder_strike": {"effect": "cinder_strike_up", "desc": "Наносит 9 урона. Накладывает 4 Яда."},
    "mirror_blow": {"effect": "mirror_blow_up", "desc": "8 урона + до 14 от твоего блока."},
    "root_snare": {"effect": "root_snare_up", "desc": "7 блока, 3 Уязвимости, возьми 1."},
    "shatter_guard": {"effect": "shatter_guard_up", "desc": "12 урона. +10 если у цели есть блок."},
}


def preview_upgrade(card):
    if card.get("upgraded") or card["id"] not in CARD_UPGRADES:
        return None
    up = CARD_UPGRADES[card["id"]]
    base = CARD_DEFS.get(card["id"], card)
    return {**card, "name": f"{base['name']}+", "desc": up["desc"], "upgraded": True}


def upgrade_card(card):
    if card.get("upgraded") or card["id"] not in CARD_UPGRADES:
        return False
    up = CARD_UPGRADES[card["id"]]
    card["upgraded"] = True
    card["name"] = f"{card['name']}+"
    card["desc"] = up["desc"]
    card["effect"] = up["effect"]
    return True


def removable_cards(deck, min_size=5):
    seen = set()
    unique = []
    for card in deck:
        if card["uid"] not in seen:
            seen.add(card["uid"])
            unique.append(card)
    curses = [c for c in unique if c.get("type") == "curse"]
    others = [c for c in unique if c.get("type") != "curse"]
    result = list(curses)
    if len(others) > min_size:
        result.extend(others)
    return result


def add_curse_to_run(run, curse_id=None):
    cid = curse_id or pick(list(CURSE_IDS))
    run.setdefault("deck", []).append(create_card(cid))
    return cid


def upgradable_cards(deck):
    return [c for c in deck if not c.get("upgraded") and c["id"] in CARD_UPGRADES and c.get("type") != "curse"]


def create_card(card_id):
    base = CARD_DEFS.get(card_id, CARD_DEFS["strike"])
    return {"id": card_id, "uid": f"{card_id}_{uuid.uuid4().hex[:8]}", **base}


def starter_deck():
    deck = [create_card("strike") for _ in range(4)]
    deck += [create_card("defend") for _ in range(5)]
    deck.append(create_card("quick_slash"))
    return shuffle(deck)


def roll_card_rewards(count=3, act=0):
    weights = (
        (0.7, 0.25, 0.05) if act == 0 else
        (0.5, 0.35, 0.15) if act == 1 else
        (0.35, 0.4, 0.25) if act == 2 else
        (0.25, 0.45, 0.30)
    )
    picks = []
    used = set()
    while len(picks) < count:
        roll = random.random()
        rarity = "common"
        if roll > weights[0] + weights[1]:
            rarity = "rare"
        elif roll > weights[0]:
            rarity = "uncommon"
        pool = [cid for cid in REWARD_POOL[rarity] if cid not in used]
        if not pool:
            continue
        cid = pick(pool)
        used.add(cid)
        picks.append(create_card(cid))
    return picks


def roll_rare_card_reward():
    pool = REWARD_POOL["rare"]
    return [create_card(pick(pool))]


def shop_removal_price():
    return shop_price(75)


def shop_cards(act=0):
    from relics import shop_inventory
    return shop_inventory(act)


def all_card_ids():
    return list(CARD_DEFS.keys())


def discover_card(meta, card_id, save=True):
    if card_id not in CARD_DEFS:
        return False
    found = meta.setdefault("cards_found", [])
    if card_id in found:
        return False
    found.append(card_id)
    if save:
        from config import save_meta
        save_meta(meta)
    return True


def sync_discovered_cards(meta, cards):
    changed = False
    for card in cards:
        if discover_card(meta, card.get("id"), save=False):
            changed = True
    if changed:
        from config import save_meta
        save_meta(meta)
        from achievements import check_card_achievements
        check_card_achievements(meta)


def play_card_effect(effect_id, ctx):
    effects = {
        "strike": lambda: ctx.deal_damage(5),
        "defend": lambda: ctx.gain_block(4),
        "quick_slash": lambda: (ctx.deal_damage(4), ctx.draw_cards(1)),
        "heavy_blow": lambda: ctx.deal_damage(14),
        "shield_wall": lambda: ctx.gain_block(12),
        "rally": lambda: ctx.draw_cards(2),
        "piercing_strike": lambda: ctx.deal_damage(8, pierce=True),
        "frost_edge": lambda: (ctx.deal_damage(7), ctx.apply_status("weak", 2)),
        "venom_dagger": lambda: (ctx.deal_damage(5), ctx.apply_status("poison", 3)),
        "battle_cry": lambda: ctx.gain_power("strength", 1),
        "iron_will": lambda: ctx.gain_power("metallicize", 4),
        "whirlwind": lambda: [ctx.deal_damage(3) for _ in range(3)],
        "execute": lambda: ctx.deal_damage(10 + (8 if ctx.enemy_hp_percent() < 0.5 else 0)),
        "frontier_pulse": lambda: (ctx.gain_block(3), ctx.draw_cards(1), ctx.discard_random(1)),
        "ruin_strike": lambda: (ctx.deal_damage(18), ctx.self_damage(3)),
        "crushing_mark": lambda: (ctx.deal_damage(4), ctx.apply_status("vulnerable", 2)),
        "expose": lambda: (ctx.apply_status("vulnerable", 3), ctx.draw_cards(1)),
        "shatter_strike": lambda: ctx.deal_damage(8 + (6 if ctx.enemy_has_status("vulnerable") else 0)),
        "toxic_bloom": lambda: (ctx.gain_block(5), ctx.apply_status("poison", 3)),
        "desperate_guard": lambda: ctx.gain_block(14 if ctx.player_hp_percent() < 0.5 else 8),
        "blood_pact": lambda: ctx.gain_power("blood_pact", 1),
        "phantom_cut": lambda: ctx.deal_damage(7 + (5 if ctx.enemy_has_any_status() else 0)),
        "soul_siphon": lambda: (ctx.deal_damage(6), ctx.heal(3)),
        "void_lance": lambda: ctx.deal_damage(9, pierce=True),
        "warding_pulse": lambda: (ctx.gain_block(7), ctx.draw_cards(1)),
        "sand_barrier": lambda: (ctx.gain_block(8), ctx.apply_status("weak", 1)),
        "cinder_strike": lambda: (ctx.deal_damage(7), ctx.apply_status("poison", 3)),
        "mirror_blow": lambda: ctx.deal_damage(6 + min(ctx.player_block(), 10)),
        "root_snare": lambda: (ctx.gain_block(5), ctx.apply_status("vulnerable", 2), ctx.draw_cards(1)),
        "shatter_guard": lambda: ctx.deal_shatter_guard(10, 8),
        "curse_doubt": lambda: ctx.discard_random(1),
        "curse_none": lambda: None,
        "strike_up": lambda: ctx.deal_damage(7),
        "defend_up": lambda: ctx.gain_block(6),
        "quick_slash_up": lambda: (ctx.deal_damage(6), ctx.draw_cards(1)),
        "heavy_blow_up": lambda: ctx.deal_damage(18),
        "shield_wall_up": lambda: ctx.gain_block(16),
        "rally_up": lambda: ctx.draw_cards(3),
        "battle_cry_up": lambda: ctx.gain_power("strength", 2),
        "iron_will_up": lambda: ctx.gain_power("metallicize", 6),
        "piercing_strike_up": lambda: ctx.deal_damage(11, pierce=True),
        "frost_edge_up": lambda: (ctx.deal_damage(10), ctx.apply_status("weak", 3)),
        "venom_dagger_up": lambda: (ctx.deal_damage(7), ctx.apply_status("poison", 5)),
        "whirlwind_up": lambda: [ctx.deal_damage(4) for _ in range(3)],
        "execute_up": lambda: ctx.deal_damage(13 + (10 if ctx.enemy_hp_percent() < 0.5 else 0)),
        "frontier_pulse_up": lambda: (ctx.gain_block(5), ctx.draw_cards(1), ctx.discard_random(1)),
        "ruin_strike_up": lambda: (ctx.deal_damage(22), ctx.self_damage(3)),
        "crushing_mark_up": lambda: (ctx.deal_damage(6), ctx.apply_status("vulnerable", 3)),
        "expose_up": lambda: (ctx.apply_status("vulnerable", 4), ctx.draw_cards(1)),
        "shatter_strike_up": lambda: ctx.deal_damage(11 + (8 if ctx.enemy_has_status("vulnerable") else 0)),
        "toxic_bloom_up": lambda: (ctx.gain_block(7), ctx.apply_status("poison", 4)),
        "desperate_guard_up": lambda: ctx.gain_block(18 if ctx.player_hp_percent() < 0.5 else 10),
        "phantom_cut_up": lambda: ctx.deal_damage(10 + (7 if ctx.enemy_has_any_status() else 0)),
        "soul_siphon_up": lambda: (ctx.deal_damage(9), ctx.heal(5)),
        "void_lance_up": lambda: ctx.deal_damage(12, pierce=True),
        "warding_pulse_up": lambda: (ctx.gain_block(10), ctx.draw_cards(1)),
        "sand_barrier_up": lambda: (ctx.gain_block(11), ctx.apply_status("weak", 2)),
        "cinder_strike_up": lambda: (ctx.deal_damage(9), ctx.apply_status("poison", 4)),
        "mirror_blow_up": lambda: ctx.deal_damage(8 + min(ctx.player_block(), 14)),
        "root_snare_up": lambda: (ctx.gain_block(7), ctx.apply_status("vulnerable", 3), ctx.draw_cards(1)),
        "shatter_guard_up": lambda: ctx.deal_shatter_guard(12, 10),
        "blood_pact_up": lambda: ctx.gain_power("blood_pact", 2),
    }
    fn = effects.get(effect_id, effects["strike"])
    fn()
