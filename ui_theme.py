"""Визуальная тема и UI-компоненты."""

import math
import pygame

import config
from config import COLORS, clamp

# --- Базовая раскладка 1280x720, масштабируется через rebuild_layouts() ---
_BASE_W, _BASE_H = 1280, 720

COMBAT_LAYOUT = {
    "hud": pygame.Rect(16, 12, 1248, 72),
    "potions": pygame.Rect(16, 88, 280, 48),
    "arena": pygame.Rect(16, 142, 1248, 220),
    "log": pygame.Rect(16, 378, 280, 196),
    "hand": pygame.Rect(308, 378, 956, 196),
    "actions": pygame.Rect(308, 582, 956, 32),
    "footer_y": 686,
}

ENTITY_W, ENTITY_H = 240, 58
CARD_W, CARD_H, CARD_GAP = 128, 132, 12

MAP_LAYOUT = {
    "map": pygame.Rect(16, 92, 1248, 592),
}

REWARD_CARD_W, REWARD_CARD_H = 148, 196
SHOP_CARD_W, SHOP_CARD_H = 148, 196


def rebuild_layouts(width=None, height=None):
    global COMBAT_LAYOUT, MAP_LAYOUT, ENTITY_W, ENTITY_H, CARD_W, CARD_H, CARD_GAP
    global REWARD_CARD_W, REWARD_CARD_H, SHOP_CARD_W, SHOP_CARD_H
    w = width or config.SCREEN_WIDTH
    h = height or config.SCREEN_HEIGHT
    sw = lambda v: int(v * w / _BASE_W)
    sh = lambda v: int(v * h / _BASE_H)
    margin_x = sw(12)
    hud_y = sh(12)
    hud_h = sh(72)
    hint_h = sh(34)
    footer = hint_h + sh(10)
    hand_h = sh(196)
    actions_h = sh(32)
    log_w = sw(280)
    gap = sw(12)
    potion_h = sh(48)
    potion_y = hud_y + hud_h + sh(4)
    top = potion_y + potion_h + sh(6)
    actions_y = h - footer - actions_h
    hand_y = actions_y - sh(8) - hand_h
    arena_h = hand_y - top - sh(10)
    COMBAT_LAYOUT["hud"] = pygame.Rect(margin_x, hud_y, w - margin_x * 2, hud_h)
    COMBAT_LAYOUT["potions"] = pygame.Rect(margin_x, potion_y, sw(280), potion_h)
    COMBAT_LAYOUT["arena"] = pygame.Rect(margin_x, top, w - margin_x * 2, max(sh(160), arena_h))
    COMBAT_LAYOUT["log"] = pygame.Rect(margin_x, hand_y, log_w, hand_h)
    COMBAT_LAYOUT["hand"] = pygame.Rect(margin_x + log_w + gap, hand_y, w - margin_x * 2 - log_w - gap, hand_h)
    COMBAT_LAYOUT["actions"] = pygame.Rect(margin_x + log_w + gap, actions_y, w - margin_x * 2 - log_w - gap, actions_h)
    COMBAT_LAYOUT["footer_y"] = h - hint_h
    top_y = top
    footer_space = footer
    content_h = max(sh(400), h - top_y - footer_space)
    MAP_LAYOUT["map"] = pygame.Rect(margin_x, top_y, w - margin_x * 2, content_h)
    MAP_LAYOUT.pop("sidebar", None)
    ENTITY_W = sw(240)
    ENTITY_H = sh(58)
    CARD_W = sw(128)
    CARD_H = sh(132)
    CARD_GAP = sw(12)
    REWARD_CARD_W = sw(148)
    REWARD_CARD_H = sh(196)
    SHOP_CARD_W = sw(148)
    SHOP_CARD_H = sh(196)


class AnimatedBackground:
    def __init__(self, seed=7):
        self.phase = 0.0
        self.stars = [
            ((i * 137 + seed * 17) % config.SCREEN_WIDTH, (i * 97 + seed * 11) % config.SCREEN_HEIGHT, 1 + i % 3, i * 0.7)
            for i in range(100)
        ]
        self.orbs = [
            (180 + i * 220, 80 + i * 90, 90 + i * 20, COLORS["accent"] if i % 2 == 0 else COLORS["accent_warm"])
            for i in range(3)
        ]

    def update(self, dt=1.0):
        self.phase += 0.012 * dt

    def draw(self, screen, accent=None, biome=None):
        biome_tints = {
            "forest": COLORS["forest"],
            "desert": COLORS["desert"],
            "snow": COLORS["snow"],
        }
        tint = biome_tints.get(biome, accent or COLORS["accent"])
        for y in range(0, config.SCREEN_HEIGHT, 3):
            t = y / config.SCREEN_HEIGHT
            top = lerp_color(COLORS["bg_top"], tint, 0.06 if biome else 0)
            bottom = lerp_color(COLORS["bg_bottom"], tint, 0.08 if biome else 0)
            c = lerp_color(top, bottom, t)
            pygame.draw.rect(screen, c, (0, y, config.SCREEN_WIDTH, 3))

        for sx, sy, size, twinkle in self.stars:
            alpha = int(100 + 80 * math.sin(self.phase * 2 + twinkle))
            pygame.draw.circle(screen, (alpha, alpha, min(255, alpha + 30)), (sx, sy), size)

        orb_color = tint
        warm = lerp_color(COLORS["accent_warm"], tint, 0.35 if biome else 0)
        for i, (ox, oy, radius, _) in enumerate(self.orbs):
            color = orb_color if i % 2 == 0 else warm
            px = ox + int(math.sin(self.phase + ox * 0.01) * 24)
            py = oy + int(math.cos(self.phase * 0.8 + oy * 0.01) * 18)
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 16), (radius, radius), radius)
            screen.blit(glow, (px - radius, py - radius))

        draw_vignette(screen)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_vignette(screen, strength=70):
    vignette = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    for edge in range(0, strength, 4):
        alpha = int(edge * 0.55)
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (0, edge, config.SCREEN_WIDTH, 4))
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (0, config.SCREEN_HEIGHT - edge - 4, config.SCREEN_WIDTH, 4))
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (edge, 0, 4, config.SCREEN_HEIGHT))
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (config.SCREEN_WIDTH - edge - 4, 0, 4, config.SCREEN_HEIGHT))
    screen.blit(vignette, (0, 0))


def draw_panel(screen, rect, fill=None, border=None, radius=14, alpha=230, shadow=True):
    fill = fill or COLORS["panel"]
    border = border or COLORS["panel_border"]
    if shadow:
        sh = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 90), (4, 6, rect.width, rect.height), border_radius=radius)
        screen.blit(sh, (rect.x - 4, rect.y - 2))
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*fill, alpha), surf.get_rect(), border_radius=radius)
    pygame.draw.rect(surf, (*border, min(255, alpha + 20)), surf.get_rect(), 2, border_radius=radius)
    screen.blit(surf, rect.topleft)


def draw_top_bar(screen, fonts, title, subtitle="", stats=None, accent=None, energy=None, buttons=None, stat_clicks=None):
    accent = accent or COLORS["accent"]
    bar_h = config.sy(72)
    bar = pygame.Rect(config.sx(16), config.sy(12), config.SCREEN_WIDTH - config.sx(32), bar_h)
    draw_panel(screen, bar, fill=(14, 18, 28), border=accent, radius=16, alpha=210)

    title_x = bar.x + config.sx(20)
    title_max_w = bar.width // 2 - config.sx(24)
    title_surf = fonts["title_sm"].render(title, True, COLORS["text"])
    if title_surf.get_width() > title_max_w:
        trimmed = title
        while trimmed and fonts["title_sm"].size(trimmed + "…")[0] > title_max_w:
            trimmed = trimmed[:-1]
        title_surf = fonts["title_sm"].render(trimmed + "…", True, COLORS["text"])
    screen.blit(title_surf, (title_x, bar.y + config.sy(10)))
    if subtitle:
        sub_max_w = bar.width // 2
        sub = subtitle
        if fonts["sm"].size(sub)[0] > sub_max_w:
            while sub and fonts["sm"].size(sub + "…")[0] > sub_max_w:
                sub = sub[:-1]
            sub += "…"
        screen.blit(fonts["sm"].render(sub, True, COLORS["text_dim"]), (title_x, bar.y + config.sy(36)))

    cx = bar.centerx
    if energy is not None:
        cur, mx = energy
        orb_x = cx - (mx * config.sx(28)) // 2
        draw_energy_orbs(screen, orb_x, bar.y + config.sy(22), cur, mx)

    if stats:
        sx_pos = bar.right - config.sx(16)
        chip_h = config.sy(36)
        chip_y = bar.y + (bar_h - chip_h) // 2
        for label, value, color in reversed(stats):
            val_surf = fonts["sm"].render(str(value), True, color)
            lbl_surf = fonts["sm"].render(label, True, COLORS["text_dim"])
            chip_w = val_surf.get_width() + lbl_surf.get_width() + config.sx(26)
            chip = pygame.Rect(sx_pos - chip_w, chip_y, chip_w, chip_h)
            draw_panel(screen, chip, fill=(10, 14, 22), border=color, radius=10, alpha=200, shadow=False)
            screen.blit(lbl_surf, (chip.x + config.sx(10), chip.y + config.sy(10)))
            screen.blit(val_surf, (chip.right - val_surf.get_width() - config.sx(10), chip.y + config.sy(10)))
            if buttons and stat_clicks and label in stat_clicks:
                buttons.add(chip, stat_clicks[label], primary=False)
            sx_pos = chip.x - config.sx(10)
    return bar


