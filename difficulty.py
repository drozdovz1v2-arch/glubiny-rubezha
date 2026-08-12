"""Настройки сложности и масштабирование."""

DIFFICULTIES = {
    "border": {
        "id": "border",
        "name": "Рубеж",
        "player_hp": 70,
        "player_max_hp": 70,
        "starting_gold": 85,
        "cards_per_turn": 5,
        "base_energy": 3,
        "rest_heal": 14,
        "rest_heal_pct": 0.22,
        "enemy_hp_mult": 1.22,
        "enemy_dmg_mult": 1.18,
        "elite_hp_mult": 1.42,
        "boss_hp_mult": 1.32,
        "boss_dmg_mult": 1.22,
        "act_scaling": 0.10,
        "double_enemy_chance": 0.38,
        "elite_node_chance": 0.18,
        "rest_node_chance": 0.14,
        "shop_node_chance": 0.12,
        "shop_price_mult": 1.1,
        "gold_reward_mult": 1.0,
        "event_heal_mult": 0.85,
        "pressure_turn": 5,
        "hunter_chance": 0.06,
        "desc": "70 HP, 5 карт за ход. Слабее враги, больше золота и привалов. Давление с 5-го хода.",
    },
    "harsh": {
        "id": "harsh",
        "name": "Суровый Рубеж",
        "player_hp": 58,
        "player_max_hp": 58,
        "starting_gold": 70,
        "cards_per_turn": 4,
        "base_energy": 3,
        "rest_heal": 12,
        "rest_heal_pct": 0.18,
        "enemy_hp_mult": 1.42,
        "enemy_dmg_mult": 1.32,
        "elite_hp_mult": 1.58,
        "boss_hp_mult": 1.48,
        "boss_dmg_mult": 1.38,
        "act_scaling": 0.14,
        "double_enemy_chance": 0.52,
        "elite_node_chance": 0.24,
        "rest_node_chance": 0.12,
        "shop_node_chance": 0.10,
        "shop_price_mult": 1.25,
        "gold_reward_mult": 0.85,
        "event_heal_mult": 0.7,
        "pressure_turn": 5,
        "hunter_chance": 0.10,
        "desc": "58 HP, 4 карты. Сбалансированный вызов: чаще элиты и двойные бои. Давление с 5-го хода.",
    },
    "nightmare": {
        "id": "nightmare",
        "name": "Кошмар",
        "player_hp": 48,
        "player_max_hp": 48,
        "starting_gold": 55,
        "cards_per_turn": 4,
        "base_energy": 3,
        "rest_heal": 10,
        "rest_heal_pct": 0.15,
        "enemy_hp_mult": 1.58,
        "enemy_dmg_mult": 1.48,
        "elite_hp_mult": 1.72,
        "boss_hp_mult": 1.62,
        "boss_dmg_mult": 1.48,
        "act_scaling": 0.16,
        "double_enemy_chance": 0.58,
        "elite_node_chance": 0.28,
        "rest_node_chance": 0.10,
        "shop_node_chance": 0.08,
        "shop_price_mult": 1.35,
        "gold_reward_mult": 0.9,
        "event_heal_mult": 0.6,
        "pressure_turn": 4,
        "hunter_chance": 0.14,
        "desc": "48 HP, 4 карты. Жёсткие враги, мало привалов и лавок. Давление с 4-го хода.",
    },
}

DEFAULT_DIFFICULTY = "harsh"
_current = DIFFICULTIES[DEFAULT_DIFFICULTY]


def get_difficulty():
    return _current


def difficulty_desc(diff_id=None):
    if diff_id:
        return DIFFICULTIES.get(diff_id, _current).get("desc", "")
    return _current.get("desc", "")


def set_difficulty(diff_id):
    global _current
    _current = DIFFICULTIES.get(diff_id, DIFFICULTIES[DEFAULT_DIFFICULTY])


def init_difficulty(meta):
    set_difficulty(meta.get("difficulty", DEFAULT_DIFFICULTY))


def cycle_difficulty(meta):
    ids = list(DIFFICULTIES.keys())
    cur = meta.get("difficulty", DEFAULT_DIFFICULTY)
    nxt = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else ids[0]
    meta["difficulty"] = nxt
    set_difficulty(nxt)
    return _current


# Обратная совместимость
DIFFICULTY = _current


