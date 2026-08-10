import random
import uuid

from config import pick, shuffle
from difficulty import shop_price

REWARD_POOL = {
    "common": ["heavy_blow", "shield_wall", "rally", "quick_slash", "crushing_mark", "desperate_guard", "arc_slash", "fortify", "deflect", "surge_strike", "guard_break"],
    "uncommon": ["piercing_strike", "frost_edge", "venom_dagger", "battle_cry", "expose", "shatter_strike", "toxic_bloom", "phantom_cut", "void_lance", "warding_pulse", "sand_barrier", "cinder_strike", "root_snare", "vital_surge", "double_tap", "focus", "marking_shot"],
    "rare": ["iron_will", "whirlwind", "execute", "frontier_pulse", "ruin_strike", "blood_pact", "soul_siphon", "mirror_blow", "shatter_guard", "razor_flurry", "bastion", "adrenaline_rush"],
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
    "arc_slash": {"name": "Дуговой Удар", "type": "attack", "cost": 1, "rarity": "common", "desc": "Наносит 6 урона.", "effect": "arc_slash"},
    "fortify": {"name": "Укрепление", "type": "skill", "cost": 1, "rarity": "common", "desc": "Даёт 6 блока.", "effect": "fortify"},
    "deflect": {"name": "Отвод", "type": "skill", "cost": 1, "rarity": "common", "desc": "Даёт 3 блока. Возьми 1 карту.", "effect": "deflect"},
    "vital_surge": {"name": "Прилив Сил", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 5 урона. Восстанавливает 2 HP.", "effect": "vital_surge"},
    "double_tap": {"name": "Двойной Удар", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 3 урона дважды.", "effect": "double_tap"},
    "razor_flurry": {"name": "Бритвенный Шторм", "type": "attack", "cost": 2, "rarity": "rare", "desc": "Наносит 4 урона 3 раза.", "effect": "razor_flurry"},
    "bastion": {"name": "Бастион", "type": "power", "cost": 2, "rarity": "rare", "desc": "В начале хода получай 3 блока.", "effect": "bastion"},
    "surge_strike": {"name": "Пробой", "type": "attack", "cost": 1, "rarity": "common", "desc": "Наносит 7 урона. +3 если у тебя нет блока.", "effect": "surge_strike"},
    "guard_break": {"name": "Слом Стража", "type": "attack", "cost": 1, "rarity": "common", "desc": "6 урона. +8 если у цели есть блок.", "effect": "guard_break"},
    "focus": {"name": "Концентрация", "type": "skill", "cost": 1, "rarity": "uncommon", "desc": "Возьми 2 карты. Сбрось 1.", "effect": "focus"},
    "marking_shot": {"name": "Меткий Выстрел", "type": "attack", "cost": 1, "rarity": "uncommon", "desc": "Наносит 5 урона. Накладывает 2 Слабости.", "effect": "marking_shot"},
    "adrenaline_rush": {"name": "Адреналин", "type": "skill", "cost": 0, "rarity": "rare", "desc": "Возьми 2 карты. Теряешь 2 HP.", "effect": "adrenaline_rush"},
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
    "arc_slash": {"effect": "arc_slash_up", "desc": "Наносит 8 урона."},
    "fortify": {"effect": "fortify_up", "desc": "Даёт 9 блока."},
    "deflect": {"effect": "deflect_up", "desc": "Даёт 5 блока. Возьми 1 карту."},
    "vital_surge": {"effect": "vital_surge_up", "desc": "Наносит 7 урона. Восстанавливает 4 HP."},
    "double_tap": {"effect": "double_tap_up", "desc": "Наносит 4 урона дважды."},
    "razor_flurry": {"effect": "razor_flurry_up", "desc": "Наносит 5 урона 3 раза."},
    "bastion": {"effect": "bastion_up", "desc": "В начале хода получай 5 блока."},
    "surge_strike": {"effect": "surge_strike_up", "desc": "Наносит 9 урона. +4 если у тебя нет блока."},
    "guard_break": {"effect": "guard_break_up", "desc": "8 урона. +10 если у цели есть блок."},
    "focus": {"effect": "focus_up", "desc": "Возьми 3 карты. Сбрось 1."},
    "marking_shot": {"effect": "marking_shot_up", "desc": "Наносит 7 урона. Накладывает 3 Слабости."},
    "adrenaline_rush": {"effect": "adrenaline_rush_up", "desc": "Возьми 3 карты. Теряешь 2 HP."},
}


CARD_SCALING = {
    "strike": {
        "stats": {"damage": (5, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage")),
    },
    "defend": {
        "stats": {"block": (4, 2)},
        "desc": lambda s: f"Даёт {s('block')} блока.",
        "play": lambda s, ctx: ctx.gain_block(s("block")),
    },
    "quick_slash": {
        "stats": {"damage": (4, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Возьми 1 карту.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.draw_cards(1)),
    },
    "heavy_blow": {
        "stats": {"damage": (14, 4)},
        "desc": lambda s: f"Наносит {s('damage')} урона.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage")),
    },
    "shield_wall": {
        "stats": {"block": (12, 4)},
        "desc": lambda s: f"Даёт {s('block')} блока.",
        "play": lambda s, ctx: ctx.gain_block(s("block")),
    },
    "rally": {
        "stats": {"draw": (2, 1)},
        "desc": lambda s: f"Возьми {s('draw')} карты.",
        "play": lambda s, ctx: ctx.draw_cards(s("draw")),
    },
    "piercing_strike": {
        "stats": {"damage": (8, 3)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Игнорирует блок.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage"), pierce=True),
    },
    "frost_edge": {
        "stats": {"damage": (7, 3), "weak": (2, 1)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Накладывает {s('weak')} Слабости.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.apply_status("weak", s("weak"))),
    },
    "venom_dagger": {
        "stats": {"damage": (5, 2), "poison": (3, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Накладывает {s('poison')} Яда.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.apply_status("poison", s("poison"))),
    },
    "battle_cry": {
        "stats": {"strength": (1, 1)},
        "desc": lambda s: f"В начале хода получай {s('strength')} Силы.",
        "play": lambda s, ctx: ctx.gain_power("strength", s("strength")),
    },
    "iron_will": {
        "stats": {"metallicize": (4, 2)},
        "desc": lambda s: f"В начале хода получай {s('metallicize')} блока.",
        "play": lambda s, ctx: ctx.gain_power("metallicize", s("metallicize")),
    },
    "whirlwind": {
        "stats": {"damage": (3, 1), "hits": (3, 0)},
        "desc": lambda s: f"Наносит {s('damage')} урона {s('hits')} раза.",
        "play": lambda s, ctx: [ctx.deal_damage(s("damage")) for _ in range(s("hits"))],
    },
    "execute": {
        "stats": {"damage": (10, 3), "bonus": (8, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. +{s('bonus')} если враг ниже 50% HP.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage") + (s("bonus") if ctx.enemy_hp_percent() < 0.5 else 0)),
    },
    "frontier_pulse": {
        "stats": {"block": (3, 2)},
        "desc": lambda s: f"Даёт {s('block')} блока. Возьми 1. Сбрось 1.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.draw_cards(1), ctx.discard_random(1)),
    },
    "ruin_strike": {
        "stats": {"damage": (18, 4)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Теряешь 3 HP.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.self_damage(3)),
    },
    "crushing_mark": {
        "stats": {"damage": (4, 2), "vulnerable": (2, 1)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Накладывает {s('vulnerable')} Уязвимости.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.apply_status("vulnerable", s("vulnerable"))),
    },
    "expose": {
        "stats": {"vulnerable": (3, 1)},
        "desc": lambda s: f"Накладывает {s('vulnerable')} Уязвимости. Возьми 1 карту.",
        "play": lambda s, ctx: (ctx.apply_status("vulnerable", s("vulnerable")), ctx.draw_cards(1)),
    },
    "shatter_strike": {
        "stats": {"damage": (8, 3), "bonus": (6, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. +{s('bonus')} если цель уязвима.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage") + (s("bonus") if ctx.enemy_has_status("vulnerable") else 0)),
    },
    "toxic_bloom": {
        "stats": {"block": (5, 2), "poison": (3, 1)},
        "desc": lambda s: f"Даёт {s('block')} блока. Накладывает {s('poison')} Яда.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.apply_status("poison", s("poison"))),
    },
    "desperate_guard": {
        "stats": {"block": (8, 2), "low_block": (14, 4)},
        "desc": lambda s: f"Даёт {s('block')} блока. {s('low_block')} если HP ниже 50%.",
        "play": lambda s, ctx: ctx.gain_block(s("low_block") if ctx.player_hp_percent() < 0.5 else s("block")),
    },
    "blood_pact": {
        "stats": {"strength": (1, 1)},
        "desc": lambda s: f"В начале хода: +{s('strength')} силы, −2 HP.",
        "play": lambda s, ctx: ctx.gain_power("blood_pact", s("strength")),
    },
    "phantom_cut": {
        "stats": {"damage": (7, 3), "bonus": (5, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. +{s('bonus')} если у врага есть эффект.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage") + (s("bonus") if ctx.enemy_has_any_status() else 0)),
    },
    "soul_siphon": {
        "stats": {"damage": (6, 3), "heal": (3, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Восстанавливает {s('heal')} HP.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.heal(s("heal"))),
    },
    "void_lance": {
        "stats": {"damage": (9, 3)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Игнорирует блок.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage"), pierce=True),
    },
    "warding_pulse": {
        "stats": {"block": (7, 3)},
        "desc": lambda s: f"Даёт {s('block')} блока. Возьми 1 карту.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.draw_cards(1)),
    },
    "sand_barrier": {
        "stats": {"block": (8, 3), "weak": (1, 1)},
        "desc": lambda s: f"Даёт {s('block')} блока. Накладывает {s('weak')} Слабости.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.apply_status("weak", s("weak"))),
    },
    "cinder_strike": {
        "stats": {"damage": (7, 2), "poison": (3, 1)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Накладывает {s('poison')} Яда.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.apply_status("poison", s("poison"))),
    },
    "mirror_blow": {
        "stats": {"damage": (6, 2), "mirror_cap": (10, 4)},
        "desc": lambda s: f"{s('damage')} урона + до {s('mirror_cap')} от твоего блока.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage") + min(ctx.player_block(), s("mirror_cap"))),
    },
    "root_snare": {
        "stats": {"block": (5, 2), "vulnerable": (2, 1)},
        "desc": lambda s: f"{s('block')} блока, {s('vulnerable')} Уязвимости, возьми 1.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.apply_status("vulnerable", s("vulnerable")), ctx.draw_cards(1)),
    },
    "shatter_guard": {
        "stats": {"damage": (10, 2), "bonus": (8, 2)},
        "desc": lambda s: f"{s('damage')} урона. +{s('bonus')} если у цели есть блок.",
        "play": lambda s, ctx: ctx.deal_shatter_guard(s("damage"), s("bonus")),
    },
    "arc_slash": {
        "stats": {"damage": (6, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage")),
    },
    "fortify": {
        "stats": {"block": (6, 3)},
        "desc": lambda s: f"Даёт {s('block')} блока.",
        "play": lambda s, ctx: ctx.gain_block(s("block")),
    },
    "deflect": {
        "stats": {"block": (3, 2)},
        "desc": lambda s: f"Даёт {s('block')} блока. Возьми 1 карту.",
        "play": lambda s, ctx: (ctx.gain_block(s("block")), ctx.draw_cards(1)),
    },
    "vital_surge": {
        "stats": {"damage": (5, 2), "heal": (2, 2)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Восстанавливает {s('heal')} HP.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.heal(s("heal"))),
    },
    "double_tap": {
        "stats": {"damage": (3, 1), "hits": (2, 0)},
        "desc": lambda s: f"Наносит {s('damage')} урона дважды.",
        "play": lambda s, ctx: tuple(ctx.deal_damage(s("damage")) for _ in range(s("hits"))),
    },
    "razor_flurry": {
        "stats": {"damage": (4, 1), "hits": (3, 0)},
        "desc": lambda s: f"Наносит {s('damage')} урона {s('hits')} раза.",
        "play": lambda s, ctx: [ctx.deal_damage(s("damage")) for _ in range(s("hits"))],
    },
    "bastion": {
        "stats": {"metallicize": (3, 2)},
        "desc": lambda s: f"В начале хода получай {s('metallicize')} блока.",
        "play": lambda s, ctx: ctx.gain_power("metallicize", s("metallicize")),
    },
    "surge_strike": {
        "stats": {"damage": (7, 2), "bonus": (3, 1)},
        "desc": lambda s: f"Наносит {s('damage')} урона. +{s('bonus')} если у тебя нет блока.",
        "play": lambda s, ctx: ctx.deal_damage(s("damage") + (0 if ctx.player_block() > 0 else s("bonus"))),
    },
    "guard_break": {
        "stats": {"damage": (6, 2), "bonus": (8, 2)},
        "desc": lambda s: f"{s('damage')} урона. +{s('bonus')} если у цели есть блок.",
        "play": lambda s, ctx: ctx.deal_shatter_guard(s("damage"), s("bonus")),
    },
    "focus": {
        "stats": {"draw": (2, 1), "discard": (1, 0)},
        "desc": lambda s: f"Возьми {s('draw')} карты. Сбрось {s('discard')}.",
        "play": lambda s, ctx: (ctx.draw_cards(s("draw")), ctx.discard_random(s("discard"))),
    },
    "marking_shot": {
        "stats": {"damage": (5, 2), "weak": (2, 1)},
        "desc": lambda s: f"Наносит {s('damage')} урона. Накладывает {s('weak')} Слабости.",
        "play": lambda s, ctx: (ctx.deal_damage(s("damage")), ctx.apply_status("weak", s("weak"))),
    },
    "adrenaline_rush": {
        "stats": {"draw": (2, 1), "self_damage": (2, 0)},
        "desc": lambda s: f"Возьми {s('draw')} карты. Теряешь {s('self_damage')} HP.",
        "play": lambda s, ctx: (ctx.draw_cards(s("draw")), ctx.self_damage(s("self_damage"))),
    },
}


def card_upgrade_level(card):
    if card.get("upgrade_level") is not None:
        return max(0, int(card["upgrade_level"]))
    if card.get("upgraded"):
        return 1
    return 0


def _scaling_stat(card_id, key, level):
    base, delta = CARD_SCALING[card_id]["stats"][key]
    return base + delta * level


def scaled_card_desc(card_id, level):
    scaling = CARD_SCALING.get(card_id)
    if not scaling or level <= 0:
        return CARD_DEFS[card_id]["desc"]
    stat = lambda key: _scaling_stat(card_id, key, level)
    return scaling["desc"](stat)


def sync_card_upgrade(card):
    card_id = card["id"]
    if card_id not in CARD_SCALING:
        return
    level = card_upgrade_level(card)
    base_name = CARD_DEFS[card_id]["name"]
    card["upgraded"] = level > 0
    card["upgrade_level"] = level
    if level > 0:
        card["name"] = base_name + ("+" * level if level <= 3 else f"+{level}")
        card["desc"] = scaled_card_desc(card_id, level)
        card["effect"] = CARD_UPGRADES[card_id]["effect"]
    else:
        card["name"] = base_name
        card["desc"] = CARD_DEFS[card_id]["desc"]
        card["effect"] = CARD_DEFS[card_id]["effect"]


def normalize_card(card):
    if card.get("type") == "curse" or card["id"] not in CARD_SCALING:
        return
    if card.get("upgrade_level") is None and card.get("upgraded"):
        card["upgrade_level"] = 1
    sync_card_upgrade(card)


def preview_upgrade(card):
    if card["id"] not in CARD_SCALING:
        return None
    level = card_upgrade_level(card) + 1
    base = CARD_DEFS[card["id"]]
    preview = {**card, "upgrade_level": level, "upgraded": True}
    preview["name"] = base["name"] + ("+" * level if level <= 3 else f"+{level}")
    preview["desc"] = scaled_card_desc(card["id"], level)
    return preview


def upgrade_card(card):
    if card["id"] not in CARD_SCALING:
        return False
    card["upgrade_level"] = card_upgrade_level(card) + 1
    sync_card_upgrade(card)
    return True


def upgradable_cards(deck):
    return [c for c in deck if c["id"] in CARD_SCALING and c.get("type") != "curse"]


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


def unique_upgradable_cards(deck):
    """One representative card per upgradable type (for the forge screen)."""
    seen_ids = set()
    unique = []
    for card in upgradable_cards(deck):
        if card["id"] in seen_ids:
            continue
        seen_ids.add(card["id"])
        unique.append(card)
    return unique


def deck_card_ids(deck):
    return {c["id"] for c in deck if c.get("type") != "curse"}


def can_add_card_to_deck(deck, card_id):
    if card_id in CURSE_IDS:
        return True
    return card_id not in deck_card_ids(deck)


def try_add_card_to_run(run, card_id):
    deck = run.setdefault("deck", [])
    if not can_add_card_to_deck(deck, card_id):
        return False
    deck.append(create_card(card_id))
    return True


def create_card(card_id):
    base = CARD_DEFS.get(card_id, CARD_DEFS["strike"])
    return {"id": card_id, "uid": f"{card_id}_{uuid.uuid4().hex[:8]}", **base}


def starter_deck():
    deck = [create_card("strike") for _ in range(4)]
    deck += [create_card("defend") for _ in range(5)]
    deck.append(create_card("quick_slash"))
    return shuffle(deck)


def roll_card_rewards(count=3, act=0, exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    weights = (
        (0.7, 0.25, 0.05) if act == 0 else
        (0.5, 0.35, 0.15) if act == 1 else
        (0.35, 0.4, 0.25) if act == 2 else
        (0.25, 0.45, 0.30)
    )
    picks = []
    used = set()
    attempts = 0
    while len(picks) < count and attempts < count * 40:
        attempts += 1
        roll = random.random()
        rarity = "common"
        if roll > weights[0] + weights[1]:
            rarity = "rare"
        elif roll > weights[0]:
            rarity = "uncommon"
        pool = [cid for cid in REWARD_POOL[rarity] if cid not in used and cid not in exclude_ids]
        if not pool:
            pool = [cid for cid in REWARD_POOL[rarity] if cid not in used]
        if not pool:
            for alt in ("uncommon", "common", "rare"):
                pool = [cid for cid in REWARD_POOL[alt] if cid not in used and cid not in exclude_ids]
                if pool:
                    break
        if not pool:
            continue
        cid = pick(pool)
        used.add(cid)
        exclude_ids.add(cid)
        picks.append(create_card(cid))
    return picks


def roll_rare_card_reward(exclude_ids=None):
    exclude_ids = set(exclude_ids or [])
    pool = [cid for cid in REWARD_POOL["rare"] if cid not in exclude_ids]
    if not pool:
        pool = list(REWARD_POOL["rare"])
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


def play_scaled_card(card_id, level, ctx):
    scaling = CARD_SCALING[card_id]
    stat = lambda key: _scaling_stat(card_id, key, level)
    scaling["play"](stat, ctx)


def play_card_effect(effect_id, ctx, card=None):
    if card and card["id"] in CARD_SCALING:
        play_scaled_card(card["id"], card_upgrade_level(card), ctx)
        return
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
        "arc_slash": lambda: ctx.deal_damage(6),
        "fortify": lambda: ctx.gain_block(6),
        "deflect": lambda: (ctx.gain_block(3), ctx.draw_cards(1)),
        "vital_surge": lambda: (ctx.deal_damage(5), ctx.heal(2)),
        "double_tap": lambda: (ctx.deal_damage(3), ctx.deal_damage(3)),
        "razor_flurry": lambda: [ctx.deal_damage(4) for _ in range(3)],
        "bastion": lambda: ctx.gain_power("metallicize", 3),
        "curse_doubt": lambda: ctx.discard_random(1),
        "curse_none": lambda: None,
    }
    fn = effects.get(effect_id, effects["strike"])
    fn()
