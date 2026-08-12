import random

from config import pick
from difficulty import apply_map_tier, apply_run_pressure, effective_combats_won, get_difficulty, scale_enemy
from icons import STATUS_NAMES

ENEMY_DEFS = {
    "slime": {"name": "Слизень", "max_hp": 30, "biome": "forest", "color": (78, 205, 196),
              "patterns": [{"intent": "attack", "value": 7}, {"intent": "attack", "value": 9}, {"intent": "buff", "value": 2, "status": "strength"}]},
    "wolf": {"name": "Лесной Волк", "max_hp": 40, "biome": "forest", "color": (138, 150, 170),
             "patterns": [{"intent": "attack", "value": 6}, {"intent": "multi", "value": 4, "hits": 2}, {"intent": "attack", "value": 10}]},
    "scorpion": {"name": "Пустынный Скорпион", "max_hp": 34, "biome": "desert", "color": (196, 154, 58),
                 "patterns": [{"intent": "attack", "value": 8}, {"intent": "debuff", "value": 3, "status": "poison"}, {"intent": "attack", "value": 11}]},
    "sand_colossus": {"name": "Песчаный Колосс", "max_hp": 55, "biome": "desert", "color": (212, 168, 74),
                      "patterns": [{"intent": "block", "value": 10}, {"intent": "attack", "value": 12}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 16}]},
    "frost_slime": {"name": "Морозный Слизень", "max_hp": 36, "biome": "snow", "color": (122, 184, 216),
                    "patterns": [{"intent": "attack", "value": 7}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 9}, {"intent": "block", "value": 9}]},
    "wraith": {"name": "Призрак Руин", "max_hp": 42, "biome": "ruins", "color": (154, 122, 184),
               "patterns": [{"intent": "attack", "value": 9}, {"intent": "steal_block"}, {"intent": "attack", "value": 11}, {"intent": "debuff", "value": 2, "status": "vulnerable"}]},
    "ice_guardian": {"name": "Ледяной Страж", "max_hp": 72, "biome": "snow", "color": (168, 216, 240), "boss": True,
                     "patterns": [{"intent": "block", "value": 15}, {"intent": "attack", "value": 14}, {"intent": "multi", "value": 5, "hits": 2}, {"intent": "debuff", "value": 3, "status": "weak"}, {"intent": "attack", "value": 20}],
                     "enrage_patterns": [{"intent": "multi", "value": 6, "hits": 3}, {"intent": "attack", "value": 24}, {"intent": "debuff", "value": 4, "status": "weak"}, {"intent": "attack", "value": 30}]},
    "blue_boss": {"name": "Синий Повелитель", "max_hp": 65, "biome": "forest", "color": (68, 136, 255), "boss": True,
                  "patterns": [{"intent": "attack", "value": 10}, {"intent": "buff", "value": 3, "status": "strength"}, {"intent": "multi", "value": 4, "hits": 3}, {"intent": "attack", "value": 18}],
                  "enrage_patterns": [{"intent": "multi", "value": 5, "hits": 3}, {"intent": "attack", "value": 22}, {"intent": "buff", "value": 4, "status": "strength"}, {"intent": "attack", "value": 25}]},
    "sand_tyrant": {"name": "Тиран Песков", "max_hp": 80, "biome": "desert", "color": (232, 184, 64), "boss": True,
                   "patterns": [{"intent": "block", "value": 12}, {"intent": "attack", "value": 13}, {"intent": "debuff", "value": 4, "status": "poison"}, {"intent": "attack", "value": 22}, {"intent": "multi", "value": 6, "hits": 2}],
                   "enrage_patterns": [{"intent": "attack", "value": 18}, {"intent": "multi", "value": 7, "hits": 2}, {"intent": "debuff", "value": 5, "status": "poison"}, {"intent": "attack", "value": 28}]},
    "forest_alpha": {"name": "Альфа-Волк", "max_hp": 52, "biome": "forest", "color": (168, 88, 88), "elite": True,
                     "patterns": [{"intent": "multi", "value": 4, "hits": 2}, {"intent": "attack", "value": 12}, {"intent": "buff", "value": 2, "status": "strength"}, {"intent": "multi", "value": 5, "hits": 2}]},
    "dune_stalker": {"name": "Охотник Дюн", "max_hp": 48, "biome": "desert", "color": (210, 140, 48), "elite": True,
                     "patterns": [{"intent": "debuff", "value": 4, "status": "poison"}, {"intent": "attack", "value": 11}, {"intent": "multi", "value": 4, "hits": 2}, {"intent": "attack", "value": 14}]},
    "frost_wraith": {"name": "Морозный Призрак", "max_hp": 50, "biome": "snow", "color": (140, 190, 230), "elite": True,
                     "patterns": [{"intent": "debuff", "value": 3, "status": "weak"}, {"intent": "attack", "value": 10}, {"intent": "steal_block"}, {"intent": "attack", "value": 14}, {"intent": "debuff", "value": 2, "status": "vulnerable"}]},
    "thorn_brute": {"name": "Шипастый Зверь", "max_hp": 46, "biome": "forest", "color": (180, 100, 90),
                    "patterns": [{"intent": "attack", "value": 9}, {"intent": "attack", "value": 12}, {"intent": "debuff", "value": 2, "status": "vulnerable"}, {"intent": "multi", "value": 5, "hits": 2}]},
    "crystal_scorpion": {"name": "Кристальный Скорпион", "max_hp": 42, "biome": "desert", "color": (220, 180, 80),
                         "patterns": [{"intent": "debuff", "value": 4, "status": "poison"}, {"intent": "attack", "value": 11}, {"intent": "block", "value": 9}, {"intent": "attack", "value": 14}]},
    "blizzard_hound": {"name": "Метельный Пес", "max_hp": 44, "biome": "snow", "color": (150, 200, 230),
                       "patterns": [{"intent": "multi", "value": 4, "hits": 2}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 12}, {"intent": "attack", "value": 15}]},
    "border_hunter": {"name": "Охотник Рубежа", "max_hp": 62, "biome": "ruins", "color": (200, 60, 80), "hunter": True,
                      "patterns": [{"intent": "attack", "value": 13}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "multi", "value": 6, "hits": 2}, {"intent": "attack", "value": 17}, {"intent": "buff", "value": 2, "status": "strength"}]},
    "void_shade": {"name": "Тень Пустоты", "max_hp": 40, "biome": "ruins", "color": (120, 80, 160),
                   "patterns": [{"intent": "attack", "value": 8}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 10}, {"intent": "steal_block"}]},
    "ruin_sentinel": {"name": "Страж Руин", "max_hp": 54, "biome": "ruins", "color": (160, 100, 200), "elite": True,
                      "patterns": [{"intent": "block", "value": 11}, {"intent": "attack", "value": 11}, {"intent": "debuff", "value": 2, "status": "vulnerable"}, {"intent": "multi", "value": 5, "hits": 2}, {"intent": "steal_block"}]},
    "void_sovereign": {"name": "Владыка Пустоты", "max_hp": 88, "biome": "ruins", "color": (180, 70, 220), "boss": True,
                       "patterns": [{"intent": "attack", "value": 12}, {"intent": "debuff", "value": 3, "status": "weak"}, {"intent": "multi", "value": 5, "hits": 2}, {"intent": "steal_block"}, {"intent": "attack", "value": 20}],
                       "enrage_patterns": [{"intent": "multi", "value": 6, "hits": 3}, {"intent": "debuff", "value": 4, "status": "vulnerable"}, {"intent": "attack", "value": 24}, {"intent": "steal_block"}, {"intent": "attack", "value": 28}]},
    "void_lurker": {"name": "Люркер Пустоты", "max_hp": 38, "biome": "ruins", "color": (130, 85, 170),
                   "patterns": [{"intent": "steal_block"}, {"intent": "attack", "value": 9}, {"intent": "attack", "value": 11}, {"intent": "multi", "value": 4, "hits": 2}]},
    "curse_weaver": {"name": "Ткач Проклятий", "max_hp": 44, "biome": "ruins", "color": (170, 90, 150),
                     "patterns": [{"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 10}, {"intent": "debuff", "value": 3, "status": "vulnerable"}, {"intent": "multi", "value": 5, "hits": 2}]},
    "rift_stalker": {"name": "Следопыт Разлома", "max_hp": 46, "biome": "snow", "color": (130, 175, 220),
                     "patterns": [{"intent": "steal_block"}, {"intent": "attack", "value": 10}, {"intent": "multi", "value": 4, "hits": 2}, {"intent": "debuff", "value": 2, "status": "weak"}]},
    "moss_colossus": {"name": "Мховый Колосс", "max_hp": 52, "biome": "forest", "color": (72, 140, 88),
                      "patterns": [{"intent": "block", "value": 9}, {"intent": "attack", "value": 11}, {"intent": "debuff", "value": 2, "status": "vulnerable"}, {"intent": "attack", "value": 14}]},
    "void_binder": {"name": "Связующий Пустоты", "max_hp": 42, "biome": "ruins", "color": (145, 85, 175),
                    "patterns": [{"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "steal_block"}, {"intent": "curse", "curse_id": "curse_doubt"}, {"intent": "attack", "value": 10}]},
    "spore_shaman": {"name": "Споровый Шаман", "max_hp": 40, "biome": "forest", "color": (90, 170, 80),
                     "patterns": [{"intent": "debuff", "value": 3, "status": "poison"}, {"intent": "attack", "value": 9}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 12}]},
    "mirror_shade": {"name": "Зеркальная Тень", "max_hp": 44, "biome": "ruins", "color": (170, 150, 220),
                     "patterns": [{"intent": "steal_block"}, {"intent": "debuff", "value": 2, "status": "vulnerable"}, {"intent": "attack", "value": 10}, {"intent": "multi", "value": 4, "hits": 2}]},
    "sand_viper": {"name": "Песчаный Аспид", "max_hp": 36, "biome": "desert", "color": (200, 130, 50),
                   "patterns": [{"intent": "debuff", "value": 3, "status": "poison"}, {"intent": "attack", "value": 9}, {"intent": "attack", "value": 11}]},
    "frost_lynx": {"name": "Морозная Рысь", "max_hp": 40, "biome": "snow", "color": (140, 195, 235),
                   "patterns": [{"intent": "multi", "value": 3, "hits": 2}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "attack", "value": 12}]},
    "briar_stalker": {"name": "Шипастый Следопыт", "max_hp": 42, "biome": "forest", "color": (100, 160, 80),
                      "patterns": [{"intent": "attack", "value": 8}, {"intent": "debuff", "value": 2, "status": "vulnerable"}, {"intent": "multi", "value": 4, "hits": 2}]},
    "void_maw": {"name": "Пасть Пустоты", "max_hp": 46, "biome": "void", "color": (120, 70, 160),
                 "patterns": [{"intent": "attack", "value": 10}, {"intent": "steal_block"}, {"intent": "multi", "value": 5, "hits": 2}]},
    "crimson_hunter": {"name": "Багровый Охотник", "max_hp": 58, "biome": "ruins", "color": (220, 50, 70), "hunter": True,
                       "patterns": [{"intent": "attack", "value": 12}, {"intent": "debuff", "value": 2, "status": "weak"}, {"intent": "multi", "value": 5, "hits": 2}, {"intent": "attack", "value": 16}]},
    "abyss_watcher": {"name": "Страж Бездны", "max_hp": 50, "biome": "void", "color": (130, 80, 190),
                      "patterns": [{"intent": "block", "value": 10}, {"intent": "debuff", "value": 3, "status": "vulnerable"}, {"intent": "attack", "value": 13}, {"intent": "steal_block"}]},
    "void_heart": {"name": "Сердце Пустоты", "max_hp": 95, "biome": "void", "color": (200, 60, 240), "boss": True,
                   "patterns": [{"intent": "attack", "value": 14}, {"intent": "multi", "value": 6, "hits": 2}, {"intent": "debuff", "value": 3, "status": "weak"}, {"intent": "steal_block"}, {"intent": "attack", "value": 22}],
                   "enrage_patterns": [{"intent": "multi", "value": 7, "hits": 3}, {"intent": "attack", "value": 26}, {"intent": "debuff", "value": 4, "status": "vulnerable"}, {"intent": "attack", "value": 32}],
                   "phases": [
                       {"threshold": 0.66, "msg": "Пустота пульсирует сильнее!", "patterns": [{"intent": "multi", "value": 5, "hits": 2}, {"intent": "attack", "value": 18}, {"intent": "debuff", "value": 3, "status": "vulnerable"}, {"intent": "attack", "value": 20}]},
                       {"threshold": 0.33, "msg": "Сердце раскрывается — финальный удар!", "patterns": [{"intent": "multi", "value": 7, "hits": 3}, {"intent": "attack", "value": 26}, {"intent": "steal_block"}, {"intent": "attack", "value": 32}]},
                   ]},
}

BIOME_ENEMIES = {
    "forest": ["slime", "wolf", "spore_shaman", "briar_stalker"],
    "desert": ["scorpion", "sand_viper"],
    "snow": ["frost_slime", "frost_lynx"],
    "ruins": ["wraith", "void_shade", "void_lurker", "void_binder", "mirror_shade"],
    "void": ["void_maw", "void_shade", "abyss_watcher"],
}
BIOME_ENEMIES_HARD = {
    "forest": ["thorn_brute", "wolf", "moss_colossus", "spore_shaman", "briar_stalker"],
    "desert": ["crystal_scorpion", "scorpion", "sand_colossus", "sand_viper"],
    "snow": ["blizzard_hound", "frost_slime", "rift_stalker", "frost_lynx"],
    "ruins": ["void_lurker", "curse_weaver", "wraith", "void_binder", "mirror_shade"],
    "void": ["void_maw", "curse_weaver", "abyss_watcher", "void_lurker"],
}
ELITE_POOLS = {
    "forest": ["forest_alpha", "thorn_brute"],
    "desert": ["dune_stalker", "crystal_scorpion"],
    "snow": ["frost_wraith", "blizzard_hound"],
    "ruins": ["ruin_sentinel", "wraith", "curse_weaver"],
    "void": ["ruin_sentinel", "abyss_watcher"],
}
ELITE_BY_BIOME = {"forest": "forest_alpha", "desert": "dune_stalker", "snow": "frost_wraith", "ruins": "ruin_sentinel", "void": "abyss_watcher"}
BOSS_BY_ACT = ["blue_boss", "sand_tyrant", "ice_guardian", "void_sovereign", "void_heart"]


def check_boss_enrage(combat, enemy):
    if enemy["hp"] <= 0 or not enemy.get("boss"):
        return
    phases = enemy.get("phases")
    if phases:
        phase_idx = enemy.get("phase", 0)
        while phase_idx < len(phases) and enemy["hp"] <= enemy["max_hp"] * phases[phase_idx]["threshold"]:
            phase = phases[phase_idx]
            enemy["patterns"] = list(phase["patterns"])
            enemy["pattern_index"] = 0
            enemy["intent"] = get_intent(enemy)
            combat.log(f"⚠ {enemy['name']}: {phase.get('msg', 'новая фаза!')}")
            phase_idx += 1
            enemy["phase"] = phase_idx
            enemy["enraged"] = phase_idx > 0
        return
    if enemy.get("enraged"):
        return
    if enemy["hp"] > enemy["max_hp"] * 0.5:
        return
    patterns = enemy.get("enrage_patterns")
    if not patterns:
        return
    enemy["enraged"] = True
    enemy["patterns"] = list(patterns)
    enemy["pattern_index"] = 0
    enemy["intent"] = get_intent(enemy)
    combat.log(f"⚠ {enemy['name']} впадает в ярость!")
    if enemy.get("id") == "void_sovereign":
        from cards import create_card
        combat.discard.append(create_card("curse_wound"))
        combat.log("⚠ Владыка вплетает проклятие в колоду!")


def create_enemy(enemy_id):
    d = ENEMY_DEFS.get(enemy_id, ENEMY_DEFS["slime"])
    return {
        "id": enemy_id,
        "name": d["name"],
        "max_hp": d["max_hp"],
        "hp": d["max_hp"],
        "block": 0,
        "biome": d["biome"],
        "color": d["color"],
        "patterns": list(d["patterns"]),
        "enrage_patterns": list(d.get("enrage_patterns", [])),
        "pattern_index": 0,
        "statuses": {},
        "powers": {},
        "intent": None,
        "boss": d.get("boss", False),
        "elite": d.get("elite", False),
        "hunter": d.get("hunter", False),
        "enraged": False,
        "phase": 0,
        "affix": None,
    }


def _battle_pool(biome, act):
    base = BIOME_ENEMIES.get(biome, BIOME_ENEMIES["forest"])
    hard = BIOME_ENEMIES_HARD.get(biome, base)
    if act >= 2:
        return hard
    if act == 1:
        return base + hard
    return base


def _finalize_enemy(enemy, act, elite=False, boss=False, combats_won=0, mutators=None, map_tier="hard", ascension=0):
    won = effective_combats_won(combats_won, map_tier)
    scale_enemy(enemy, act, elite=elite, boss=boss, ascension=ascension)
    apply_run_pressure(enemy, won)
    apply_map_tier(enemy, map_tier)
    hp_bonus = 0.0
    if mutators:
        from mutators import enemy_hp_bonus
        hp_bonus = enemy_hp_bonus(mutators)
    if hp_bonus > 0:
        enemy["max_hp"] = max(1, int(enemy["max_hp"] * (1 + hp_bonus)))
        enemy["hp"] = enemy["max_hp"]
    return enemy


def roll_battle_enemies(biome, elite=False, act=0, combats_won=0, mutators=None, map_tier="hard", ascension=0):
    if elite:
        pool = ELITE_POOLS.get(biome, ELITE_POOLS["forest"])
        e = create_enemy(pick(pool))
        enemies = [_finalize_enemy(e, act, elite=True, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension)]
        affix = roll_elite_affix()
        if affix:
            apply_affix(enemies[0], affix)
        minion_chance = 0.0 if map_tier in ("easy", "split") else (1.0 if mutators and "elite_swarm" in mutators else 0.40)
        if random.random() < minion_chance:
            minion = create_enemy(pick(_battle_pool(biome, act)))
            minion["name"] = f"{minion['name']} (соратник)"
            _finalize_enemy(minion, act, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension)
            minion["max_hp"] = max(12, int(minion["max_hp"] * 0.58))
            minion["hp"] = minion["max_hp"]
            enemies.append(minion)
        return enemies
    if map_tier != "hard":
        pool = BIOME_ENEMIES.get(biome, BIOME_ENEMIES["forest"])
        double_chance = 0.0 if map_tier == "easy" else 0.12
        count = 2 if random.random() < double_chance else 1
        return [
            _finalize_enemy(create_enemy(pick(pool)), act, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension)
            for _ in range(count)
        ]
    hunter_chance = get_difficulty().get("hunter_chance", 0.0)
    if mutators:
        from mutators import hunter_bonus
        hunter_chance += hunter_bonus(mutators)
    if ascension:
        from ascension import ascension_hunter_bonus
        hunter_chance += ascension_hunter_bonus(ascension)
    if act >= 1 and random.random() < hunter_chance + act * 0.02:
        hunter_id = "crimson_hunter" if random.random() < 0.35 else "border_hunter"
        e = create_enemy(hunter_id)
        enemies = [_finalize_enemy(e, act, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension)]
        if random.random() < 0.32:
            minion = create_enemy(pick(_battle_pool(biome, act)))
            minion["name"] = f"{minion['name']} (приставка)"
            _finalize_enemy(minion, act, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension)
            minion["max_hp"] = max(10, int(minion["max_hp"] * 0.5))
            minion["hp"] = minion["max_hp"]
            enemies.append(minion)
        return enemies
    pool = _battle_pool(biome, act)
    double_chance = get_difficulty()["double_enemy_chance"]
    if act >= 3:
        double_chance += 0.14
    if mutators:
        from mutators import double_spawn_bonus
        double_chance += double_spawn_bonus(mutators)
    count = 2 if random.random() < double_chance else 1
    return [_finalize_enemy(create_enemy(pick(pool)), act, combats_won=combats_won, mutators=mutators, map_tier=map_tier, ascension=ascension) for _ in range(count)]


def roll_ambush_enemies(biome, act=0, combats_won=0, mutators=None, ascension=0):
    pool = _battle_pool(biome, act)
    count = 2 if random.random() < 0.45 else 1
    enemies = []
    for _ in range(count):
        e = create_enemy(pick(pool))
        _finalize_enemy(e, act, combats_won=combats_won, mutators=mutators, ascension=ascension)
        e["max_hp"] = max(10, int(e["max_hp"] * 0.72))
        e["hp"] = e["max_hp"]
        e["name"] = f"{e['name']} (засада)"
        enemies.append(e)
    return enemies


def roll_hunter_fight(act=0, combats_won=0, mutators=None, ascension=0):
    hunter_id = "crimson_hunter" if random.random() < 0.4 else "border_hunter"
    e = create_enemy(hunter_id)
    _finalize_enemy(e, act, combats_won=combats_won, mutators=mutators, ascension=ascension)
    return [e]


def roll_boss(act, combats_won=0, mutators=None, ascension=0):
    e = create_enemy(BOSS_BY_ACT[act] if act < len(BOSS_BY_ACT) else BOSS_BY_ACT[0])
    return [_finalize_enemy(e, act, boss=True, combats_won=combats_won, mutators=mutators, ascension=ascension)]


def get_intent(enemy):
    return dict(enemy["patterns"][enemy["pattern_index"] % len(enemy["patterns"])])


def get_next_intent(enemy):
    patterns = enemy.get("patterns") or []
    if len(patterns) < 2:
        return None
    nxt = (enemy["pattern_index"] + 1) % len(patterns)
    return dict(patterns[nxt])


def advance_pattern(enemy):
    enemy["pattern_index"] = (enemy["pattern_index"] + 1) % len(enemy["patterns"])


def intent_label(intent):
    kind = intent.get("intent")
    if kind == "attack":
        return f"Атака {intent['value']}"
    if kind == "multi":
        return f"Атака {intent['value']}x{intent['hits']}"
    if kind == "block":
        return f"Блок {intent['value']}"
    if kind == "buff":
        return f"Сила +{intent['value']}"
    if kind == "debuff":
        st = intent.get("status", "")
        return f"{STATUS_NAMES.get(st, st)} {intent['value']}"
    if kind == "steal_block":
        return "Кража блока"
    if kind == "curse":
        return "Проклятие"
    return "?"


def intent_color(intent):
    kind = intent.get("intent")
    if kind in ("attack", "multi"):
        return (255, 92, 92)
    if kind == "block":
        return (111, 168, 255)
    if kind == "buff":
        return (255, 179, 71)
    if kind in ("debuff", "steal_block", "curse"):
        return (199, 125, 255)
    return (138, 150, 170)


def add_status(target, key, amount):
    target["statuses"][key] = target["statuses"].get(key, 0) + amount


def get_status(target, key):
    return target["statuses"].get(key, 0)


def tick_statuses(target):
    total = 0
    poison = target["statuses"].get("poison", 0)
    if poison > 0:
        target["hp"] -= poison
        target["statuses"]["poison"] = max(0, poison - 1)
        total += poison
    burn = target["statuses"].get("burn", 0)
    if burn > 0:
        target["hp"] -= burn
        target["statuses"]["burn"] = max(0, burn - 1)
        total += burn
    return total


def tick_poison(target):
    poison = target["statuses"].get("poison", 0)
    if poison > 0:
        target["hp"] -= poison
        target["statuses"]["poison"] = max(0, poison - 1)
        return poison
    return 0


def tick_burn(target):
    burn = target["statuses"].get("burn", 0)
    if burn > 0:
        target["hp"] -= burn
        target["statuses"]["burn"] = max(0, burn - 1)
        return burn
    return 0


AFFIX_DEFS = {
    "armored": {"name": "Бронированный", "desc": "+28% HP", "hp_mult": 1.28},
    "vampiric": {"name": "Вампир", "desc": "Лечится при атаке", "heal_on_attack": 4},
    "thorns": {"name": "Шипастый", "desc": "2 урона при ударе", "thorns": 2},
    "regenerating": {"name": "Регенератор", "desc": "+4 HP каждый ход", "regen": 4},
}


def affix_label(affix_id):
    return AFFIX_DEFS.get(affix_id, {}).get("name", affix_id)


def roll_elite_affix():
    import random
    if random.random() > 0.72:
        return None
    return pick(list(AFFIX_DEFS.keys()))


def apply_affix(enemy, affix_id):
    if not affix_id:
        return
    info = AFFIX_DEFS.get(affix_id, {})
    enemy["affix"] = affix_id
    hp_mult = info.get("hp_mult", 1.0)
    if hp_mult != 1.0:
        enemy["max_hp"] = max(1, int(enemy["max_hp"] * hp_mult))
        enemy["hp"] = enemy["max_hp"]
    label = info.get("name", affix_id)
    enemy["name"] = f"{enemy['name']} ({label})"


def decay_statuses(target):
    for key in ("weak", "vulnerable"):
        if target["statuses"].get(key, 0) > 0:
            target["statuses"][key] -= 1


def scaled_damage(base, attacker, defender):
    dmg = base
    dmg += attacker.get("statuses", {}).get("strength", 0)
    if get_status(attacker, "weak") > 0:
        dmg = int(dmg * 0.75)
    if get_status(defender, "vulnerable") > 0:
        dmg = int(dmg * 1.5)
    return max(0, dmg)


def apply_block_damage(target, amount, pierce=False):
    remaining = amount
    if not pierce and target.get("block", 0) > 0:
        absorbed = min(target["block"], remaining)
        target["block"] -= absorbed
        remaining -= absorbed
    target["hp"] -= remaining
    return remaining