def scale_enemy(enemy, act=0, elite=False, boss=False, ascension=0):
    d = get_difficulty()
    hp_mult = d["enemy_hp_mult"] + act * d["act_scaling"]
    dmg_mult = d["enemy_dmg_mult"] + act * 0.08
    if ascension:
        from ascension import ascension_enemy_dmg_mult, ascension_enemy_hp_mult
        hp_mult *= ascension_enemy_hp_mult(ascension)
        dmg_mult *= ascension_enemy_dmg_mult(ascension)
    if elite:
        hp_mult *= d["elite_hp_mult"] / d["enemy_hp_mult"]
    if boss:
        hp_mult *= d["boss_hp_mult"] / d["enemy_hp_mult"]
        dmg_mult *= d["boss_dmg_mult"] / d["enemy_dmg_mult"]

    enemy["max_hp"] = int(enemy["max_hp"] * hp_mult)
    enemy["hp"] = enemy["max_hp"]

    scaled_patterns = []
    for p in enemy["patterns"]:
        np = dict(p)
        if np.get("intent") in ("attack", "multi", "block", "buff", "debuff") and "value" in np:
            np["value"] = max(1, int(np["value"] * dmg_mult))
        if np.get("intent") == "steal_block":
            np["bonus_dmg"] = max(5, int(5 * dmg_mult))
        scaled_patterns.append(np)
    enemy["patterns"] = scaled_patterns
    if enemy.get("enrage_patterns"):
        scaled_enrage = []
        for p in enemy["enrage_patterns"]:
            np = dict(p)
            if np.get("intent") in ("attack", "multi", "block", "buff", "debuff") and "value" in np:
                np["value"] = max(1, int(np["value"] * dmg_mult))
            if np.get("intent") == "steal_block":
                np["bonus_dmg"] = max(5, int(5 * dmg_mult))
            scaled_enrage.append(np)
        enemy["enrage_patterns"] = scaled_enrage
    return enemy


def apply_run_pressure(enemy, combats_won=0):
    """Чем дальше забег — тем опаснее враги."""
    hp_bonus = min(combats_won * 0.032, 0.42)
    dmg_bonus = min(combats_won * 0.020, 0.30)
    if hp_bonus <= 0 and dmg_bonus <= 0:
        return enemy
    enemy["max_hp"] = max(1, int(enemy["max_hp"] * (1 + hp_bonus)))
    enemy["hp"] = enemy["max_hp"]
    for key in ("patterns", "enrage_patterns"):
        if not enemy.get(key):
            continue
        scaled = []
        for p in enemy[key]:
            np = dict(p)
            if np.get("intent") in ("attack", "multi", "block", "buff", "debuff") and "value" in np:
                np["value"] = max(1, int(np["value"] * (1 + dmg_bonus)))
            if np.get("intent") == "steal_block":
                np["bonus_dmg"] = max(5, int(np.get("bonus_dmg", 7) * (1 + dmg_bonus)))
            scaled.append(np)
        enemy[key] = scaled
    return enemy


def pressure_tier(combats_won):
    if combats_won >= 14:
        return "Критическое", COLORS_PRESSURE["critical"]
    if combats_won >= 9:
        return "Высокое", COLORS_PRESSURE["high"]
    if combats_won >= 4:
        return "Растущее", COLORS_PRESSURE["medium"]
    return "Спокойное", COLORS_PRESSURE["low"]


COLORS_PRESSURE = {
    "low": (128, 140, 162),
    "medium": (255, 176, 72),
    "high": (255, 120, 88),
    "critical": (255, 72, 72),
}


def effective_combats_won(combats_won, map_tier="hard"):
    if map_tier == "easy":
        return max(0, combats_won - 3)
    if map_tier == "split":
        return max(0, combats_won - 1)
    return combats_won


def apply_map_tier(enemy, map_tier="hard"):
    if map_tier == "easy":
        hp_m, dmg_m = 0.72, 0.78
    elif map_tier == "split":
        hp_m, dmg_m = 0.88, 0.90
    else:
        return enemy
    enemy["max_hp"] = max(6, int(enemy["max_hp"] * hp_m))
    enemy["hp"] = enemy["max_hp"]
    for key in ("patterns", "enrage_patterns"):
        if not enemy.get(key):
            continue
        scaled = []
        for p in enemy[key]:
            np = dict(p)
            if np.get("intent") in ("attack", "multi", "block", "buff", "debuff") and "value" in np:
                np["value"] = max(1, int(np["value"] * dmg_m))
            if np.get("intent") == "steal_block":
                np["bonus_dmg"] = max(4, int(np.get("bonus_dmg", 7) * dmg_m))
            scaled.append(np)
        enemy[key] = scaled
    return enemy


def node_threat_label(node_type, act=0, combats_won=0, map_tier="hard"):
    tier_labels = {
        "easy": {"battle": "Лёгкая", "elite": "Опасная"},
        "split": {"battle": "Умеренная", "elite": "Опасная"},
        "hard": {"battle": "Умеренная", "elite": "Опасная"},
    }
    labels = {
        "battle": tier_labels.get(map_tier, tier_labels["hard"])["battle"],
        "elite": "Опасная",
        "boss": "Смертельная",
        "hunter": "Экстремальная · охотник",
        "rest": "Безопасно",
        "shop": "Безопасно",
        "event": "Неизвестно",
    }
    base = labels.get(node_type, "?")
    if node_type in ("battle", "elite", "boss"):
        if map_tier == "easy":
            base += " · разминка"
        elif map_tier == "split":
            base += " · развилка"
        elif act >= 3:
            base += " · акт IV"
        elif act >= 2:
            base += " · акт III"
        elif act >= 1:
            base += " · акт II"
        if map_tier == "hard" and combats_won >= 8 and node_type == "battle":
            base += " · усилены"
    return base


def gold_reward(node_type):
    d = get_difficulty()
    base = {"battle": 18, "elite": 38, "boss": 85, "hunter": 55}.get(node_type, 18)
    return max(8, int(base * d["gold_reward_mult"]))


def shop_price(base_price):
    return int(base_price * get_difficulty()["shop_price_mult"])