class ButtonRegistry:
    def __init__(self):
        self.items = []

    def clear(self):
        self.items = []

    def add(self, rect, callback, primary=True):
        self.items.append({"rect": pygame.Rect(rect), "callback": callback, "primary": primary})

    def draw(self, screen, fonts, mouse):
        for btn in self.items:
            rect = btn["rect"]
            hovered = rect.collidepoint(mouse)
            if btn["primary"]:
                top = lerp_color(COLORS["accent"], (255, 255, 255), 0.15 if hovered else 0)
                bottom = lerp_color((40, 130, 125), COLORS["accent"], 0.3 if hovered else 0)
                text_color = (10, 18, 24)
                border = (255, 255, 255)
            else:
                top = lerp_color((52, 62, 82), (72, 86, 110), 0.4 if hovered else 0)
                bottom = lerp_color((34, 42, 58), (52, 62, 82), 0.3 if hovered else 0)
                text_color = COLORS["text"]
                border = COLORS["panel_border"]

            draw_rect = rect.move(0, -1 if hovered else 0)
            pygame.draw.rect(screen, (0, 0, 0), draw_rect.move(0, 3), border_radius=12)
            for i in range(draw_rect.height):
                t = i / max(1, draw_rect.height)
                pygame.draw.rect(screen, lerp_color(top, bottom, t), (draw_rect.x, draw_rect.y + i, draw_rect.width, 1))
            pygame.draw.rect(screen, border, draw_rect, 2, border_radius=12)

    def hit(self, pos):
        for btn in self.items:
            if btn["rect"].collidepoint(pos):
                btn["callback"]()
                return True
        return False


def draw_button(screen, fonts, rect, label, mouse, registry, callback, primary=True):
    hovered = rect.collidepoint(mouse)
    draw_rect = rect.move(0, -1 if hovered else 0)
    if primary:
        top = lerp_color(COLORS["accent"], (255, 255, 255), 0.15 if hovered else 0)
        bottom = lerp_color((40, 130, 125), COLORS["accent"], 0.3 if hovered else 0)
        text_color = (10, 18, 24)
        border = (255, 255, 255)
    else:
        top = lerp_color((52, 62, 82), (72, 86, 110), 0.4 if hovered else 0)
        bottom = lerp_color((34, 42, 58), (52, 62, 82), 0.3 if hovered else 0)
        text_color = COLORS["text"]
        border = COLORS["panel_border"]

    pygame.draw.rect(screen, (0, 0, 0), draw_rect.move(0, 3), border_radius=12)
    for i in range(draw_rect.height):
        t = i / max(1, draw_rect.height)
        pygame.draw.rect(screen, lerp_color(top, bottom, t), (draw_rect.x, draw_rect.y + i, draw_rect.width, 1))
    pygame.draw.rect(screen, border, draw_rect, 2, border_radius=12)
    text = fonts["lg"].render(label, True, text_color)
    screen.blit(text, text.get_rect(center=draw_rect.center))
    registry.add(rect, callback, primary)


