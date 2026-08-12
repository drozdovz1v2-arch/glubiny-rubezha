import random

from cards import create_card, add_curse_to_run, try_add_card_to_run
from potions import POTION_DEFS, add_potion, can_add_potion
from config import ACTS, NODE_TYPES, pick, rand_int
import config
from difficulty import get_difficulty
from relics import grant_random_relic

def _alchemist_buy(run):
    if run["gold"] < 40 or not can_add_potion(run):
        return None
    run["gold"] -= 40
    add_potion(run, pick(list(POTION_DEFS.keys())))


def _sand_tomb_open(run):
    from potions import add_potion, can_add_potion, roll_rest_potion
    if run["hp"] <= 10 or not can_add_potion(run):
        return None
    run["hp"] -= 10
    add_potion(run, roll_rest_potion())


def _shadow_deal(run):
    grant_random_relic(run)
    add_curse_to_run(run)


EVENTS = [
    {
        "id": "campfire",
        "title": "Заброшенный Костёр",
        "text": "Тёплый огонь манит отдохнуть. Восстановить HP или обыскать остатки лагеря?",
        "choices": [
            ("Отдохнуть (+10 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + int(10 * get_difficulty()["event_heal_mult"]))}), "Восстановить HP"),
            ("Обыскать (+35 золота)", lambda run: run.update({"gold": run["gold"] + 35}), "+35 золота"),
        ],
    },
    {
        "id": "ruins",
        "title": "Шепчущие Руины",
        "text": "Древние камни шепчут секреты. Рискнуть и получить редкую карту, но потерять 8 HP?",
        "choices": [
            ("Слушать шёпот", lambda run: run.update({"hp": run["hp"] - 8, "pending_event_reward": "rare"}), "−8 HP · редкая карта"),
            ("Уйти", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "smith",
        "title": "Странствующий Кузнец",
        "text": "Кузнец протягивает артефакт — странная энергия Рубежа отзывается в твоих руках.",
        "choices": [
            ("Взять артефакт", lambda run: grant_random_relic(run), "Случайная реликвия"),
            ("Отказаться", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "fog",
        "title": "Туман Рубежа",
        "text": "Густой туман окутывает тропу. Через него можно найти силу — или золото.",
        "choices": [
            ("Идти дальше (+1 энергия)", lambda run: run.update({"bonus_energy": run.get("bonus_energy", 0) + 1}), "+1 энергия в боях"),
            ("Вернуться (+20 золота)", lambda run: run.update({"gold": run["gold"] + 20}), "+20 золота"),
        ],
    },
    {
        "id": "ancient_tree",
        "biome": "forest",
        "title": "Древо Рубежа",
        "text": "Древнее дерево сияет спорами. Выпить сок или взять семя силы?",
        "choices": [
            ("Выпить сок (+12 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + 12)}), "+12 HP"),
            ("Взять семя", lambda run: try_add_card_to_run(run, "crushing_mark"), "Карта «Сокрушающая Метка»"),
        ],
    },
    {
        "id": "mirage",
        "biome": "desert",
        "title": "Пустынное Зеркало",
        "text": "Мираж показывает сокровища. Рискнуть золотом или пройти мимо?",
        "choices": [
            ("Рискнуть (−15 зол., +45)", lambda run: run.update({"gold": run["gold"] + 30}) if run["gold"] >= 15 else None, "−15 зол., +45 при успехе"),
            ("Обойти (+18 золота)", lambda run: run.update({"gold": run["gold"] + 18}), "+18 золота"),
        ],
    },
    {
        "id": "frozen_shrine",
        "biome": "snow",
        "title": "Ледяной Алтарь",
        "text": "Алтарь покрыт инеем. Принять дар стойкости или согреться?",
        "choices": [
            ("Принять дар (+6 max HP)", lambda run: run.update({"max_hp": run["max_hp"] + 6, "hp": run["hp"] + 6}), "+6 max HP"),
            ("Согреться (+14 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + 14)}), "+14 HP"),
        ],
    },
    {
        "id": "wandering_healer",
        "title": "Странник-Целитель",
        "text": "Целитель предлагает помощь за скромную плату.",
        "choices": [
            ("Лечение (−20 зол., +18 HP)", lambda run: run.update({"gold": run["gold"] - 20, "hp": min(run["max_hp"], run["hp"] + 18)}) if run["gold"] >= 20 else None, "−20 зол., +18 HP"),
            ("Отказаться", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "ambush",
        "title": "Засада Рубежа",
        "text": "Из тумана выскакивают тени. Сражаться, бежать или обмануть их?",
        "choices": [
            ("Сражаться", lambda run: run.update({"pending_ambush": True}), "Ослабленные враги"),
            ("Бежать (−8 HP)", lambda run: run.update({"hp": max(1, run["hp"] - 8)}), "−8 HP"),
            ("Обмануть (+25 золота)", lambda run: run.update({"gold": run["gold"] + 25}), "+25 золота"),
        ],
    },
    {
        "id": "dark_pact",
        "title": "Тёмный Пакт",
        "text": "Тень предлагает золото — цена проклятие в колоде.",
        "choices": [
            ("Принять (+55 зол., проклятие)", lambda run: (add_curse_to_run(run), run.update({"gold": run["gold"] + 55})), "+55 зол., проклятие"),
            ("Отказаться", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "cursed_shrine",
        "title": "Проклятый Алтарь",
        "text": "Алтарь сияет силой, но метка проклятия уже на твоей руке.",
        "choices": [
            ("Принять дар (проклятие, редкая карта)", lambda run: (add_curse_to_run(run), run.update({"pending_event_reward": "rare"})), "Проклятие · редкая карта"),
            ("Разрушить (+30 золота)", lambda run: run.update({"gold": run["gold"] + 30}), "+30 золота"),
        ],
    },
    {
        "id": "alchemist",
        "title": "Алхимик Рубежа",
        "text": "Странник варит настои из тумана. Купить зелье или обменять рецепт на золото?",
        "choices": [
            ("Купить настой (−40 зол.)", _alchemist_buy, "−40 зол. · случайное зелье"),
            ("Продать рецепт (+28 золота)", lambda run: run.update({"gold": run["gold"] + 28}), "+28 золота"),
        ],
    },
    {
        "id": "void_altar",
        "biome": "ruins",
        "title": "Алтарь Пустоты",
        "text": "Камни пульсируют тёмной силой. Принять дар или разрушить алтарь?",
        "choices": [
            ("Принять дар", lambda run: try_add_card_to_run(run, "phantom_cut"), "Карта «Призрачный Разрез»"),
            ("Разрушить (+35 золота)", lambda run: run.update({"gold": run["gold"] + 35}), "+35 золота"),
        ],
    },
    {
        "id": "snow_echo",
        "biome": "snow",
        "title": "Эхо Метели",
        "text": "Ветер приносит голоса прошлых стражей. Принять дар или укрыться?",
        "choices": [
            ("Принять дар", lambda run: run.update({"pending_event_reward": "rare"}), "Редкая карта"),
            ("Укрыться (+16 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + 16)}), "+16 HP"),
        ],
    },
    {
        "id": "sand_tomb",
        "biome": "desert",
        "title": "Пески Гробницы",
        "text": "Под песками скрыт сундук. Рискнуть HP или обойти?",
        "choices": [
            ("Открыть (−10 HP, зелье)", _sand_tomb_open, "−10 HP · зелье"),
            ("Обойти (+22 золота)", lambda run: run.update({"gold": run["gold"] + 22}), "+22 золота"),
        ],
    },
    {
        "id": "whispering_thicket",
        "biome": "forest",
        "title": "Шепчущая Чаща",
        "text": "Лес шепчет имена павших стражей. Принять дар, укрепить тело или идти дальше?",
        "choices": [
            ("Принять дар", lambda run: try_add_card_to_run(run, "root_snare"), "Карта «Корневая Петля»"),
            ("Укрепиться (+6 max HP)", lambda run: run.update({"max_hp": run["max_hp"] + 6, "hp": run["hp"] + 6}), "+6 max HP"),
            ("Уйти (+20 золота)", lambda run: run.update({"gold": run["gold"] + 20}), "+20 золота"),
        ],
    },
    {
        "id": "healing_spring",
        "title": "Источник Рубежа",
        "text": "Чистая вода пульсирует светом. Выпить или укрепить тело?",
        "choices": [
            ("Выпить (+15 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + 15)}), "+15 HP"),
            ("Укрепить (+4 max HP)", lambda run: run.update({"max_hp": run["max_hp"] + 4, "hp": run["hp"] + 4}), "+4 max HP"),
        ],
    },
    {
        "id": "shadow_deal",
        "title": "Сделка с Тенью",
        "text": "Тень протягивает артефакт, но требует дань проклятием.",
        "choices": [
            ("Принять", _shadow_deal, "Реликвия + проклятие"),
            ("Отказаться", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "hunter_ambush",
        "title": "Засада Охотника",
        "text": "Багровый плащ мелькает между камней. Охотник Рубежа выслеживает слабых стражей.",
        "choices": [
            ("Принять вызов", lambda run: run.update({"pending_hunter_fight": True}), "Бой с охотником"),
            ("Скрыться (−12 HP)", lambda run: run.update({"hp": max(1, run["hp"] - 12)}), "−12 HP"),
            ("Подкуп (−35 зол.)", lambda run: run.update({"gold": run["gold"] - 35}) if run["gold"] >= 35 else None, "−35 зол."),
        ],
    },
    {
        "id": "void_whisper",
        "biome": "void",
        "title": "Шёпот Пустоты",
        "text": "Тьма предлагает силу — цена капля крови или отказ.",
        "choices": [
            ("Принять (+1 энергия, −6 HP)", lambda run: run.update({"bonus_energy": run.get("bonus_energy", 0) + 1, "hp": max(1, run["hp"] - 6)}), "+1 энергия · −6 HP"),
            ("Отвергнуть (+25 золота)", lambda run: run.update({"gold": run["gold"] + 25}), "+25 золота"),
        ],
    },
    {
        "id": "void_shrine",
        "biome": "void",
        "title": "Святилище Разлома",
        "text": "Кристаллы пульсируют в такт твоему пульсу. Укрепить тело или взять дар?",
        "choices": [
            ("Укрепить (+8 max HP)", lambda run: run.update({"max_hp": run["max_hp"] + 8, "hp": run["hp"] + 8}), "+8 max HP"),
            ("Принять дар", lambda run: run.update({"pending_event_reward": "rare"}), "Редкая карта"),
        ],
    },
    {
        "id": "hunter_contract",
        "title": "Контракт Охотника",
        "text": "Охотник предлагает сделку: золото за твою кровь — или наоборот.",
        "choices": [
            ("Заплатить (−30 зол., +20 HP)", lambda run: run.update({"gold": run["gold"] - 30, "hp": min(run["max_hp"], run["hp"] + 20)}) if run["gold"] >= 30 else None, "−30 зол. · +20 HP"),
            ("Продать информацию (+40 зол.)", lambda run: run.update({"gold": run["gold"] + 40, "hp": max(1, run["hp"] - 5)}), "+40 зол. · −5 HP"),
            ("Отказаться", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "shrine_of_fate",
        "title": "Святилище Судьбы",
        "text": "Камни светятся. Принять благословение или обменять его на золото?",
        "choices": [
            ("Принять благословение", lambda run: run.update({"pending_blessing_pick": True}), "Случайное благословение"),
            ("Обменять (+45 зол.)", lambda run: run.update({"gold": run["gold"] + 45}), "+45 золота"),
            ("Уйти", lambda run: None, "Без последствий"),
        ],
    },
    {
        "id": "molten_spring",
        "biome": "desert",
        "title": "Расплавленный Источник",
        "text": "Горячая вода пульсирует пламенем. Ожечь врагов или исцелиться?",
        "choices": [
            ("Исцелиться (+14 HP)", lambda run: run.update({"hp": min(run["max_hp"], run["hp"] + 14)}), "+14 HP"),
            ("Принять пламя (+1 энергия)", lambda run: run.update({"bonus_energy": run.get("bonus_energy", 0) + 1}), "+1 энергия в боях"),
            ("Ожечь тропу", lambda run: run.update({"pending_burn_ambush": True}), "Следующий бой: враги получают 3 ожога"),
        ],
    },
]


MAP_ROWS = 18
MAP_COLS = 9
MAP_EASY_UNTIL = 2
MAP_SPLIT_ROW = 3
MAP_SERVICE_STEP = 4


def map_node_tier(row):
    if row <= MAP_EASY_UNTIL:
        return "easy"
    if row == MAP_SPLIT_ROW:
        return "split"
    return "hard"

# Шаблоны колонок для ровного распределения узлов (минимум 2 клетки между соседями).
_ROW_SLOT_TEMPLATES = {
    1: [(4,)],
    2: [(2, 6), (3, 6), (1, 5), (2, 5), (3, 7), (1, 7)],
    3: [(1, 4, 7), (2, 4, 6), (0, 3, 6), (1, 5, 7), (2, 5, 7), (0, 4, 8)],
    4: [(0, 2, 5, 8), (1, 3, 5, 7), (0, 2, 4, 6), (1, 3, 6, 8), (0, 3, 5, 8)],
    5: [(0, 2, 4, 6, 8), (1, 2, 4, 6, 7), (0, 1, 4, 7, 8), (1, 3, 4, 5, 7)],
    6: [(0, 1, 3, 5, 7, 8), (0, 2, 3, 5, 6, 8), (1, 2, 4, 5, 6, 7)],
}


def _row_node_count(row, rows):
    if row in (0, rows - 1):
        return 1
    if row <= MAP_EASY_UNTIL:
        return 2
    if row == MAP_SPLIT_ROW:
        return rand_int(4, 5)
    if row >= rows - 3:
        return rand_int(2, 3)
    return rand_int(3, 5)


def _service_row(row, rows):
    return MAP_SERVICE_STEP <= row < rows - 2 and row % MAP_SERVICE_STEP == 0


def _pick_service_type():
    roll = random.random()
    if roll < 0.38:
        return "rest"
    if roll < 0.72:
        return "shop"
    if roll < 0.88:
        return "event"
    return "battle"


def _pick_row_slots(cols, count):
    count = max(1, min(count, cols))
    templates = _ROW_SLOT_TEMPLATES.get(count, _ROW_SLOT_TEMPLATES[3])
    slots = set(pick(templates))
    while len(slots) < count:
        candidates = [c for c in range(cols) if c not in slots and all(abs(c - s) >= 2 for s in slots)]
        if not candidates:
            candidates = [c for c in range(cols) if c not in slots]
        if not candidates:
            break
        slots.add(pick(candidates))
    return slots


def generate_map(act_index=0, ascension=0):
    rows, cols = MAP_ROWS, MAP_COLS
    grid = []
    for row in range(rows):
        count = _row_node_count(row, rows)
        slots = _pick_row_slots(cols, count)
        line = []
        for col in range(cols):
            if col in slots:
                line.append(_create_node(row, col, act_index, rows, ascension=ascension))
            else:
                line.append(None)
        grid.append(line)
    _boost_service_nodes(grid)
    _apply_ascension_map({"grid": grid}, ascension)
    _link_nodes(grid)
    return {
        "grid": grid,
        "rows": rows,
        "cols": cols,
        "act": act_index,
        "split_row": MAP_SPLIT_ROW,
        "easy_until": MAP_EASY_UNTIL,
    }


def _apply_ascension_map(map_data, ascension):
    if ascension < 3:
        return
    rests = [n for row in map_data["grid"] for n in row if n and n["type"] == "rest" and not n.get("visited")]
    if rests:
        target = pick(rests)
        target["type"] = "battle"
        target["service"] = False


def _create_node(row, col, act, total_rows, ascension=0):
    tier = map_node_tier(row)
    node_type = "battle"
    if row == total_rows - 1:
        node_type = "boss"
    elif _service_row(row, total_rows):
        node_type = _pick_service_type()
    else:
        elite_chance = get_difficulty()["elite_node_chance"]
        if ascension >= 3:
            from ascension import ascension_elite_bonus
            elite_chance += ascension_elite_bonus(ascension)
        if tier == "hard" and random.random() < elite_chance:
            node_type = "elite"
        elif tier == "hard" and random.random() < get_difficulty()["rest_node_chance"]:
            node_type = "rest"
        elif tier == "hard" and random.random() < get_difficulty().get("shop_node_chance", 0.12):
            node_type = "shop"
        elif tier == "hard" and random.random() < 0.12:
            node_type = "event"
        elif tier == "hard" and random.random() < 0.07:
            node_type = "treasure"
    return {
        "id": f"{act}_{row}_{col}",
        "row": row,
        "col": col,
        "type": node_type,
        "tier": tier,
        "links": [],
        "visited": False,
        "available": row == 0,
        "service": node_type in ("rest", "shop"),
        "x": 0,
        "y": 0,
    }


def _boost_service_nodes(grid):
    rows = len(grid)
    for row in range(rows):
        nodes = [n for n in grid[row] if n]
        if not nodes:
            continue
        for node in nodes:
            if node["type"] in ("rest", "shop"):
                node["service"] = True
        if row < 3 or row >= rows - 2:
            continue
        if not _service_row(row, rows):
            continue
        services = [n for n in nodes if n["type"] in ("rest", "shop")]
        if len(services) >= 1:
            continue
        target = min(nodes, key=lambda n: abs(n["col"] - (MAP_COLS // 2)))
        target["type"] = pick(["rest", "rest", "shop", "shop"])
        target["service"] = True


def _link_nodes(grid):
    for r in range(len(grid) - 1):
        current = [n for n in grid[r] if n]
        nxt = [n for n in grid[r + 1] if n]
        if not current or not nxt:
            continue
        for node in current:
            wide = [n for n in nxt if abs(n["col"] - node["col"]) <= 2]
            candidates = wide or sorted(nxt, key=lambda n: abs(n["col"] - node["col"]))[:3]
            candidates = sorted(candidates, key=lambda n: (abs(n["col"] - node["col"]), n["col"]))
            link_count = 1
            if len(candidates) > 1:
                roll = random.random()
                if roll < 0.58:
                    link_count = 2
                elif roll < 0.78 and len(candidates) > 2:
                    link_count = 3
            targets = candidates[:link_count]
            if link_count >= 2 and len(candidates) > link_count and random.random() < 0.45:
                targets = [candidates[0], pick(candidates[1:])]
                if link_count == 3 and len(candidates) > 2:
                    extra = [c for c in candidates[1:] if c not in targets]
                    if extra:
                        targets.append(pick(extra))
            for target in targets:
                if target["id"] not in node["links"]:
                    node["links"].append(target["id"])
        for node in nxt:
            if not any(node["id"] in parent["links"] for parent in current):
                parent = min(current, key=lambda p: abs(p["col"] - node["col"]))
                if node["id"] not in parent["links"]:
                    parent["links"].append(node["id"])


def flatten_map(game_map):
    return [n for row in game_map["grid"] for n in row if n]


def get_node(game_map, node_id):
    for node in flatten_map(game_map):
        if node["id"] == node_id:
            return node
    return None


def visit_node(game_map, node_id):
    node = get_node(game_map, node_id)
    if not node:
        return
    node["visited"] = True
    node["available"] = False
    for n in flatten_map(game_map):
        n["available"] = n["id"] in node["links"]


def layout_map(game_map, area=None):
    nodes = flatten_map(game_map)
    if not nodes:
        return
    if area is None:
        import ui_theme

        area = ui_theme.MAP_LAYOUT["map"].inflate(-config.sx(8), -config.sy(24))
    lanes = game_map.get("cols", MAP_COLS)
    max_row = max(n["row"] for n in nodes) + 1
    pad_x = config.sx(20)
    pad_top = config.sy(12)
    pad_bottom = config.sy(16)
    usable_w = max(config.sx(360), area.width - pad_x * 2)
    usable_h = max(config.sy(280), area.height - pad_top - pad_bottom)
    col_w = max(config.sx(122), usable_w // lanes)
    row_h = max(config.sy(54), usable_h // max_row)
    grid_w = lanes * col_w
    start_x = area.x + max(pad_x, (area.width - grid_w) // 2)
    start_y = area.bottom - pad_bottom
    game_map["_layout"] = {
        "lanes": lanes,
        "col_w": col_w,
        "row_h": row_h,
        "start_x": start_x,
        "start_y": start_y,
        "max_row": max_row,
    }
    for node in nodes:
        lane_x = start_x + node["col"] * col_w + col_w // 2
        if node["row"] % 2 == 1:
            lane_x += col_w // 2
        node["x"] = int(lane_x)
        node["y"] = int(start_y - node["row"] * row_h)


def get_act_info(act_index):
    return ACTS[act_index] if act_index < len(ACTS) else ACTS[0]


def roll_event(act=0):
    biome = ACTS[act]["biome"] if act < len(ACTS) else "forest"
    pool = [e for e in EVENTS if not e.get("biome") or e["biome"] == biome]
    ev = pick(pool or EVENTS)
    return {"id": ev["id"], "title": ev["title"], "text": ev["text"], "choices": ev["choices"]}
