"""Процедурные иконки для UI, карт, врагов и узлов карты."""

import pygame


def _circle(surf, color, cx, cy, r, width=0):
    pygame.draw.circle(surf, color, (cx, cy), r, width)


def _poly(surf, color, points, width=0):
    pygame.draw.polygon(surf, color, points, width)


def draw_node_icon(surf, cx, cy, size, node_type, tint=(255, 255, 255)):
    s = size
    if node_type == "battle":
        _poly(surf, tint, [(cx - s * 0.35, cy + s * 0.3), (cx + s * 0.35, cy + s * 0.3), (cx, cy - s * 0.4)])
        pygame.draw.rect(surf, tint, (cx - s * 0.08, cy - s * 0.15, s * 0.16, s * 0.55))
    elif node_type == "elite":
        _circle(surf, tint, cx, cy - s * 0.05, int(s * 0.22), 2)
        _poly(surf, tint, [(cx - s * 0.28, cy + s * 0.3), (cx + s * 0.28, cy + s * 0.3), (cx, cy - s * 0.05)])
    elif node_type == "rest":
        _circle(surf, (255, 140, 60), cx, cy + s * 0.1, int(s * 0.18))
        _poly(surf, tint, [(cx - s * 0.12, cy - s * 0.05), (cx + s * 0.12, cy - s * 0.05), (cx, cy - s * 0.35)])
    elif node_type == "shop":
        pygame.draw.rect(surf, tint, (cx - s * 0.25, cy - s * 0.15, s * 0.5, s * 0.35), border_radius=3)
        pygame.draw.arc(surf, tint, (cx - s * 0.3, cy - s * 0.45, s * 0.6, s * 0.35), 0, 3.14, 2)
    elif node_type == "event":
        _circle(surf, tint, cx, cy, int(s * 0.28), 2)
        pygame.draw.line(surf, tint, (cx, cy - s * 0.12), (cx, cy + s * 0.02), 2)
        _circle(surf, tint, cx, cy + s * 0.15, 3)
    elif node_type == "boss":
        _circle(surf, tint, cx, cy, int(s * 0.3), 2)
        _circle(surf, tint, cx - s * 0.12, cy - s * 0.05, 5)
        _circle(surf, tint, cx + s * 0.12, cy - s * 0.05, 5)


def draw_card_type_icon(surf, x, y, size, card_type):
    cx, cy = x + size // 2, y + size // 2
    s = size * 0.45
    if card_type == "attack":
        _poly(surf, (255, 210, 210), [(cx, cy - s), (cx + s * 0.55, cy + s * 0.7), (cx - s * 0.55, cy + s * 0.7)])
    elif card_type == "skill":
        _poly(surf, (180, 220, 255), [(cx, cy - s * 0.8), (cx + s * 0.75, cy), (cx, cy + s * 0.8), (cx - s * 0.75, cy)])
    elif card_type == "power":
        _circle(surf, (210, 180, 255), cx, cy, int(s * 0.65), 2)
        pygame.draw.line(surf, (210, 180, 255), (cx, cy - s * 0.5), (cx, cy + s * 0.5), 2)
    elif card_type == "curse":
        _circle(surf, (180, 100, 140), cx, cy, int(s * 0.55), 2)
        pygame.draw.line(surf, (220, 140, 160), (cx - s * 0.35, cy - s * 0.35), (cx + s * 0.35, cy + s * 0.35), 2)
        pygame.draw.line(surf, (220, 140, 160), (cx + s * 0.35, cy - s * 0.35), (cx - s * 0.35, cy + s * 0.35), 2)


def draw_potion_icon(surf, x, y, size, potion_id, color=None):
    from potions import POTION_DEFS

    info = POTION_DEFS.get(potion_id, {})
    col = color or info.get("color", (120, 180, 255))
    cx, cy = x + size // 2, y + size // 2
    s = size * 0.38
    pygame.draw.rect(surf, col, (cx - s * 0.45, cy - s * 0.15, s * 0.9, s * 0.75), border_radius=3)
    pygame.draw.rect(surf, lerp_color(col, (255, 255, 255), 0.25), (cx - s * 0.22, cy - s * 0.55, s * 0.44, s * 0.42), border_radius=2)
    pygame.draw.rect(surf, lerp_color(col, (0, 0, 0), 0.2), (cx - s * 0.45, cy - s * 0.15, s * 0.9, s * 0.75), 2, border_radius=3)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_intent_icon(surf, x, y, size, intent):
    cx, cy = x + size // 2, y + size // 2
    s = size * 0.4
    kind = intent.get("intent", "")
    if kind in ("attack", "multi"):
        _poly(surf, (255, 100, 100), [(cx + s, cy - s * 0.2), (cx - s * 0.2, cy + s * 0.5), (cx + s * 0.3, cy + s * 0.5)])
    elif kind == "block":
        _poly(surf, (100, 160, 255), [(cx, cy - s * 0.7), (cx + s * 0.7, cy - s * 0.1), (cx + s * 0.45, cy + s * 0.6), (cx - s * 0.45, cy + s * 0.6), (cx - s * 0.7, cy - s * 0.1)])
    elif kind == "buff":
        pygame.draw.line(surf, (255, 180, 80), (cx - s * 0.5, cy + s * 0.3), (cx + s * 0.5, cy - s * 0.3), 3)
    elif kind in ("debuff", "steal_block"):
        _circle(surf, (200, 120, 255), cx, cy, int(s * 0.55), 2)
    elif kind == "curse":
        pygame.draw.line(surf, (180, 100, 220), (cx - s * 0.4, cy - s * 0.3), (cx + s * 0.4, cy + s * 0.3), 2)
        pygame.draw.line(surf, (180, 100, 220), (cx + s * 0.4, cy - s * 0.3), (cx - s * 0.4, cy + s * 0.3), 2)