def draw_hp_bar(screen, fonts, x, y, w, hp, max_hp, h=16):
    ratio = clamp(hp / max_hp, 0, 1)
    w = max(h * 2, w)
    bg = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (24, 28, 36), bg, border_radius=max(2, h // 2))
    if ratio > 0:
        fill_w = min(w, max(h, int(w * ratio)))
        color = COLORS["success"] if ratio > 0.35 else COLORS["danger"]
        grad_top = lerp_color(color, (255, 255, 255), 0.2)
        for i in range(h):
            t = i / max(1, h)
            pygame.draw.rect(screen, lerp_color(grad_top, color, t), (x, y + i, fill_w, 1))
        pygame.draw.rect(screen, lerp_color(color, (0, 0, 0), 0.25), pygame.Rect(x, y, fill_w, h), 1, border_radius=max(2, h // 2))
    txt = fonts["sm"].render(f"{hp}/{max_hp}", True, COLORS["text"])
    if txt.get_width() > w - 4:
        txt = fonts["sm"].render(f"{hp}", True, COLORS["text"])
    screen.blit(txt, txt.get_rect(center=bg.center))


def draw_energy_orbs(screen, x, y, current, maximum):
    for i in range(maximum):
        cx = x + i * 28
        filled = i < current
        color = COLORS["accent"] if filled else (40, 48, 62)
        pygame.draw.circle(screen, (20, 24, 32), (cx + 1, y + 13), 11)
        pygame.draw.circle(screen, color, (cx, y + 12), 11)
        if filled:
            pygame.draw.circle(screen, lerp_color(color, (255, 255, 255), 0.35), (cx - 3, y + 8), 4)
        else:
            pygame.draw.circle(screen, COLORS["panel_border"], (cx, y + 12), 11, 2)


def draw_section_panel(screen, rect, title, fonts, accent=None, alpha=215):
    accent = accent or COLORS["accent"]
    draw_panel(screen, rect, fill=(12, 16, 26), border=accent, radius=14, alpha=alpha)
    header_h = 28
    header = pygame.Rect(rect.x + 1, rect.y + 1, rect.width - 2, header_h)
    for row in range(header_h):
        t = row / max(1, header_h - 1)
        c = lerp_color((18, 24, 36), (14, 18, 28), t)
        pygame.draw.line(screen, c, (header.x, header.y + row), (header.right, header.y + row))
    pygame.draw.line(screen, (*lerp_color(accent, (0, 0, 0), 0.35), 120), (rect.x + 12, rect.y + header_h), (rect.right - 12, rect.y + header_h), 1)
    screen.blit(fonts["sm"].render(title, True, accent if accent else COLORS["text_dim"]), (rect.x + 14, rect.y + 7))
    return pygame.Rect(rect.x + 10, rect.y + header_h + 8, rect.width - 20, rect.height - header_h - 14)


def draw_card(screen, fonts, card, x, y, w, h, playable, hovered, draw_type_icon):
    from sprites import draw_card_art

    lift = -10 if hovered and playable else 0
    y += lift
    rect = pygame.Rect(x, y, w, h)

    base_key = f"card_{card['type']}"
    base = COLORS.get(base_key, COLORS["panel_border"])
    if not playable:
        base = (42, 44, 52)

    pygame.draw.rect(screen, (0, 0, 0), rect.move(0, 5), border_radius=14)

    body = pygame.Surface((w, h), pygame.SRCALPHA)
    for row in range(h):
        t = row / max(1, h)
        c = lerp_color(lerp_color(base, (0, 0, 0), 0.18), lerp_color(base, (255, 255, 255), 0.06), t)
        pygame.draw.rect(body, (*c, 248), (0, row, w, 1))

    rarity_colors = {"starter": COLORS["text_dim"], "common": COLORS["text_dim"], "uncommon": (120, 180, 255), "rare": COLORS["gold"]}
    stripe = rarity_colors.get(card.get("rarity", "common"), COLORS["text_dim"])
    if card.get("upgraded"):
        stripe = COLORS["gold"]
    pygame.draw.rect(body, (*stripe, 230), (0, 0, 5, h), border_radius=3)
    border_col = COLORS["gold"] if card.get("upgraded") else (COLORS["accent"] if hovered and playable else (255, 255, 255))
    border_a = 220 if card.get("upgraded") else (200 if hovered and playable else 35)
    pygame.draw.rect(body, (*border_col, border_a), body.get_rect(), 2, border_radius=14)
    screen.blit(body, rect.topleft)

    footer_h = max(config.sy(54), int(h * 0.40))
    pad = max(4, int(6 * w / max(1, CARD_W)))
    art_top = y + pad
    art_bottom = y + h - footer_h - pad
    art_h = max(config.sy(36), art_bottom - art_top)
    art_w = w - pad * 2
    art_x = x + pad

    draw_card_art(screen, card, art_x, art_top, art_w, art_h)
    pygame.draw.rect(screen, lerp_color(base, (255, 255, 255), 0.18), pygame.Rect(art_x, art_top, art_w, art_h), 1, border_radius=8)

    footer = pygame.Rect(x + 1, y + h - footer_h, w - 2, footer_h - 1)
    foot_surf = pygame.Surface((footer.width, footer.height), pygame.SRCALPHA)
    for row in range(footer.height):
        t = row / max(1, footer.height - 1)
        c = lerp_color((8, 10, 16), (14, 18, 26), t)
        pygame.draw.rect(foot_surf, (*c, 245), (0, row, footer.width, 1))
    screen.blit(foot_surf, footer.topleft)
    pygame.draw.line(screen, (*lerp_color(base, (255, 255, 255), 0.15), 80), (footer.x, footer.y), (footer.right, footer.y), 1)

    cost_r = max(10, int(13 * min(w / max(1, CARD_W), h / max(1, CARD_H))))
    cost_x = x + cost_r + 8
    cost_y = y + cost_r + 8
    pygame.draw.circle(screen, (0, 0, 0), (cost_x + 1, cost_y + 1), cost_r + 1)
    pygame.draw.circle(screen, COLORS["gold"], (cost_x, cost_y), cost_r)
    pygame.draw.circle(screen, lerp_color(COLORS["gold"], (255, 255, 255), 0.35), (cost_x - cost_r // 3, cost_y - cost_r // 3), max(3, cost_r // 3))
    cost = fonts["md"].render(str(card["cost"]), True, (24, 18, 8))
    screen.blit(cost, cost.get_rect(center=(cost_x, cost_y)))

    icon_sz = max(16, int(22 * min(w / max(1, CARD_W), h / max(1, CARD_H))))
    draw_type_icon(screen, x + w - icon_sz - pad, y + pad, icon_sz, card["type"])

    if card.get("upgraded"):
        badge = pygame.Rect(x + w - pad - 28, y + h - footer_h - 20, 26, 18)
        pygame.draw.rect(screen, COLORS["gold"], badge, border_radius=5)
        plus = fonts["sm"].render("+", True, (24, 16, 8))
        screen.blit(plus, plus.get_rect(center=badge.center))

    name_y = footer.y + config.sy(5)
    name_txt = fonts["card"].render(card["name"], True, COLORS["text"])
    name_max_w = footer.width - config.sx(16)
    if name_txt.get_width() > name_max_w:
        short = card["name"]
        while short and fonts["card"].size(short + "…")[0] > name_max_w:
            short = short[:-1]
        name_txt = fonts["card"].render(short + "…", True, COLORS["text"])
    screen.blit(name_txt, (footer.x + config.sx(8), name_y))
    type_labels = {"attack": "Атака", "skill": "Навык", "power": "Сила"}
    type_label = type_labels.get(card["type"], card["type"])
    type_surf = fonts["sm"].render(type_label, True, lerp_color(base, (255, 255, 255), 0.45))
    type_y = name_y + config.sy(16)
    desc_y = type_y + config.sy(15)
    desc_max_w = footer.width - config.sx(16)
    wrap_text(
        screen, fonts["sm"], card["desc"], footer.x + config.sx(8), desc_y,
        desc_max_w, COLORS["text_dim"],
        line_h=config.sy(13),
    )
    screen.blit(type_surf, (footer.x + config.sx(8), type_y))
    return rect


def wrap_text(screen, font, text, x, y, max_w, color, line_h=18):
    words = text.split()
    line, cy = "", y
    for word in words:
        test = (line + " " + word).strip()
        if font.size(test)[0] > max_w and line:
            screen.blit(font.render(line, True, color), (x, cy))
            line, cy = word, cy + line_h
        else:
            line = test
    if line:
        screen.blit(font.render(line, True, color), (x, cy))


def draw_entity_panel(screen, fonts, name, entity, x, y, accent, draw_icon_fn, intent=None, intent_icon_fn=None, intent_label_fn=None, intent_color_fn=None, highlight=False, acting=False, w=ENTITY_W, h=None, chip_hits=None, next_intent=None):
    h = h or config.sy(84)
    rect = pygame.Rect(x, y, w, h)
    border = accent if highlight or acting else COLORS["panel_border"]
    fill = (28, 38, 58) if acting else ((20, 28, 44) if highlight else (16, 22, 34))
    draw_panel(screen, rect, fill=fill, border=border, radius=12, alpha=240, shadow=False)
    if acting:
        glow = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent, 35), glow.get_rect(), border_radius=14)
        screen.blit(glow, (x - 6, y - 6))

    portrait = pygame.Rect(x + config.sx(8), y + config.sy(8), config.sx(44), config.sy(44))
    for row in range(portrait.height):
        t = row / max(1, portrait.height - 1)
        c = lerp_color((12, 16, 24), (8, 10, 18), t)
        pygame.draw.line(screen, c, (portrait.x, portrait.y + row), (portrait.right, portrait.y + row))
    pygame.draw.rect(screen, accent, portrait, 2, border_radius=8)
    draw_icon_fn(screen, portrait.x + 2, portrait.y + 2, portrait.width - 4, portrait.height - 4)

    tx = x + config.sx(60)
    name_surf = fonts["sm"].render(name, True, accent)
    if name_surf.get_width() > w - config.sx(120):
        short = name
        while short and fonts["sm"].size(short + "…")[0] > w - config.sx(120):
            short = short[:-1]
        name_surf = fonts["sm"].render(short + "…", True, accent)
    screen.blit(name_surf, (tx, y + config.sy(6)))

    block_txt = fonts["sm"].render(f"Блок {entity.get('block', 0)}", True, COLORS["text_dim"])
    block_w = block_txt.get_width() + config.sx(14)
    block_box = pygame.Rect(x + w - block_w - config.sx(8), y + config.sy(6), block_w, config.sy(22))
    pygame.draw.rect(screen, (10, 14, 22), block_box, border_radius=6)
    screen.blit(block_txt, (block_box.x + config.sx(7), block_box.y + config.sy(3)))
    if chip_hits is not None and entity.get("block", 0) > 0:
        from icons import BLOCK_DESC
        chip_hits.append((block_box, f"Блок {entity.get('block', 0)}", BLOCK_DESC))

    draw_hp_bar(screen, fonts, tx, y + config.sy(24), w - config.sx(72), entity["hp"], entity["max_hp"], h=config.sy(11))

    row_y = y + config.sy(40)
    if intent and intent_icon_fn:
        intent_txt = fonts["sm"].render(intent_label_fn(intent), True, intent_color_fn(intent))
        intent_w = min(intent_txt.get_width() + config.sx(28), w - config.sx(72))
        intent_box = pygame.Rect(tx, row_y, intent_w, config.sy(22))
        pygame.draw.rect(screen, (10, 14, 22), intent_box, border_radius=6)
        pygame.draw.rect(screen, intent_color_fn(intent), intent_box, 1, border_radius=6)
        intent_icon_fn(screen, intent_box.x + config.sx(4), intent_box.y + config.sy(2), config.sy(18), intent)
        screen.blit(intent_txt, (intent_box.x + config.sx(24), intent_box.y + config.sy(4)))
        if chip_hits is not None:
            from icons import INTENT_DESC
            kind = intent.get("intent", "")
            desc = INTENT_DESC.get(kind, intent_label_fn(intent))
            if next_intent and intent_label_fn:
                desc = f"{desc}  Следом: {intent_label_fn(next_intent)}."
            chip_hits.append((intent_box, intent_label_fn(intent), desc))
        row_y += config.sy(24)
        if next_intent and intent_label_fn:
            next_txt = fonts["sm"].render(f"→ {intent_label_fn(next_intent)}", True, COLORS["text_dim"])
            screen.blit(next_txt, (tx, row_y))
            row_y += config.sy(16)

    from icons import POWER_DESC, POWER_NAMES, STATUS_DESC, STATUS_NAMES
    sx_pos, sy_pos = tx, row_y
    for key, val in entity.get("powers", {}).items():
        if val <= 0:
            continue
        chip_txt = fonts["sm"].render(f"{POWER_NAMES.get(key, key)} {val}", True, COLORS["gold"])
        chip_rect = pygame.Rect(sx_pos, sy_pos, chip_txt.get_width() + config.sx(10), config.sy(16))
        if chip_rect.right > x + w - config.sx(8):
            break
        pygame.draw.rect(screen, (36, 28, 12), chip_rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["gold"], chip_rect, 1, border_radius=4)
        screen.blit(chip_txt, (sx_pos + config.sx(5), sy_pos + 1))
        if chip_hits is not None:
            chip_hits.append((chip_rect, POWER_NAMES.get(key, key), POWER_DESC.get(key, "")))
        sx_pos += chip_rect.width + config.sx(4)
    for key, val in entity.get("statuses", {}).items():
        if val <= 0:
            continue
        chip_txt = fonts["sm"].render(f"{STATUS_NAMES.get(key, key)} {val}", True, COLORS["text"])
        chip_rect = pygame.Rect(sx_pos, sy_pos, chip_txt.get_width() + config.sx(10), config.sy(16))
        if chip_rect.right > x + w - config.sx(8):
            break
        pygame.draw.rect(screen, (30, 38, 56), chip_rect, border_radius=4)
        screen.blit(chip_txt, (sx_pos + config.sx(5), sy_pos + 1))
        if chip_hits is not None:
            chip_hits.append((chip_rect, STATUS_NAMES.get(key, key), STATUS_DESC.get(key, "")))
        sx_pos += chip_rect.width + config.sx(4)

    return rect


def draw_combat_arena(screen, accent=None):
    accent = accent or COLORS["accent"]
    arena = COMBAT_LAYOUT["arena"]
    draw_panel(screen, arena, fill=(8, 12, 20), border=accent, radius=16, alpha=145, shadow=False)

    stage = pygame.Rect(arena.x + 14, arena.y + 72, arena.width - 28, arena.height - 84)
    for row in range(stage.height):
        t = row / max(1, stage.height - 1)
        c = lerp_color((16, 22, 34), (6, 10, 18), t)
        pygame.draw.line(screen, c, (stage.x, stage.y + row), (stage.right, stage.y + row))
    pygame.draw.rect(screen, lerp_color(accent, (0, 0, 0), 0.5), stage, 1, border_radius=12)

    floor_y = stage.bottom - 18
    for i, alpha in enumerate((28, 18, 10)):
        y = floor_y + i * 3
        pygame.draw.line(screen, (*accent, alpha), (stage.x + 24, y), (stage.right - 24, y), 1)

    hud_line = arena.y + 68
    pygame.draw.line(screen, (*COLORS["panel_border"], 70), (arena.x + 14, hud_line), (arena.right - 14, hud_line), 1)


def draw_hand_tray(screen, fonts, accent=None):
    tray = COMBAT_LAYOUT["hand"]
    content = draw_section_panel(screen, tray, "Рука", fonts, accent=accent or COLORS["accent"])
    return tray, content


def _log_line_color(line):
    low = line.lower()
    if any(w in low for w in ("урон", "бьёт", "наносит", "теряет", "крадёт", "получает урон")):
        return COLORS["danger"]
    if "блок" in low:
        return COLORS["accent"]
    if "яд" in low or "слабость" in low or "уязвим" in low:
        return COLORS["success"]
    if "леч" in low or ("hp" in low and "+" in line):
        return COLORS["gold"]
    if "сила" in low or "металл" in low:
        return COLORS["accent_warm"]
    return COLORS["text"]


def draw_combat_log(screen, fonts, lines, deck_count, discard_count, accent=None, offset=0, max_lines=8):
    log = COMBAT_LAYOUT["log"]
    content = draw_section_panel(screen, log, "Журнал боя", fonts, accent=accent or COLORS["panel_border"])
    piles_y = content.y + config.sy(2)
    deck_label = fonts["sm"].render(f"Колода {deck_count}", True, COLORS["accent"])
    discard_label = fonts["sm"].render(f"Сброс {discard_count}", True, COLORS["text_dim"])
    screen.blit(deck_label, (content.x, piles_y))
    screen.blit(discard_label, (content.x + deck_label.get_width() + config.sx(12), piles_y))
    deck_rect = pygame.Rect(content.x, piles_y - 2, deck_label.get_width() + config.sx(6), config.sy(18))
    discard_rect = pygame.Rect(content.x + deck_label.get_width() + config.sx(12), piles_y - 2, discard_label.get_width() + config.sx(6), config.sy(18))
    log_top = content.y + config.sy(24)
    if len(lines) > max_lines:
        scroll = fonts["sm"].render(f"↕ {offset + 1}-{min(offset + max_lines, len(lines))}/{len(lines)}", True, COLORS["text_dim"])
        screen.blit(scroll, (content.right - scroll.get_width() - config.sx(4), content.y + config.sy(2)))
    max_offset = max(0, len(lines) - max_lines)
    offset = max(0, min(offset, max_offset))
    visible = lines[offset:offset + max_lines]
    line_h = config.sy(18)
    for i, line in enumerate(visible):
        row_y = log_top + i * line_h
        if i % 2 == 0:
            row_bg = pygame.Rect(content.x - config.sx(4), row_y - 1, content.width + config.sx(8), line_h - 1)
            pygame.draw.rect(screen, (16, 20, 30), row_bg, border_radius=4)
        screen.blit(fonts["sm"].render(line, True, _log_line_color(line)), (content.x, row_y))
    scroll_rect = pygame.Rect(content.x, log_top, content.width, content.bottom - log_top)
    return log, deck_rect, discard_rect, scroll_rect


def draw_combat_chip_tooltip(screen, fonts, mouse, hits):
    for rect, title, desc in hits:
        if not rect.collidepoint(mouse) or not desc:
            continue
        tip_w = 248
        tip_h = 58 if len(desc) < 40 else 72
        tip = pygame.Rect(min(mouse[0] + 14, config.SCREEN_WIDTH - tip_w - 12), mouse[1] + 14, tip_w, tip_h)
        draw_panel(screen, tip, fill=(12, 16, 24), border=COLORS["accent"], radius=10, alpha=235, shadow=True)
        screen.blit(fonts["sm"].render(title, True, COLORS["text"]), (tip.x + 10, tip.y + 8))
        wrap_text(screen, fonts["sm"], desc, tip.x + 10, tip.y + 26, tip.width - 20, COLORS["text_dim"], line_h=15)
        return


def draw_card_grid_overlay(screen, fonts, title, cards, mouse, buttons, draw_type_icon, on_pick=None, on_close=None, accent=None, page=0, on_page=None):
    accent = accent or COLORS["accent"]
    dim = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 170))
    screen.blit(dim, (0, 0))

    panel = pygame.Rect(60, 70, config.SCREEN_WIDTH - 120, config.SCREEN_HEIGHT - 140)
    content = draw_section_panel(screen, panel, title, fonts, accent=accent, alpha=235)
    cw, ch, gap = 112, 118, 10
    cols = max(1, min(8, (content.width - 40) // (cw + gap)))
    rows = max(1, (len(cards) + cols - 1) // cols)
    visible_rows = min(rows, 3)
    grid_h = visible_rows * ch + (visible_rows - 1) * gap
    sx = content.x + max(16, (content.width - (cols * cw + (cols - 1) * gap)) // 2)
    sy = content.y + max(16, (content.height - grid_h - 52) // 2)

    limit = cols * visible_rows
    total_pages = max(1, (len(cards) + limit - 1) // limit)
    page = max(0, min(page, total_pages - 1))
    start = page * limit
    page_cards = cards[start:start + limit]
    hovered_card = None

    for i, card in enumerate(page_cards):
        col = i % cols
        row = i // cols
        x = sx + col * (cw + gap)
        y = sy + row * (ch + gap)
        hovered = pygame.Rect(x, y, cw, ch).collidepoint(mouse)
        if hovered:
            hovered_card = card
        rect = draw_card(screen, fonts, card, x, y, cw, ch, bool(on_pick), hovered, draw_type_icon)
        if on_pick:
            idx = start + i
            buttons.add(rect, lambda idx=idx: on_pick(idx))

    nav_y = content.bottom - 44
    if total_pages > 1:
        page_txt = fonts["sm"].render(f"Стр. {page + 1}/{total_pages}  ·  {len(cards)} карт", True, COLORS["text_dim"])
        screen.blit(page_txt, page_txt.get_rect(center=(content.centerx, nav_y + 10)))
        if page > 0 and on_page:
            draw_button(screen, fonts, pygame.Rect(content.x + 16, nav_y - 4, 120, 34), "← Назад", mouse, buttons, lambda: on_page(page - 1), primary=False)
        if page + 1 < total_pages and on_page:
            draw_button(screen, fonts, pygame.Rect(content.right - 136, nav_y - 4, 120, 34), "Далее →", mouse, buttons, lambda: on_page(page + 1), primary=False)
    elif len(cards) > limit:
        more = fonts["sm"].render(f"{len(cards)} карт", True, COLORS["text_dim"])
        screen.blit(more, (content.x + 16, nav_y))

    if on_close:
        close_rect = pygame.Rect(panel.centerx - 90, panel.bottom - 46, 180, 38)
        draw_button(screen, fonts, close_rect, "Закрыть", mouse, buttons, on_close, primary=False)
    return panel, hovered_card


def draw_upgrade_preview(screen, fonts, card, preview, x, y, draw_type_icon):
    panel = pygame.Rect(x, y, 280, 148)
    draw_panel(screen, panel, fill=(14, 18, 28), border=COLORS["accent_warm"], radius=12, alpha=245, shadow=True)
    screen.blit(fonts["sm"].render("После улучшения", True, COLORS["accent_warm"]), (panel.x + 12, panel.y + 10))
    screen.blit(fonts["md"].render(preview["name"], True, COLORS["gold"]), (panel.x + 12, panel.y + 34))
    draw_type_icon(screen, panel.x + 12, panel.y + 58, 20, preview["type"])
    cost = fonts["sm"].render(f"Стоимость: {preview['cost']}", True, COLORS["text_dim"])
    screen.blit(cost, (panel.x + 38, panel.y + 60))
    wrap_text(screen, fonts["sm"], preview["desc"], panel.x + 12, panel.y + 84, panel.width - 24, COLORS["text"], line_h=16)
    return panel


def position_upgrade_preview(card_rect, preview_w=280, preview_h=148):
    margin = config.sx(16)
    px = card_rect.right + margin
    py = card_rect.centery - preview_h // 2
    if px + preview_w > config.SCREEN_WIDTH - margin:
        px = card_rect.left - preview_w - margin
    if py + preview_h > config.SCREEN_HEIGHT - config.sy(58):
        py = config.SCREEN_HEIGHT - config.sy(58) - preview_h
    if py < config.sy(100):
        py = config.sy(100)
    if px < margin:
        px = margin
    if px + preview_w > config.SCREEN_WIDTH - margin:
        px = config.SCREEN_WIDTH - margin - preview_w
    return int(px), int(py)


def layout_hand_cards(hand_size):
    tray = COMBAT_LAYOUT["hand"]
    header = config.sy(36)
    pad_y = config.sy(6)
    content_h = max(config.sy(100), tray.height - header - pad_y)
    card_h = min(CARD_H, content_h)
    card_w = max(config.sx(96), int(CARD_W * card_h / max(1, CARD_H)))
    gap = max(config.sx(8), int(CARD_GAP * card_h / max(1, CARD_H)))
    total = hand_size * card_w + max(0, hand_size - 1) * gap
    sx = tray.x + max(config.sx(10), (tray.width - total) // 2)
    sy = tray.y + header + max(0, (content_h - card_h) // 2)
    return sx, sy, card_w, card_h, gap


def draw_actions_bar(screen, fonts, accent=None):
    bar = COMBAT_LAYOUT["actions"]
    draw_panel(screen, bar, fill=(12, 16, 26), border=accent or COLORS["panel_border"], radius=12, alpha=200, shadow=False)
    return pygame.Rect(bar.x + config.sx(12), bar.y + config.sy(8), bar.width - config.sx(24), bar.height - config.sy(14))


def draw_flying_card(screen, fonts, anim, target_pos, draw_type_icon):
    if not anim or not target_pos:
        return
    duration = max(1, anim["duration"])
    t = clamp(anim["progress"] / duration, 0, 1)
    ease = 1 - (1 - t) ** 2
    fx, fy = anim["from"]
    tx, ty = target_pos
    x = fx + (tx - fx) * ease
    y = fy + (ty - fy) * ease - math.sin(t * math.pi) * 52
    w, h = anim["size"]
    scale = 1.0 - t * 0.3
    cw, ch = max(40, int(w * scale)), max(52, int(h * scale))
    alpha = int(255 * (1 - t * 0.15))
    card_surf = pygame.Surface((cw + 8, ch + 8), pygame.SRCALPHA)
    draw_card(card_surf, fonts, anim["card"], 4, 4, cw, ch, True, False, draw_type_icon)
    card_surf.set_alpha(alpha)
    screen.blit(card_surf, (int(x - cw // 2 - 4), int(y - ch // 2 - 4)))


def draw_combat_fx(screen, fonts, fx_list, positions):
    for fx in fx_list:
        pos = positions.get(fx["target"])
        if not pos:
            continue
        bx, by = pos
        alpha = int(255 * clamp(fx["life"] / fx["max_life"], 0, 1))
        y = int(by - fx["y"] - (1 - fx["life"] / fx["max_life"]) * 18)
        x = bx + fx.get("offset_x", 0)
        outline = fonts["lg"].render(fx["text"], True, (0, 0, 0))
        outline.set_alpha(min(180, alpha))
        text = fonts["lg"].render(fx["text"], True, fx["color"])
        text.set_alpha(alpha)
        ox = x - text.get_width() // 2
        screen.blit(outline, (ox + 1, y + 1))
        screen.blit(text, (ox, y))


def draw_hit_pulse(screen, center, radius, strength, color):
    if strength <= 0:
        return
    t = strength / 16.0
    glow = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, int(50 * t)), (radius + 4, radius + 4), int(radius * (1 + (1 - t) * 0.2)))
    screen.blit(glow, (center[0] - radius - 4, center[1] - radius - 4))


def combat_shake_offset(combat, anim):
    if not combat or combat.shake <= 0:
        return 0, 0
    mag = combat.shake * 0.45
    return int(math.sin(anim * 18) * mag), int(math.cos(anim * 14) * mag)


def layout_action_buttons():
    bar = COMBAT_LAYOUT["actions"]
    bw = min(config.sx(180), max(config.sx(140), bar.width // 3))
    return pygame.Rect(bar.right - bw - config.sx(12), bar.y + config.sy(5), bw, bar.height - config.sy(10))


def draw_potion_bar(screen, fonts, potions, mouse, buttons, on_use, accent, used_this_turn=False, draw_icon=None, panel_rect=None):
    from potions import POTION_DEFS, POTION_MAX

    draw_icon = draw_icon or (lambda s, x, y, sz, pid: None)
    panel = panel_rect or COMBAT_LAYOUT.get("potions") or pygame.Rect(config.sx(16), config.sy(88), config.sx(300), config.sy(52))
    draw_panel(screen, panel, fill=(12, 16, 24), border=COLORS["panel_border"], radius=12, alpha=210, shadow=False)
    screen.blit(fonts["sm"].render(f"Зелья ({len(potions)}/{POTION_MAX})", True, accent), (panel.x + config.sx(12), panel.y + config.sy(8)))
    keys = ("Z", "X", "C")
    slot_x = panel.x + config.sx(12)
    slot_w = max(config.sx(72), (panel.width - config.sx(24) - config.sx(8) * 2) // 3)
    for i in range(POTION_MAX):
        slot = pygame.Rect(slot_x + i * (slot_w + config.sx(8)), panel.y + config.sy(24), slot_w, config.sy(22))
        if i < len(potions):
            pid = potions[i]
            info = POTION_DEFS.get(pid, {})
            hovered = slot.collidepoint(mouse)
            fill = lerp_color(info.get("color", accent), (255, 255, 255), 0.12 if hovered else 0.0)
            pygame.draw.rect(screen, fill, slot, border_radius=6)
            pygame.draw.rect(screen, info.get("color", accent), slot, 1, border_radius=6)
            draw_icon(screen, slot.x + 4, slot.y + 3, 16, pid)
            label = fonts["sm"].render(info.get("name", pid)[:9], True, COLORS["text"])
            screen.blit(label, (slot.x + 22, slot.y + 4))
            key = fonts["sm"].render(keys[i], True, COLORS["text_dim"])
            screen.blit(key, (slot.right - 14, slot.y - 12))
            if not used_this_turn and on_use:
                buttons.add(slot, lambda idx=i: on_use(idx), primary=False)
        else:
            pygame.draw.rect(screen, (24, 28, 36), slot, border_radius=6)
            pygame.draw.rect(screen, (48, 56, 72), slot, 1, border_radius=6)
    return panel


def layout_reward_cards(count):
    panel, sx, sy, cw, ch, gap, _cols = layout_card_grid(count, top=118, bottom_pad=58)
    return panel, sx, sy, cw, ch, gap


def layout_card_grid(count, top=118, bottom_pad=58, margin_x=40):
    """Card grid scaled to fill the screen between top bar and footer."""
    action_h = config.sy(52)
    panel_h = config.SCREEN_HEIGHT - top - bottom_pad - action_h
    panel = pygame.Rect(margin_x, top, config.SCREEN_WIDTH - margin_x * 2, max(config.sy(220), panel_h))
    inner_top = config.sy(44)
    avail_h = max(config.sy(120), panel.height - inner_top - config.sy(12))
    avail_w = max(config.sx(120), panel.width - config.sx(24))
    gap = config.sx(14)
    min_cw, min_ch = config.sx(96), config.sy(112)
    max_cw, max_ch = REWARD_CARD_W, REWARD_CARD_H

    if count <= 0:
        return panel, panel.x + config.sx(12), panel.y + inner_top, max_cw, max_ch, gap, 1

    best = None
    max_cols = min(count, 7)
    for cols in range(1, max_cols + 1):
        rows = (count + cols - 1) // cols
        cw = min(max_cw, (avail_w - (cols - 1) * gap) // cols)
        ch = min(max_ch, (avail_h - (rows - 1) * gap) // max(1, rows))
        cw = max(min_cw, cw)
        ch = max(min_ch, ch)
        total_w = cols * cw + (cols - 1) * gap
        total_h = rows * ch + (rows - 1) * gap
        if total_w <= avail_w and total_h <= avail_h:
            best = (cols, cw, ch, total_w, total_h)

    if best:
        cols, cw, ch, total_w, total_h = best
    else:
        cols = min(count, 5)
        cw = max(min_cw, min(max_cw, (avail_w - (cols - 1) * gap) // cols))
        rows = (count + cols - 1) // cols
        ch = max(min_ch, min(max_ch, (avail_h - (rows - 1) * gap) // max(1, rows)))
        total_w = cols * cw + (cols - 1) * gap
        total_h = rows * ch + (rows - 1) * gap

    sx = panel.x + max(config.sx(12), (panel.width - total_w) // 2)
    sy = panel.y + inner_top + max(0, (avail_h - total_h) // 2)
    return panel, sx, sy, cw, ch, gap, cols


def layout_shop_cards(count):
    panel = pygame.Rect(40, 108, config.SCREEN_WIDTH - 80, 410)
    cw, ch, gap = SHOP_CARD_W, SHOP_CARD_H, 28
    total = count * cw + max(0, count - 1) * gap
    sx = panel.x + max(24, (panel.width - total) // 2)
    sy = panel.y + 48
    return panel, sx, sy, cw, ch, gap


def _path_point(points, t):
    if not points:
        return (0, 0)
    if len(points) == 1:
        return points[0]
    segments = len(points) - 1
    seg = min(int(t * segments), segments - 1)
    local = t * segments - seg
    x1, y1 = points[seg]
    x2, y2 = points[seg + 1]
    return (int(x1 + (x2 - x1) * local), int(y1 + (y2 - y1) * local))


def draw_map_paths(screen, nodes, accent, anim=0.0, x_offset=0, y_offset=0):
    for a in nodes:
        for b in nodes:
            if b["id"] not in a["links"]:
                continue
            active = b["available"] and not b["visited"]
            col = accent if active else (48, 56, 72)
            width = 4 if active else 2
            ax, ay = a["x"] + x_offset, a["y"] + y_offset
            bx, by = b["x"] + x_offset, b["y"] + y_offset
            mx = (ax + bx) // 2
            my = (ay + by) // 2 - 12
            points = [(ax, ay), (mx, my), (bx, by)]
            if active:
                pygame.draw.lines(screen, lerp_color(accent, (0, 0, 0), 0.45), False, points, width + 2)
            pygame.draw.lines(screen, col, False, points, width)
            if active:
                for i, offset in enumerate((0.0, 0.33, 0.66)):
                    t = (offset + anim * 0.12 + i * 0.08) % 1.0
                    dot = _path_point(points, t)
                    pygame.draw.circle(screen, lerp_color(accent, (255, 255, 255), 0.35), dot, 5)
                    pygame.draw.circle(screen, accent, dot, 3)
                pygame.draw.circle(screen, accent, (bx, by), 5)
            elif a["visited"] and b["visited"]:
                mid = _path_point(points, 0.5)
                pygame.draw.circle(screen, lerp_color(col, accent, 0.25), mid, 3)


def draw_volume_slider(screen, fonts, rect, label, value, accent):
    screen.blit(fonts["sm"].render(label, True, COLORS["text_dim"]), (rect.x, rect.y))
    pct = fonts["md"].render(f"{int(value * 100)}%", True, accent)
    screen.blit(pct, (rect.right - pct.get_width(), rect.y))
    track = pygame.Rect(rect.x, rect.y + 24, rect.width, 10)
    pygame.draw.rect(screen, (20, 24, 34), track, border_radius=5)
    fill_w = max(10, int(track.width * value))
    for row in range(track.height):
        t = row / max(1, track.height - 1)
        c = lerp_color(accent, lerp_color(accent, (0, 0, 0), 0.35), t)
        pygame.draw.rect(screen, c, (track.x, track.y + row, fill_w, 1))
    pygame.draw.rect(screen, accent, track, 1, border_radius=5)
    knob_x = track.x + int(track.width * value)
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, track.centery), 8)
    pygame.draw.circle(screen, accent, (knob_x, track.centery), 6)
    return track.inflate(0, 16)


def draw_relic_tooltip(screen, fonts, mouse, hits):
    from relics import RELIC_DEFS

    for rect, rid in hits:
        if not rect.collidepoint(mouse):
            continue
        info = RELIC_DEFS.get(rid, {})
        tip_w = 240
        tip = pygame.Rect(min(mouse[0] + 14, config.SCREEN_WIDTH - tip_w - 12), mouse[1] + 14, tip_w, 52)
        draw_panel(screen, tip, fill=(12, 16, 24), border=info.get("color", COLORS["accent"]), radius=10, alpha=235, shadow=True)
        screen.blit(fonts["sm"].render(info.get("name", rid), True, info.get("color", COLORS["text"])), (tip.x + 10, tip.y + 8))
        screen.blit(fonts["sm"].render(info.get("desc", ""), True, COLORS["text_dim"]), (tip.x + 10, tip.y + 28))
        return


def draw_target_marker(screen, cx, cy, pulse, color):
    r = int(34 + math.sin(pulse * 2.2) * 5)
    ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(ring, (*color, 90), (r + 2, r + 2), r, 2)
    screen.blit(ring, (cx - r - 2, cy - r - 2))
    tri = [(cx, cy + 18), (cx - 8, cy + 32), (cx + 8, cy + 32)]
    pygame.draw.polygon(screen, color, tri)
    pygame.draw.polygon(screen, (255, 255, 255), tri, 1)


def draw_combat_relic_bar(screen, fonts, relics):
    from relics import draw_relic_icon

    if not relics:
        return []
    hits = []
    shown = min(len(relics), 8)
    hud = COMBAT_LAYOUT["hud"]
    start_x = hud.right - config.sx(16) - shown * config.sx(26)
    start_y = hud.y + config.sy(10)
    for i, rid in enumerate(relics[:8]):
        ix = start_x + i * config.sx(26)
        draw_relic_icon(screen, ix, start_y, config.sy(20), rid)
        hits.append((pygame.Rect(ix, start_y, config.sy(20), config.sy(20)), rid))
    if len(relics) > 8:
        extra = fonts["sm"].render(f"+{len(relics) - 8}", True, COLORS["text_dim"])
        ex = start_x - extra.get_width() - config.sx(6)
        screen.blit(extra, (ex, start_y + config.sy(2)))
        hits.append((pygame.Rect(ex, start_y, extra.get_width() + config.sx(4), config.sy(20)), "overflow"))
    return hits


def draw_relic_strip(screen, fonts, relics, x, y, max_count=6, size=28):
    from relics import RELIC_DEFS, draw_relic_icon

    hits = []
    for i, rid in enumerate(relics[:max_count]):
        ix = x + i * (size + 8)
        draw_relic_icon(screen, ix, y, size, rid)
        hits.append((pygame.Rect(ix, y, size, size), rid))
    if len(relics) > max_count:
        extra = fonts["sm"].render(f"+{len(relics) - max_count}", True, COLORS["text_dim"])
        screen.blit(extra, (x + max_count * (size + 8), y + size // 2 - 8))
    return hits


def draw_card_tooltip(screen, fonts, card, mouse, draw_type_icon, energy=None):
    tip_w, tip_h = 220, 168
    if energy is not None and card["cost"] > energy:
        tip_h = 186
    tx = min(mouse[0] + 16, config.SCREEN_WIDTH - tip_w - 12)
    ty = min(mouse[1] + 8, config.SCREEN_HEIGHT - tip_h - 12)
    if ty < 80:
        ty = mouse[1] + 16
    panel = pygame.Rect(tx, ty, tip_w, tip_h)
    base = COLORS.get(f"card_{card['type']}", COLORS["panel_border"])
    draw_panel(screen, panel, fill=(10, 14, 22), border=base, radius=12, alpha=240, shadow=True)
    draw_type_icon(screen, panel.x + 12, panel.y + 10, 22, card["type"])
    screen.blit(fonts["md"].render(card["name"], True, COLORS["text"]), (panel.x + 40, panel.y + 12))
    cost_color = COLORS["gold"] if energy is None or card["cost"] <= energy else COLORS["danger"]
    cost = fonts["sm"].render(f"Энергия: {card['cost']}", True, cost_color)
    screen.blit(cost, (panel.x + 12, panel.y + 38))
    if energy is not None and card["cost"] > energy:
        lack = fonts["sm"].render(f"Нужно {card['cost']}, есть {energy}", True, COLORS["danger"])
        screen.blit(lack, (panel.x + 12, panel.y + 54))
        desc_y = panel.y + 72
    else:
        desc_y = panel.y + 58
    wrap_text(screen, fonts["sm"], card["desc"], panel.x + 12, desc_y, panel.width - 24, COLORS["text_dim"], line_h=16)
    if card.get("upgraded"):
        up = fonts["sm"].render("Улучшено", True, COLORS["gold"])
        screen.blit(up, (panel.x + 12, panel.bottom - 22))


def draw_achievements_grid(screen, fonts, meta, accent=None):
    from achievements import ACHIEVEMENT_DEFS, achievement_progress

    accent = accent or COLORS["accent"]
    unlocked = set(meta.get("achievements", []))
    panel = pygame.Rect(80, 96, config.SCREEN_WIDTH - 160, 520)
    content = draw_section_panel(
        screen, panel,
        f"Достижения ({len(unlocked)}/{len(ACHIEVEMENT_DEFS)})",
        fonts, accent=accent, alpha=220,
    )
    cols = 2
    cw = (content.width - 24) // cols
    for i, (aid, info) in enumerate(ACHIEVEMENT_DEFS.items()):
        col = i % cols
        row = i // cols
        box = pygame.Rect(content.x + 12 + col * (cw + 8), content.y + 12 + row * 78, cw - 8, 70)
        done = aid in unlocked
        border = info["color"] if done else COLORS["panel_border"]
        draw_panel(screen, box, fill=(10, 14, 22), border=border, radius=10, alpha=220, shadow=False)
        icon = "★" if done else "○"
        screen.blit(fonts["md"].render(icon, True, info["color"] if done else COLORS["text_dim"]), (box.x + 12, box.y + 10))
        screen.blit(fonts["sm"].render(info["name"], True, info["color"] if done else COLORS["text_dim"]), (box.x + 36, box.y + 12))
        wrap_text(screen, fonts["sm"], info["desc"], box.x + 36, box.y + 32, box.width - 44, COLORS["text_dim"], line_h=15)
        if not done:
            progress = achievement_progress(meta, aid)
            if progress:
                prog = fonts["sm"].render(progress, True, COLORS["accent"])
                screen.blit(prog, (box.x + 36, box.bottom - 18))
    return content


def draw_relic_codex(screen, fonts, meta, mouse, buttons, accent=None):
    from relics import RELIC_DEFS, draw_relic_icon

    accent = accent or COLORS["gold"]
    found = set(meta.get("relics_found", []))
    panel = pygame.Rect(80, 96, config.SCREEN_WIDTH - 160, 520)
    content = draw_section_panel(
        screen, panel,
        f"Артефакты ({len(found)}/{len(RELIC_DEFS)})",
        fonts, accent=accent, alpha=220,
    )
    cols = 4
    cw, ch = (content.width - 56) // cols, 118
    ids = list(RELIC_DEFS.keys())
    hovered_info = None
    for i, rid in enumerate(ids):
        col = i % cols
        row = i // cols
        box = pygame.Rect(content.x + 16 + col * (cw + 8), content.y + 16 + row * (ch + 10), cw - 8, ch)
        known = rid in found
        info = RELIC_DEFS[rid]
        border = info["color"] if known else COLORS["panel_border"]
        draw_panel(screen, box, fill=(10, 14, 22), border=border, radius=12, alpha=220, shadow=False)
        if known:
            draw_relic_icon(screen, box.x + 14, box.y + 12, 36, rid)
            screen.blit(fonts["sm"].render(info["name"], True, info["color"]), (box.x + 58, box.y + 16))
            if info.get("boss"):
                tag = fonts["sm"].render("Босс", True, COLORS["gold"])
                screen.blit(tag, (box.right - tag.get_width() - 10, box.y + 14))
            wrap_text(screen, fonts["sm"], info["desc"], box.x + 58, box.y + 36, box.width - 66, COLORS["text_dim"], line_h=16)
        else:
            lock = pygame.Rect(box.x + 14, box.y + 12, 36, 36)
            draw_panel(screen, lock, fill=(8, 10, 16), border=COLORS["panel_border"], radius=18, alpha=200, shadow=False)
            q = fonts["md"].render("?", True, COLORS["text_dim"])
            screen.blit(q, q.get_rect(center=lock.center))
            screen.blit(fonts["sm"].render("Неизвестно", True, COLORS["text_dim"]), (box.x + 58, box.y + 24))
        if box.collidepoint(mouse) and known:
            hovered_info = info
    if hovered_info:
        tip = pygame.Rect(min(mouse[0] + 12, config.SCREEN_WIDTH - 260), mouse[1] + 12, 248, 52)
        draw_panel(screen, tip, fill=(12, 16, 24), border=hovered_info["color"], radius=10, alpha=235, shadow=True)
        screen.blit(fonts["sm"].render(hovered_info["name"], True, hovered_info["color"]), (tip.x + 10, tip.y + 8))
        screen.blit(fonts["sm"].render(hovered_info["desc"], True, COLORS["text_dim"]), (tip.x + 10, tip.y + 28))
    return content


RARITY_LABELS = {
    "starter": "Стартовая",
    "common": "Обычная",
    "uncommon": "Необычная",
    "rare": "Редкая",
}


def draw_codex_tabs(screen, fonts, mouse, buttons, active_tab, on_tab, accent=None):
    accent = accent or COLORS["gold"]
    tabs = [("relics", "Артефакты"), ("cards", "Карты"), ("potions", "Зелья")]
    tab_w, tab_h = 140, 36
    start_x = config.SCREEN_WIDTH // 2 - int(tab_w * 1.5) - 8
    y = 56
    for i, (tab_id, label) in enumerate(tabs):
        rect = pygame.Rect(start_x + i * (tab_w + 8), y, tab_w, tab_h)
        selected = tab_id == active_tab
        border = accent if selected else COLORS["panel_border"]
        fill = (18, 24, 36) if selected else (12, 16, 24)
        draw_panel(screen, rect, fill=fill, border=border, radius=10, alpha=230, shadow=False)
        color = accent if selected else COLORS["text_dim"]
        text = fonts["md"].render(label, True, color)
        screen.blit(text, text.get_rect(center=rect.center))
        if tab_id != active_tab:
            buttons.add(rect, lambda tid=tab_id: on_tab(tid), primary=False)


def draw_potion_codex(screen, fonts, meta, mouse, draw_icon, accent=None):
    from potions import POTION_DEFS

    accent = accent or COLORS["success"]
    found = set(meta.get("potions_found", []))
    panel = pygame.Rect(80, 96, config.SCREEN_WIDTH - 160, 520)
    content = draw_section_panel(
        screen, panel,
        f"Зелья ({len(found)}/{len(POTION_DEFS)})",
        fonts, accent=accent, alpha=220,
    )
    cols = 2
    cw = (content.width - 40) // cols
    ch = 88
    ids = list(POTION_DEFS.keys())
    for i, pid in enumerate(ids):
        col = i % cols
        row = i // cols
        x = content.x + 16 + col * (cw + 8)
        y = content.y + 16 + row * (ch + 10)
        slot = pygame.Rect(x, y, cw, ch)
        known = pid in found
        info = POTION_DEFS[pid]
        fill = (18, 24, 36) if known else (10, 12, 18)
        border = info.get("color", accent) if known else (48, 56, 72)
        draw_panel(screen, slot, fill=fill, border=border, radius=10, alpha=220 if known else 160, shadow=False)
        if known:
            draw_icon(screen, slot.x + 12, slot.y + 12, 28, pid)
            name = fonts["md"].render(info["name"], True, COLORS["text"])
            screen.blit(name, (slot.x + 48, slot.y + 12))
            desc = fonts["sm"].render(info["desc"], True, COLORS["text_dim"])
            screen.blit(desc, (slot.x + 48, slot.y + 38))
        else:
            q = fonts["md"].render("???", True, COLORS["text_dim"])
            screen.blit(q, q.get_rect(center=slot.center))


def draw_card_codex(screen, fonts, meta, mouse, draw_type_icon, accent=None):
    from cards import CARD_DEFS

    accent = accent or COLORS["accent"]
    found = set(meta.get("cards_found", []))
    panel = pygame.Rect(80, 96, config.SCREEN_WIDTH - 160, 520)
    content = draw_section_panel(
        screen, panel,
        f"Карты ({len(found)}/{len(CARD_DEFS)})",
        fonts, accent=accent, alpha=220,
    )
    cols = 3
    cw = (content.width - 40) // cols
    ch = 76
    ids = list(CARD_DEFS.keys())
    hovered_card = None
    for i, cid in enumerate(ids):
        col = i % cols
        row = i // cols
        box = pygame.Rect(content.x + 12 + col * (cw + 8), content.y + 12 + row * (ch + 8), cw - 8, ch)
        known = cid in found
        info = CARD_DEFS[cid]
        type_color = COLORS.get(f"card_{info['type']}", COLORS["panel_border"])
        border = type_color if known else COLORS["panel_border"]
        draw_panel(screen, box, fill=(10, 14, 22), border=border, radius=10, alpha=220, shadow=False)
        if known:
            draw_type_icon(screen, box.x + 12, box.y + 12, 28, info["type"])
            screen.blit(fonts["sm"].render(info["name"], True, COLORS["text"]), (box.x + 48, box.y + 12))
            rarity = RARITY_LABELS.get(info.get("rarity", "common"), info.get("rarity", ""))
            tag = fonts["sm"].render(rarity, True, COLORS["text_dim"])
            screen.blit(tag, (box.right - tag.get_width() - 12, box.y + 14))
            wrap_text(screen, fonts["sm"], info["desc"], box.x + 48, box.y + 34, box.width - 58, COLORS["text_dim"], line_h=15)
        else:
            lock = pygame.Rect(box.x + 12, box.y + 12, 28, 28)
            draw_panel(screen, lock, fill=(8, 10, 16), border=COLORS["panel_border"], radius=14, alpha=200, shadow=False)
            q = fonts["md"].render("?", True, COLORS["text_dim"])
            screen.blit(q, q.get_rect(center=lock.center))
            screen.blit(fonts["sm"].render("Неизвестно", True, COLORS["text_dim"]), (box.x + 48, box.y + 18))
        if box.collidepoint(mouse) and known:
            hovered_card = {**info, "id": cid}
    if hovered_card:
        draw_card_tooltip(screen, fonts, hovered_card, mouse, draw_type_icon)
    return content


def draw_achievement_toast(screen, fonts, ach_id, timer, max_timer=180, y_offset=0):
    from achievements import ACHIEVEMENT_DEFS

    info = ACHIEVEMENT_DEFS.get(ach_id)
    if not info:
        return
    progress = 1.0 - (timer / max_timer)
    slide = min(1.0, progress * 3.0)
    ease = 1.0 - (1.0 - slide) ** 3
    w, h = 340, 72
    x = config.SCREEN_WIDTH - w - 24 + int((1.0 - ease) * (w + 40))
    y = 88 + y_offset
    alpha = min(240, int(255 * min(1.0, timer / 30)))
    panel = pygame.Rect(x, y, w, h)
    draw_panel(screen, panel, fill=(14, 18, 28), border=info["color"], radius=12, alpha=alpha, shadow=True)
    screen.blit(fonts["md"].render("★ Достижение", True, info["color"]), (panel.x + 14, panel.y + 10))
    screen.blit(fonts["sm"].render(info["name"], True, COLORS["text"]), (panel.x + 14, panel.y + 32))
    screen.blit(fonts["sm"].render(info["desc"], True, COLORS["text_dim"]), (panel.x + 14, panel.y + 50))


def draw_map_node_tooltip(screen, fonts, mouse, label, accent=None, subtitle=None):
    accent = accent or COLORS["accent"]
    lines = [label]
    if subtitle:
        lines.append(subtitle)
    tip_w = max(160, max(fonts["sm"].size(line)[0] for line in lines) + 28)
    tip_h = 22 + len(lines) * 18
    tip = pygame.Rect(min(mouse[0] + 14, config.SCREEN_WIDTH - tip_w - 12), mouse[1] - tip_h - 4, tip_w, tip_h)
    draw_panel(screen, tip, fill=(12, 16, 24), border=accent, radius=8, alpha=235, shadow=True)
    for i, line in enumerate(lines):
        col = COLORS["text"] if i == 0 else COLORS["text_dim"]
        text = fonts["sm"].render(line, True, col)
        screen.blit(text, (tip.x + 12, tip.y + 6 + i * 18))


def draw_map_node(screen, x, y, node_type, color, active, visited, pulse, draw_node_icon, hovered=False):
    from sprites import draw_node_sprite

    r = 28
    if active:
        for i in range(3):
            phase = pulse * 1.4 + i * 1.8
            rr = int(r + 10 + i * 7 + math.sin(phase) * 4)
            alpha = max(10, 55 - i * 16)
            ring = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*color, alpha), (rr + 2, rr + 2), rr, 2)
            screen.blit(ring, (x - rr - 2, y - rr - 2))
        glow_r = int(r + 8 + math.sin(pulse * 1.2) * 4)
        glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 60), (glow_r + 2, glow_r + 2), glow_r)
        screen.blit(glow, (x - glow_r - 2, y - glow_r - 2))

    sprite_size = r * 2 - 4
    bob = int(math.sin(pulse * 1.6) * 2) if active else 0
    draw_node_sprite(screen, x - sprite_size // 2, y - sprite_size // 2 + bob, sprite_size, node_type)
    border = (255, 255, 255) if active else ((90, 94, 104) if visited else (60, 64, 74))
    if hovered and active:
        pygame.draw.circle(screen, (255, 255, 255), (x, y), r + 5, 2)
    pygame.draw.circle(screen, border, (x, y), r, 3 if active else 1)
    if node_type == "boss" and active:
        for i in range(4):
            ang = pulse * 0.8 + i * math.pi / 2
            sx = int(x + math.cos(ang) * (r + 10))
            sy = int(y + math.sin(ang) * (r + 10))
            pygame.draw.circle(screen, lerp_color(color, (255, 255, 255), 0.4), (sx, sy), 3)
    if visited:
        mark = pygame.Rect(x + r - 16, y - r + 2, 14, 14)
        pygame.draw.circle(screen, COLORS["success"], mark.center, 7)
        pygame.draw.circle(screen, (255, 255, 255), mark.center, 7, 1)
    if not active and not visited:
        dim = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 80))
        screen.blit(dim, (x - sprite_size // 2, y - sprite_size // 2 + bob))
    return pygame.Rect(x - r - 4, y - r - 4, (r + 4) * 2, (r + 4) * 2)


def load_fonts(scale=1.0):
    def sz(n):
        return max(10, int(n * scale))

    return {
        "hero": pygame.font.SysFont("segoeui", sz(42), bold=True),
        "title": pygame.font.SysFont("segoeui", sz(34), bold=True),
        "title_sm": pygame.font.SysFont("segoeui", sz(24), bold=True),
        "lg": pygame.font.SysFont("segoeui", sz(20), bold=True),
        "md": pygame.font.SysFont("segoeui", sz(16)),
        "sm": pygame.font.SysFont("segoeui", sz(14)),
        "card": pygame.font.SysFont("segoeui", sz(15), bold=True),
    }