def draw_enemy_icon(surf, x, y, w, h, enemy_id, color):
    cx, cy = x + w // 2, y + h // 2 - 4
    s = min(w, h) * 0.35
    if enemy_id in ("slime", "frost_slime"):
        _circle(surf, color, cx, cy + s * 0.15, int(s * 0.75))
        _circle(surf, (255, 255, 255), cx - s * 0.25, cy, 4)
        _circle(surf, (255, 255, 255), cx + s * 0.25, cy, 4)
    elif enemy_id == "wolf":
        _poly(surf, color, [(cx - s, cy + s * 0.4), (cx + s, cy + s * 0.4), (cx + s * 0.5, cy - s * 0.2), (cx, cy - s * 0.6), (cx - s * 0.5, cy - s * 0.2)])
    elif enemy_id == "scorpion":
        _circle(surf, color, cx, cy, int(s * 0.45))
        pygame.draw.line(surf, color, (cx + s * 0.4, cy), (cx + s * 0.9, cy - s * 0.5), 3)
    elif enemy_id in ("sand_colossus", "sand_tyrant", "moss_colossus"):
        pygame.draw.rect(surf, color, (cx - s * 0.7, cy - s * 0.5, s * 1.4, s * 1.0), border_radius=4)
    elif enemy_id == "wraith":
        _poly(surf, color, [(cx, cy - s), (cx + s * 0.7, cy + s * 0.5), (cx - s * 0.7, cy + s * 0.5)])
    elif enemy_id in ("ice_guardian", "blue_boss"):
        pygame.draw.rect(surf, color, (cx - s * 0.55, cy - s * 0.7, s * 1.1, s * 1.3), border_radius=6)
    elif enemy_id == "border_hunter":
        _poly(surf, color, [(cx - s, cy + s * 0.35), (cx + s, cy + s * 0.35), (cx + s * 0.4, cy - s * 0.15), (cx, cy - s * 0.65), (cx - s * 0.4, cy - s * 0.15)])
        pygame.draw.line(surf, (255, 200, 200), (cx - s * 0.5, cy - s * 0.1), (cx + s * 0.5, cy + s * 0.2), 2)
    elif enemy_id in ("void_shade", "void_sovereign", "void_lurker", "curse_weaver", "rift_stalker", "void_binder"):
        _poly(surf, color, [(cx, cy - s), (cx + s * 0.75, cy + s * 0.55), (cx - s * 0.75, cy + s * 0.55)])
        pygame.draw.circle(surf, (220, 180, 255), (cx - s * 0.2, cy - s * 0.05), 4)
        pygame.draw.circle(surf, (220, 180, 255), (cx + s * 0.2, cy - s * 0.05), 4)
    else:
        _circle(surf, color, cx, cy, int(s * 0.6))


def draw_stat_icon(surf, x, y, size, kind, color):
    cx, cy = x + size // 2, y + size // 2
    s = size * 0.4
    if kind == "hp":
        _poly(surf, color, [(cx, cy - s * 0.6), (cx + s * 0.55, cy - s * 0.1), (cx + s * 0.55, cy + s * 0.4), (cx, cy + s * 0.7), (cx - s * 0.55, cy + s * 0.4), (cx - s * 0.55, cy - s * 0.1)])
    elif kind == "gold":
        _circle(surf, color, cx, cy, int(s * 0.55), 2)
    elif kind == "energy":
        _poly(surf, color, [(cx, cy - s * 0.7), (cx + s * 0.35, cy), (cx, cy + s * 0.2), (cx - s * 0.35, cy)])
    elif kind == "block":
        _poly(surf, color, [(cx, cy - s * 0.55), (cx + s * 0.55, cy - s * 0.05), (cx + s * 0.35, cy + s * 0.55), (cx - s * 0.35, cy + s * 0.55), (cx - s * 0.55, cy - s * 0.05)])
    elif kind == "deck":
        pygame.draw.rect(surf, color, (cx - s * 0.35, cy - s * 0.45, s * 0.55, s * 0.7), border_radius=3)
        pygame.draw.rect(surf, color, (cx - s * 0.15, cy - s * 0.55, s * 0.55, s * 0.7), border_radius=3, width=2)


STATUS_NAMES = {
    "weak": "Слабость",
    "vulnerable": "Уязвимость",
    "poison": "Яд",
    "strength": "Сила",
}

STATUS_DESC = {
    "weak": "Атаки наносят на 25% меньше урона.",
    "vulnerable": "Получаемый урон увеличен на 50%.",
    "poison": "В начале хода теряешь HP (стек).",
    "strength": "Каждая атака наносит +1 урона за стек.",
}

POWER_NAMES = {
    "strength": "Сила",
    "metallicize": "Металл",
    "blood_pact": "Кровавый Пакт",
}

POWER_DESC = {
    "strength": "В начале хода получаешь Силу (стек).",
    "metallicize": "В начале хода получаешь блок (стек).",
    "blood_pact": "В начале хода: +сила, −2 HP.",
}

INTENT_DESC = {
    "attack": "Враг нанесёт указанный урон.",
    "multi": "Несколько ударов подряд.",
    "block": "Враг получит блок.",
    "buff": "Враг усилит себя.",
    "debuff": "Враг наложит негативный эффект.",
    "steal_block": "Враг украдёт часть твоего блока.",
    "curse": "Враг вплетёт проклятие в колоду.",
}

BLOCK_DESC = "Поглощает урон до конца хода, затем сгорает."
ENEMY_BLOCK_DESC = "Поглощает урон от твоих атак, пока не будет пробит."
