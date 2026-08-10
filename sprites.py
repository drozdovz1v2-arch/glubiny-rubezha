"""Процедурные спрайты премиум-уровня — рендер 2x + даунскейл для сглаживания."""

import math

import pygame

from config import COLORS

SPRITE_VER = 6
RENDER_SCALE = 3
CARD_RENDER_SCALE = 4


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _shade(color, amount):
    return _lerp(color, (255, 255, 255), amount) if amount > 0 else _lerp(color, (0, 0, 0), -amount)


def _rgba(color, alpha):
    return (*color[:3], alpha)


def _vgradient(surf, rect, top, bottom):
    x, y, w, h = rect
    for row in range(max(1, h)):
        t = row / max(1, h - 1)
        pygame.draw.line(surf, _lerp(top, bottom, t), (x, y + row), (x + w - 1, y + row))


def _hgradient(surf, rect, left, right):
    x, y, w, h = rect
    for col in range(max(1, w)):
        t = col / max(1, w - 1)
        c = _lerp(left, right, t)
        pygame.draw.line(surf, c, (x + col, y), (x + col, y + h - 1))


def _radial_glow(surf, cx, cy, radius, color, alpha=50):
    if radius <= 0:
        return
    for r in range(radius, 0, -2):
        a = max(1, int(alpha * (r / max(1, radius))))
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, a), (r, r), r)
        surf.blit(glow, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)


def _ground_shadow(surf, cx, cy, rx, ry, alpha=70):
    sh = pygame.Surface((rx * 2 + 10, ry * 2 + 6), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, alpha), sh.get_rect())
    surf.blit(sh, (cx - rx - 5, cy - ry))


def _sparkle(surf, x, y, color, size=3):
    pygame.draw.circle(surf, _shade(color, 0.4), (x, y), size)
    pygame.draw.line(surf, color, (x - size, y), (x + size, y), 1)
    pygame.draw.line(surf, color, (x, y - size), (x, y + size), 1)


def _poly(surf, pts, fill, outline=None, width=0):
    pygame.draw.polygon(surf, fill, pts, width)
    if outline and width:
        pygame.draw.polygon(surf, outline, pts, width)


def _metallic_plate(surf, rect, base, rim=None):
    rim = rim or _shade(base, -0.35)
    _vgradient(surf, rect, _shade(base, 0.22), _shade(base, -0.28))
    pygame.draw.rect(surf, _shade(base, 0.35), (rect.x + 2, rect.y + 2, max(2, rect.width // 3), max(2, rect.height // 4)), border_radius=3)
    pygame.draw.rect(surf, rim, rect, 2, border_radius=rect.height // 4)


def _rim_light(surf, pts, color, width=2):
    if len(pts) >= 2:
        for i in range(min(3, len(pts) - 1)):
            pygame.draw.line(surf, color, pts[i], pts[i + 1], width)


def _curve_chain(surf, points, color, width=4):
    if len(points) < 2:
        return
    pygame.draw.lines(surf, color, False, points, width)
    for p in points[::2]:
        pygame.draw.circle(surf, _shade(color, 0.15), p, max(2, width // 2))


class SpriteBank:
    def __init__(self):
        self._cache = {}

    def get(self, key, w, h, painter, scale=RENDER_SCALE):
        k = (SPRITE_VER, scale, key, w, h)
        if k not in self._cache:
            rw, rh = max(1, w * scale), max(1, h * scale)
            hi = pygame.Surface((rw, rh), pygame.SRCALPHA)
            painter(hi, rw, rh)
            surf = pygame.transform.smoothscale(hi, (max(1, w), max(1, h))) if (rw, rh) != (w, h) else hi
            self._cache[k] = surf
        return self._cache[k]

    def blit(self, screen, key, w, h, painter, x, y, scale=RENDER_SCALE):
        screen.blit(self.get(key, w, h, painter, scale), (x, y))


SPRITES = SpriteBank()


def _illustration_sky(s, w, h, sky_top, sky_bottom, ground_top=None, ground_bottom=None, horizon=0.62):
    _vgradient(s, (0, 0, w, h), sky_top, sky_bottom)
    hy = int(h * horizon)
    gt = ground_top or _shade(sky_bottom, -0.12)
    gb = ground_bottom or _shade(sky_bottom, -0.35)
    _vgradient(s, (0, hy, w, h - hy), gt, gb)
    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(0, max(w, h) // 3, 2):
        pygame.draw.rect(vignette, (0, 0, 0, int(6 + i * 0.4)), (i // 2, i // 2, w - i, h - i), 1, border_radius=5)
    s.blit(vignette, (0, 0))


def _impact_sparks(s, cx, cy, size):
    for i in range(10):
        ang = i * math.pi / 5 + 0.2
        dist = size * (0.5 + (i % 3) * 0.2)
        x2 = int(cx + math.cos(ang) * dist)
        y2 = int(cy + math.sin(ang) * dist)
        col = (255, 220, 160) if i % 2 else (255, 140, 120)
        pygame.draw.line(s, col, (cx, cy), (x2, y2), max(1, int(size * 0.08)))


def _draw_card_knight(s, cx, cy, sc, pose="slash", heavy=False):
    _ground_shadow(s, cx, cy + sc * 0.18, int(sc * 0.22), int(sc * 0.05), 55)
    cape = [(cx - sc * 0.22, cy - sc * 0.02), (cx - sc * 0.28, cy + sc * 0.2), (cx - sc * 0.04, cy + sc * 0.14), (cx + sc * 0.02, cy + sc * 0.02)]
    _poly(s, cape, (24, 34, 48))
    leg_l = pygame.Rect(cx - sc * 0.1, cy + sc * 0.06, sc * 0.08, sc * 0.14)
    leg_r = pygame.Rect(cx + sc * 0.02, cy + sc * 0.06, sc * 0.08, sc * 0.14)
    _vgradient(s, leg_l, (40, 48, 62), (24, 28, 36))
    _vgradient(s, leg_r, (40, 48, 62), (24, 28, 36))
    torso = pygame.Rect(cx - sc * 0.14, cy - sc * 0.08, sc * 0.28, sc * 0.18)
    _metallic_plate(s, torso, _shade(COLORS["accent"], -0.2))
    head_y = int(cy - sc * 0.14)
    helm = pygame.Rect(cx - sc * 0.1, head_y - sc * 0.1, sc * 0.2, sc * 0.12)
    _metallic_plate(s, helm, (150, 160, 175), (70, 78, 92))
    pygame.draw.rect(s, COLORS["accent"], (cx - sc * 0.06, head_y - sc * 0.02, sc * 0.12, sc * 0.03), border_radius=2)
    if pose == "block":
        shield = [(cx + sc * 0.08, cy - sc * 0.16), (cx + sc * 0.28, cy - sc * 0.04), (cx + sc * 0.24, cy + sc * 0.14), (cx + sc * 0.06, cy + sc * 0.1)]
        _poly(s, shield, (95, 130, 185))
        _poly(s, shield, (150, 190, 240), width=max(1, int(sc * 0.02)))
        _poly(s, [(cx + sc * 0.14, cy - sc * 0.06), (cx + sc * 0.2, cy + sc * 0.02), (cx + sc * 0.14, cy + sc * 0.06), (cx + sc * 0.08, cy + sc * 0.02)], COLORS["accent"])
        _radial_glow(s, cx + sc * 0.18, cy, int(sc * 0.12), (120, 180, 255), 30)
    else:
        _poly(s, [(cx + sc * 0.06, cy - sc * 0.04), (cx + sc * 0.14, cy - sc * 0.02), (cx + sc * 0.1, cy + sc * 0.06)], _shade(COLORS["accent"], -0.1))
        blade_len = sc * (1.05 if heavy else 0.88)
        tip_x, tip_y = cx + blade_len, cy - sc * 0.35
        _poly(s, [(cx + sc * 0.1, cy - sc * 0.02), (tip_x, tip_y), (cx + sc * 0.16, cy + sc * 0.02)], (220, 228, 240))
        pygame.draw.line(s, COLORS["accent"], (cx + sc * 0.1, cy), (tip_x - sc * 0.05, tip_y + sc * 0.05), max(1, int(sc * 0.03)))
        hilt = pygame.Rect(cx + sc * 0.04, cy - sc * 0.01, sc * 0.08, sc * 0.05)
        _metallic_plate(s, hilt, (90, 60, 30))


def _card_frame(s, w, h, top, bottom):
    _illustration_sky(s, w, h, top, bottom)


# --- ПЕРСОНАЖИ ---

def _paint_player(surf, w, h):
    cx, cy = w // 2, h // 2 + h * 0.04
    s = min(w, h) * 0.44
    _ground_shadow(surf, cx, cy + s * 0.74, int(s * 0.58), int(s * 0.13), 75)

    cape_outer = [(cx - s * 0.58, cy - s * 0.02), (cx - s * 0.82, cy + s * 0.72), (cx - s * 0.12, cy + s * 0.5), (cx + s * 0.06, cy + s * 0.12)]
    cape_inner = [(cx - s * 0.5, cy + s * 0.02), (cx - s * 0.68, cy + s * 0.58), (cx - s * 0.16, cy + s * 0.42)]
    _poly(surf, cape_outer, (22, 32, 48))
    _poly(surf, cape_inner, _shade(COLORS["accent"], -0.55))
    _rim_light(surf, cape_outer[:3], _rgba(COLORS["accent"], 80))

    for lx, rx in [(-0.22, -0.04), (0.04, 0.22)]:
        leg = pygame.Rect(cx + s * lx, cy + s * 0.34, s * 0.18, s * 0.4)
        _vgradient(surf, leg, (42, 50, 66), (24, 28, 38))
        boot = pygame.Rect(leg.x - s * 0.02, leg.bottom - s * 0.1, leg.width + s * 0.04, s * 0.1)
        _metallic_plate(surf, boot, (58, 48, 36))

    body = pygame.Rect(cx - s * 0.36, cy - s * 0.1, s * 0.72, s * 0.54)
    _metallic_plate(surf, body, _shade(COLORS["accent"], -0.25), _shade(COLORS["accent"], -0.5))
    pygame.draw.line(surf, _shade(COLORS["accent"], 0.4), (cx, cy - s * 0.06), (cx, cy + s * 0.4), 2)
    belt = pygame.Rect(body.x + s * 0.06, body.y + s * 0.28, body.width - s * 0.12, s * 0.08)
    _hgradient(surf, belt, (70, 52, 28), (110, 85, 40))
    pygame.draw.circle(surf, COLORS["gold"], (cx, belt.centery), int(s * 0.045))

    for side in (-1, 1):
        pad = pygame.Rect(cx + side * s * 0.34 - s * 0.1, cy - s * 0.08, s * 0.2, s * 0.2)
        _metallic_plate(surf, pad, _shade(COLORS["accent"], -0.05))

    head_y = int(cy - s * 0.3)
    pygame.draw.circle(surf, (205, 175, 135), (cx, head_y), int(s * 0.17))
    helm = pygame.Rect(cx - s * 0.24, head_y - s * 0.24, s * 0.48, s * 0.3)
    _metallic_plate(surf, helm, (155, 165, 180), (70, 78, 92))
    visor = pygame.Rect(cx - s * 0.14, head_y - s * 0.05, s * 0.28, s * 0.07)
    pygame.draw.rect(surf, (12, 18, 28), visor, border_radius=3)
    _radial_glow(surf, cx, visor.centery, int(s * 0.12), COLORS["accent"], 30)
    pygame.draw.rect(surf, COLORS["accent"], visor, 1, border_radius=3)
    crest = [(cx, head_y - s * 0.28), (cx - s * 0.08, head_y - s * 0.14), (cx + s * 0.08, head_y - s * 0.14)]
    _poly(surf, crest, _shade(COLORS["accent"], 0.05))

    shield_pts = [(cx - s * 0.66, cy + s * 0.04), (cx - s * 0.5, cy - s * 0.2), (cx - s * 0.32, cy + s * 0.04), (cx - s * 0.5, cy + s * 0.3)]
    _poly(surf, shield_pts, (105, 115, 132))
    _poly(surf, shield_pts, _shade(COLORS["accent"], -0.15), width=2)
    _poly(surf, [(cx - s * 0.54, cy - s * 0.06), (cx - s * 0.46, cy + s * 0.02), (cx - s * 0.54, cy + s * 0.1), (cx - s * 0.62, cy + s * 0.02)], COLORS["accent"])
    _radial_glow(surf, int(cx - s * 0.5), int(cy + s * 0.02), int(s * 0.08), COLORS["accent"], 25)

    sx, sy = cx + s * 0.2, cy - s * 0.06
    _radial_glow(surf, int(cx + s * 0.78), int(cy - s * 0.08), int(s * 0.28), COLORS["accent"], 40)
    blade = [(sx, sy), (cx + s * 1.0, cy - s * 0.38), (cx + s * 0.92, cy - s * 0.18), (sx + s * 0.06, sy + s * 0.06)]
    _poly(surf, blade, (225, 232, 242))
    _poly(surf, [(sx, sy), (cx + s * 0.58, cy - s * 0.24), (cx + s * 0.52, cy - s * 0.14), (sx + s * 0.04, sy + s * 0.02)], (170, 180, 195))
    pygame.draw.line(surf, COLORS["accent"], (sx, sy + s * 0.02), (cx + s * 0.92, cy - s * 0.22), 3)
    hilt = pygame.Rect(sx - s * 0.02, sy + s * 0.02, s * 0.14, s * 0.1)
    _metallic_plate(surf, hilt, (95, 62, 32))
    pommel = pygame.Rect(hilt.centerx - s * 0.04, hilt.bottom - s * 0.02, s * 0.08, s * 0.06)
    pygame.draw.ellipse(surf, COLORS["gold"], pommel)
    _sparkle(surf, int(cx + s * 0.86), int(cy - s * 0.3), (255, 255, 255), max(3, int(s * 0.05)))


def _paint_slime(surf, w, h, color, frost=False):
    cx, cy = w // 2, h // 2 + h * 0.05
    s = min(w, h) * 0.43
    _ground_shadow(surf, cx, cy + s * 0.48, int(s * 0.8), int(s * 0.15), 60)

    puddle = pygame.Rect(cx - s * 1.1, cy + s * 0.05, s * 2.2, s * 0.35)
    pygame.draw.ellipse(surf, _rgba(_shade(color, -0.45), 120), puddle)

    layers = [
        (_shade(color, -0.35), 1.05, 0.38, 1.08),
        (color, 0.92, 0.58, 0.98),
        (_shade(color, 0.12), 0.68, 0.64, 0.58),
        (_rgba(_shade(color, 0.35), 90), 0.42, 0.48, 0.35),
    ]
    for col, wx, hy, oy in layers:
        rect = (cx - s * wx, cy - s * hy + s * oy, s * wx * 2, s * hy)
        if len(col) == 4:
            blob = pygame.Surface((int(s * wx * 2 + 2), int(s * hy + 2)), pygame.SRCALPHA)
            pygame.draw.ellipse(blob, col, blob.get_rect())
            surf.blit(blob, (int(cx - s * wx), int(cy - s * hy + s * oy)))
        else:
            pygame.draw.ellipse(surf, col, rect)

    for dx, dy, r in [(-0.38, -0.18, 0.15), (-0.02, -0.26, 0.11), (0.3, -0.1, 0.09), (-0.15, 0.08, 0.06)]:
        hx, hy = int(cx + s * dx), int(cy + s * dy)
        pygame.draw.circle(surf, (255, 255, 255), (hx, hy), max(2, int(s * r)))
        pygame.draw.circle(surf, _rgba(_shade(color, 0.5), 100), (hx + 2, hy + 2), max(1, int(s * r * 0.4)))

    eye_y = int(cy - s * 0.04)
    for ex, pupil in ((-0.2, -1), (0.14, 1)):
        px = int(cx + s * ex)
        pygame.draw.ellipse(surf, (14, 20, 30), (px - 6, eye_y - 5, 12, 14))
        pygame.draw.circle(surf, (255, 255, 255), (px + pupil, eye_y - 1), 3)
        pygame.draw.circle(surf, (10, 14, 20), (px + pupil + 1, eye_y), 2)

    for drip_x in (-0.55, -0.2, 0.25, 0.55):
        dx = int(cx + s * drip_x)
        pygame.draw.line(surf, _shade(color, -0.15), (dx, int(cy + s * 0.35)), (dx + (2 if drip_x > 0 else -2), int(cy + s * 0.52)), 3)

    if frost:
        for i in range(8):
            ang = i * 0.78
            ix = int(cx + math.cos(ang) * s * 0.88)
            iy = int(cy - s * 0.32 + math.sin(ang) * s * 0.38)
            crystal = [(ix, iy - 8), (ix + 4, iy + 2), (ix, iy + 6), (ix - 4, iy + 2)]
            _poly(surf, crystal, (220, 245, 255))
            _poly(surf, crystal, (160, 200, 230), width=1)
        _radial_glow(surf, cx, cy - s * 0.12, int(s * 0.4), (190, 230, 255), 28)
    else:
        for bx, by in [(-0.42, 0.12), (0.35, 0.18)]:
            pygame.draw.circle(surf, _rgba(_shade(color, 0.4), 80), (int(cx + s * bx), int(cy + s * by)), int(s * 0.07))


def _paint_wolf(surf, w, h, color):
    cx, cy = w // 2, h // 2 + h * 0.04
    s = min(w, h) * 0.41
    _ground_shadow(surf, cx, cy + s * 0.58, int(s * 0.75), int(s * 0.13), 65)

    dark = _shade(color, -0.3)
    mid = color
    light = _shade(color, 0.12)

    body_dark = [(cx - s, cy + s * 0.28), (cx + s * 0.78, cy + s * 0.38), (cx + s * 0.58, cy - s * 0.02), (cx - s * 0.12, cy - s * 0.12)]
    body_mid = [(cx - s * 0.78, cy + s * 0.18), (cx + s * 0.58, cy + s * 0.25), (cx + s * 0.38, cy + s * 0.02), (cx - s * 0.02, cy - s * 0.06)]
    _poly(surf, body_dark, dark)
    _poly(surf, body_mid, mid)
    _rim_light(surf, body_mid[:3], light)

    tail_pts = [(cx - s * 0.95, cy + s * 0.18), (cx - s * 1.28, cy - s * 0.18), (cx - s * 1.05, cy - s * 0.32), (cx - s * 0.72, cy + s * 0.02)]
    _poly(surf, tail_pts, dark)
    _poly(surf, tail_pts[:3], mid)

    head = [(cx + s * 0.12, cy - s * 0.06), (cx + s * 0.74, cy + s * 0.1), (cx + s * 0.58, cy + s * 0.3), (cx + s * 0.02, cy + s * 0.2)]
    _poly(surf, head, mid)
    jaw = [(cx + s * 0.42, cy + s * 0.12), (cx + s * 0.95, cy + s * 0.16), (cx + s * 0.68, cy + s * 0.28), (cx + s * 0.38, cy + s * 0.24)]
    _poly(surf, jaw, _shade(mid, -0.12))
    nose = (int(cx + s * 0.88), int(cy + s * 0.17))
    pygame.draw.circle(surf, (18, 18, 22), nose, max(3, int(s * 0.035)))

    for ear_pts in [
        [(cx + s * 0.16, cy - s * 0.1), (cx + s * 0.06, cy - s * 0.58), (cx + s * 0.3, cy - s * 0.16)],
        [(cx + s * 0.34, cy - s * 0.08), (cx + s * 0.42, cy - s * 0.52), (cx + s * 0.5, cy - s * 0.1)],
    ]:
        _poly(surf, ear_pts, dark)
        inner = [(ear_pts[0][0] + 4, ear_pts[0][1] + 2), (ear_pts[1][0], ear_pts[1][1] + 10), (ear_pts[2][0] - 2, ear_pts[2][1])]
        _poly(surf, inner, _shade(mid, -0.05))

    eye = (int(cx + s * 0.5), int(cy + s * 0.04))
    _radial_glow(surf, eye[0], eye[1], 10, (255, 50, 50), 50)
    pygame.draw.circle(surf, (255, 60, 60), eye, 5)
    pygame.draw.circle(surf, (255, 200, 200), (eye[0] + 1, eye[1] - 1), 2)

    for i in range(4):
        lx = int(cx - s * 0.58 + i * s * 0.2)
        pygame.draw.line(surf, dark, (lx, cy + s * 0.2), (lx - 5, cy + s * 0.42), 3)
        pygame.draw.line(surf, mid, (lx + 1, cy + s * 0.22), (lx - 3, cy + s * 0.38), 1)


def _paint_scorpion(surf, w, h, color):
    cx, cy = w // 2, h // 2 + h * 0.02
    s = min(w, h) * 0.39
    _ground_shadow(surf, cx, cy + s * 0.52, int(s * 0.7), int(s * 0.12), 60)

    dark = _shade(color, -0.35)
    for i in range(5):
        seg_x = cx - s * 0.42 + i * s * 0.16
        seg = pygame.Rect(seg_x - s * 0.12, cy - s * 0.2, s * 0.24, s * 0.38)
        _vgradient(surf, seg, color if i % 2 == 0 else _shade(color, -0.08), dark)
        pygame.draw.ellipse(surf, _shade(color, 0.1), (seg_x - s * 0.08, cy - s * 0.12, s * 0.16, s * 0.12))

    for side in (-1, 1):
        for i in range(3):
            root_x = cx + side * s * (0.06 + i * 0.06)
            root_y = cy + s * 0.06 + i * 5
            knee_x = root_x + side * s * 0.18
            knee_y = root_y + s * 0.08
            foot_x = knee_x + side * s * 0.18
            foot_y = knee_y + s * 0.12
            _curve_chain(surf, [(root_x, root_y), (knee_x, knee_y), (foot_x, foot_y)], dark, 3)

    claw_base = cx + s * 0.28
    for claw, sign in [(cy - s * 0.08, -1), (cy + s * 0.1, 1)]:
        p1 = (claw_base, claw)
        p2 = (claw_base + s * 0.32, claw + sign * s * 0.18)
        p3 = (claw_base + s * 0.24, claw + sign * s * 0.04)
        tip = (claw_base + s * 0.38, claw + sign * s * 0.06)
        _poly(surf, [p1, p2, p3], _shade(color, 0.08))
        _poly(surf, [p3, tip, (p3[0] + 4, p3[1] + sign * 6)], (190, 170, 120))

    tail_pts = []
    for t in range(10):
        tx = cx - s * 0.25 + t * s * 0.11
        ty = cy - s * 0.28 - math.sin(t * 0.55) * s * 0.42
        tail_pts.append((tx, ty))
    _curve_chain(surf, tail_pts, dark, 6)
    _curve_chain(surf, tail_pts, _shade(color, -0.05), 3)
    tip = tail_pts[-1]
    _radial_glow(surf, int(tip[0]), int(tip[1]), 12, (255, 220, 80), 60)
    pygame.draw.circle(surf, (255, 240, 120), (int(tip[0]), int(tip[1])), 6)
    _sparkle(surf, int(tip[0]), int(tip[1]), (255, 255, 200), 4)


def _paint_wraith(surf, w, h, color):
    cx, cy = w // 2, h // 2
    s = min(w, h) * 0.45
    _radial_glow(surf, cx, cy, int(s * 0.6), color, 32)

    for scale, alpha, tint in [(1.0, 55, -0.4), (0.88, 85, -0.2), (0.76, 115, 0.0), (0.64, 150, 0.15)]:
        layer = pygame.Surface((w, h), pygame.SRCALPHA)
        pts = [(cx, cy - s * scale), (cx + s * 0.64 * scale, cy + s * 0.18 * scale), (cx + s * 0.24 * scale, cy + s * 0.58 * scale),
               (cx - s * 0.24 * scale, cy + s * 0.58 * scale), (cx - s * 0.64 * scale, cy + s * 0.18 * scale)]
        pygame.draw.polygon(layer, (*_shade(color, tint), alpha), pts)
        for i in range(5):
            fx = int(cx - s * 0.45 * scale + i * s * 0.22 * scale)
            fy = int(cy + s * 0.42 * scale + (i % 2) * 8)
            pygame.draw.circle(layer, (*_shade(color, 0.2), alpha // 2), (fx, fy), 4)
        surf.blit(layer, (0, 0))

    hood = [(cx, cy - s * 0.58), (cx + s * 0.38, cy - s * 0.02), (cx - s * 0.38, cy - s * 0.02)]
    _poly(surf, hood, _shade(color, -0.25))
    void = pygame.Rect(cx - s * 0.18, cy - s * 0.28, s * 0.36, s * 0.22)
    pygame.draw.ellipse(surf, (8, 6, 16), void)
    for ex in (-0.1, 0.1):
        px = int(cx + s * ex)
        _radial_glow(surf, px, int(cy - s * 0.16), 10, (230, 210, 255), 45)
        pygame.draw.circle(surf, (240, 220, 255), (px, int(cy - s * 0.16)), 6)
        pygame.draw.circle(surf, (255, 255, 255), (px + 1, int(cy - s * 0.17)), 2)


def _paint_colossus(surf, w, h, color, crowned=False):
    cx, cy = w // 2, h // 2 + h * 0.04
    s = min(w, h) * 0.43
    _ground_shadow(surf, cx, cy + s * 0.58, int(s * 0.85), int(s * 0.15), 70)

    body = pygame.Rect(cx - s * 0.58, cy - s * 0.48, s * 1.16, s * 1.0)
    _metallic_plate(surf, body, _shade(color, -0.05), _shade(color, -0.45))

    for row in range(4):
        for col in range(3):
            bx = int(body.x + s * 0.08 + col * s * 0.32)
            by = int(body.y + s * 0.08 + row * s * 0.2)
            brick = pygame.Rect(bx, by, int(s * 0.24), int(s * 0.14))
            shade = -0.12 if (row + col) % 2 else -0.28
            _vgradient(surf, brick, _shade(color, shade + 0.08), _shade(color, shade - 0.12))
            pygame.draw.rect(surf, _shade(color, -0.45), brick, 1, border_radius=2)

    for crack in [((cx - s * 0.2, cy - s * 0.1), (cx + s * 0.05, cy + s * 0.18)), ((cx + s * 0.15, cy - s * 0.15), (cx + s * 0.35, cy + s * 0.1))]:
        pygame.draw.line(surf, (35, 25, 15), crack[0], crack[1], 2)

    shoulders = [pygame.Rect(body.x - s * 0.08, body.y + s * 0.05, s * 0.22, s * 0.18), pygame.Rect(body.right - s * 0.14, body.y + s * 0.05, s * 0.22, s * 0.18)]
    for sh in shoulders:
        _metallic_plate(surf, sh, _shade(color, 0.05))

    _radial_glow(surf, cx, cy + s * 0.02, int(s * 0.14), (255, 220, 120), 40)
    pygame.draw.circle(surf, (255, 215, 90), (cx, cy + s * 0.02), int(s * 0.09))
    pygame.draw.circle(surf, (255, 240, 180), (cx - 2, cy + s * 0.02 - 2), int(s * 0.035))

    if crowned:
        crown_pts = [(cx - s * 0.22, cy - s * 0.42), (cx - s * 0.14, cy - s * 0.68), (cx - s * 0.04, cy - s * 0.5), (cx + s * 0.06, cy - s * 0.72), (cx + s * 0.16, cy - s * 0.52), (cx + s * 0.24, cy - s * 0.42)]
        _poly(surf, crown_pts, COLORS["gold"])
        _poly(surf, crown_pts, _shade(COLORS["gold"], -0.25), width=2)
        for i in range(3):
            _sparkle(surf, int(cx - s * 0.1 + i * s * 0.1), int(cy - s * 0.58), COLORS["gold"], 3)


def _paint_blue_boss(surf, w, h):
    cx, cy = w // 2, h // 2 + h * 0.02
    s = min(w, h) * 0.43
    _ground_shadow(surf, cx, cy + s * 0.6, int(s * 0.58), int(s * 0.13), 75)
    _radial_glow(surf, cx, cy, int(s * 0.55), (68, 136, 255), 30)

    robe = pygame.Rect(cx - s * 0.44, cy - s * 0.38, s * 0.88, s * 1.0)
    _vgradient(surf, robe, (55, 95, 195), (12, 18, 42))
    pygame.draw.rect(surf, (130, 175, 255), robe, 2, border_radius=14)
    for fold_x in (-0.22, 0.0, 0.22):
        pygame.draw.line(surf, _rgba((30, 50, 100), 120), (cx + s * fold_x, robe.top + s * 0.1), (cx + s * fold_x, robe.bottom - s * 0.08), 2)

    for horn_x in (-0.3, 0.3):
        hx = int(cx + s * horn_x)
        horn = [(hx, cy - s * 0.38), (hx - 8, cy - s * 0.68), (hx + 8, cy - s * 0.68)]
        _poly(surf, horn, (190, 200, 220))
        _poly(surf, horn, (120, 130, 150), width=2)

    mask = pygame.Rect(cx - s * 0.3, cy - s * 0.24, s * 0.6, s * 0.34)
    _metallic_plate(surf, mask, (95, 145, 245), (40, 70, 140))
    for ex in (-0.15, 0.15):
        px = int(cx + s * ex)
        _radial_glow(surf, px, int(cy - s * 0.08), 9, (140, 210, 255), 55)
        pygame.draw.circle(surf, (200, 235, 255), (px, int(cy - s * 0.08)), 6)
        pygame.draw.circle(surf, (255, 255, 255), (px + 1, int(cy - s * 0.09)), 2)

    for i in range(4):
        sx = int(cx - s * 0.38 + i * s * 0.22)
        sy = int(cy + s * 0.18)
        pygame.draw.line(surf, (160, 210, 255), (sx, sy), (sx + 10, sy - 16), 3)
        _sparkle(surf, sx + 10, sy - 16, (180, 220, 255), 2)


def _paint_ice_guardian(surf, w, h):
    cx, cy = w // 2, h // 2 + h * 0.03
    s = min(w, h) * 0.43
    _ground_shadow(surf, cx, cy + s * 0.58, int(s * 0.62), int(s * 0.13), 65)
    _radial_glow(surf, cx, cy, int(s * 0.52), (168, 216, 240), 35)

    core = pygame.Rect(cx - s * 0.38, cy - s * 0.32, s * 0.76, s * 0.9)
    _vgradient(surf, core, (225, 245, 255), (95, 150, 195))
    pygame.draw.rect(surf, (250, 255, 255), core, 2, border_radius=12)
    _hgradient(surf, (core.x + 4, core.y + 4, core.width // 2, core.height - 8), _rgba((255, 255, 255), 0), _rgba((255, 255, 255), 60))

    for i in range(8):
        ang = i * math.pi / 4 - 0.2
        dist = s * 0.58
        ox = int(cx + math.cos(ang) * dist)
        oy = int(cy + math.sin(ang) * dist * 0.85)
        size = 12 if i % 2 == 0 else 9
        crystal = [(ox, oy - size), (ox + size * 0.45, oy + size * 0.35), (ox - size * 0.45, oy + size * 0.35)]
        _poly(surf, crystal, (215, 240, 255))
        _poly(surf, crystal, (150, 190, 230), width=1)
        _hgradient(surf, pygame.Rect(ox - size // 2, oy - size, size, size + 4), _rgba((255, 255, 255), 80), _rgba((200, 230, 255), 0))

    _radial_glow(surf, cx, int(cy - s * 0.06), 12, (255, 255, 255), 45)
    pygame.draw.circle(surf, (255, 255, 255), (cx, int(cy - s * 0.06)), 7)
    for i in range(6):
        px = int(cx - s * 0.42 + i * s * 0.16)
        pygame.draw.circle(surf, _rgba((210, 235, 255), 140), (px, int(cy + s * 0.38)), 3)


ENEMY_PAINTERS = {
    "slime": lambda s, w, h: _paint_slime(s, w, h, (78, 205, 196)),
    "frost_slime": lambda s, w, h: _paint_slime(s, w, h, (122, 184, 216), frost=True),
    "wolf": lambda s, w, h: _paint_wolf(s, w, h, (138, 150, 170)),
    "thorn_brute": lambda s, w, h: _paint_wolf(s, w, h, (180, 100, 90)),
    "blizzard_hound": lambda s, w, h: _paint_wolf(s, w, h, (150, 200, 230)),
    "forest_alpha": lambda s, w, h: _paint_wolf(s, w, h, (168, 88, 88)),
    "scorpion": lambda s, w, h: _paint_scorpion(s, w, h, (196, 154, 58)),
    "crystal_scorpion": lambda s, w, h: _paint_scorpion(s, w, h, (220, 180, 80)),
    "dune_stalker": lambda s, w, h: _paint_scorpion(s, w, h, (210, 140, 48)),
    "wraith": lambda s, w, h: _paint_wraith(s, w, h, (154, 122, 184)),
    "frost_wraith": lambda s, w, h: _paint_wraith(s, w, h, (140, 190, 230)),
    "void_shade": lambda s, w, h: _paint_wraith(s, w, h, (120, 80, 160)),
    "ruin_sentinel": lambda s, w, h: _paint_colossus(s, w, h, (160, 100, 200)),
    "void_sovereign": lambda s, w, h: _paint_wraith(s, w, h, (180, 70, 220)),
    "void_lurker": lambda s, w, h: _paint_wraith(s, w, h, (130, 85, 170)),
    "curse_weaver": lambda s, w, h: _paint_wraith(s, w, h, (170, 90, 150)),
    "rift_stalker": lambda s, w, h: _paint_wraith(s, w, h, (130, 175, 220)),
    "moss_colossus": lambda s, w, h: _paint_colossus(s, w, h, (72, 140, 88)),
    "void_binder": lambda s, w, h: _paint_wraith(s, w, h, (145, 85, 175)),
    "spore_shaman": lambda s, w, h: _paint_slime(s, w, h, (90, 170, 80)),
    "mirror_shade": lambda s, w, h: _paint_wraith(s, w, h, (170, 150, 220)),
    "sand_colossus": lambda s, w, h: _paint_colossus(s, w, h, (212, 168, 74)),
    "sand_tyrant": lambda s, w, h: _paint_colossus(s, w, h, (232, 184, 64), crowned=True),
    "blue_boss": _paint_blue_boss,
    "ice_guardian": _paint_ice_guardian,
    "border_hunter": lambda s, w, h: _paint_wolf(s, w, h, (200, 60, 80)),
}


def draw_enemy_sprite(screen, x, y, w, h, enemy_id, color=None):
    painter = ENEMY_PAINTERS.get(enemy_id)
    if painter:
        SPRITES.blit(screen, f"sprite_{enemy_id}", w, h, painter, x, y)
    else:
        SPRITES.blit(screen, f"enemy_{enemy_id}_{color}", w, h, lambda s, ww, hh: _paint_slime(s, ww, hh, color or (120, 120, 120)), x, y)


def draw_player_sprite(screen, x, y, w, h):
    SPRITES.blit(screen, "player", w, h, _paint_player, x, y)


# --- АРТ КАРТ ---

def _paint_card_strike(s, w, h, heavy=False):
    _illustration_sky(s, w, h, (78, 32, 36), (32, 12, 14), (36, 20, 20), (14, 6, 8))
    sc = min(w, h) * 0.42
    kx, ky = int(w * 0.34), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash", heavy)
    for i in range(6):
        pygame.draw.arc(s, _rgba((255, 90 + i * 18, 90), 170 - i * 22), (kx - sc * 0.05, ky - sc * 0.95, sc * 1.15, sc * 0.95), 0.1, 2.4, max(2, int(sc * 0.04)))
    ex, ey = int(w * 0.82), int(h * 0.52)
    _poly(s, [(ex, ey - sc * 0.2), (ex + sc * 0.18, ey), (ex, ey + sc * 0.22), (ex - sc * 0.12, ey + sc * 0.05)], (28, 16, 18))
    _radial_glow(s, ex, ey, int(sc * 0.18), (255, 70, 70), 45)
    _impact_sparks(s, ex, ey - sc * 0.05, sc * 0.22)


def _paint_card_quick_slash(s, w, h):
    _illustration_sky(s, w, h, (70, 28, 30), (28, 10, 12))
    sc = min(w, h) * 0.36
    for i, dx in enumerate((0.22, 0.42)):
        kx = int(w * dx)
        _draw_card_knight(s, kx, int(h * 0.68), sc * 0.85, "slash")
        pygame.draw.line(s, (255, 140, 140), (kx + sc * 0.2, int(h * 0.45)), (kx + sc * 0.55, int(h * 0.28)), 3)


def _paint_card_pierce(s, w, h):
    _illustration_sky(s, w, h, (58, 24, 42), (20, 8, 16), (32, 14, 22), (10, 4, 8))
    sc = min(w, h) * 0.4
    kx, ky = int(w * 0.3), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash")
    ex, ey = int(w * 0.78), int(h * 0.54)
    shield = [(ex, ey - sc * 0.18), (ex + sc * 0.22, ey - sc * 0.12), (ex + sc * 0.18, ey + sc * 0.18), (ex - sc * 0.04, ey + sc * 0.14)]
    _poly(s, shield, (95, 130, 175))
    _poly(s, shield, (150, 180, 220), width=2)
    tip_x, tip_y = int(w * 0.86), int(h * 0.46)
    _poly(s, [(kx + sc * 0.5, ky - sc * 0.2), (tip_x, tip_y), (kx + sc * 0.55, ky - sc * 0.08)], (220, 228, 240))
    pygame.draw.line(s, (240, 248, 255), (kx + sc * 0.48, ky - sc * 0.16), (tip_x - 4, tip_y + 4), 2)
    _radial_glow(s, tip_x, tip_y, int(sc * 0.12), (255, 120, 120), 35)
    _impact_sparks(s, tip_x, tip_y, sc * 0.14)


def _paint_card_frost(s, w, h):
    _illustration_sky(s, w, h, (24, 52, 78), (8, 18, 32), (20, 36, 58), (6, 14, 28))
    sc = min(w, h) * 0.42
    kx, ky = int(w * 0.36), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash")
    tip_x, tip_y = kx + int(sc * 0.82), ky - int(sc * 0.32)
    pygame.draw.line(s, (170, 210, 235), (kx + int(sc * 0.12), ky - int(sc * 0.04)), (tip_x, tip_y), 6)
    pygame.draw.line(s, (235, 248, 255), (kx + int(sc * 0.14), ky - int(sc * 0.06)), (tip_x - 4, tip_y + 4), 2)
    for i in range(5):
        px = int(tip_x - sc * 0.12 + i * sc * 0.08)
        py = int(tip_y - sc * 0.04 - (i % 2) * 8)
        crystal = [(px, py - 6), (px + 4, py + 1), (px, py + 5), (px - 4, py + 1)]
        _poly(s, crystal, (215, 240, 255))
    _radial_glow(s, tip_x, tip_y, int(sc * 0.1), (170, 220, 255), 30)


def _paint_card_iron_will(s, w, h):
    _illustration_sky(s, w, h, (38, 42, 58), (12, 14, 22), (28, 32, 48), (8, 10, 16))
    sc = min(w, h) * 0.42
    kx, ky = int(w * 0.38), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "block")
    cx, cy = int(kx + sc * 0.12), int(ky - sc * 0.22)
    for i in range(4):
        rr = int(sc * (0.18 + i * 0.1))
        col = _shade((190, 200, 220), -i * 0.08)
        pygame.draw.arc(s, col, (cx - rr, cy - rr, rr * 2, rr * 2), -1.1, 1.1, 2)
    _radial_glow(s, cx, cy, int(sc * 0.22), (180, 190, 210), 35)


def _paint_card_defend(s, w, h, wall=False):
    _illustration_sky(s, w, h, (28, 48, 78), (8, 18, 34), (20, 36, 58), (6, 14, 28))
    sc = min(w, h) * 0.42
    kx, ky = int(w * 0.36), int(h * 0.68)
    if wall:
        for i in range(3):
            sx = int(w * 0.18 + i * sc * 0.28)
            _draw_card_knight(s, sx, ky, sc * 0.75, "block")
    else:
        _draw_card_knight(s, kx, ky, sc, "block")
        for i in range(5):
            ang = -0.5 + i * 0.25
            px = int(kx + sc * 0.32 + math.cos(ang) * sc * 0.15)
            py = int(ky - sc * 0.08 + math.sin(ang) * sc * 0.15)
            _impact_sparks(s, px, py, sc * 0.08)


def _paint_card_power(s, w, h, cry=False):
    _illustration_sky(s, w, h, (48, 28, 68), (14, 8, 26))
    sc = min(w, h) * 0.4
    kx, ky = int(w * 0.38), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "block" if cry else "slash")
    cx, cy = int(kx + sc * 0.06), int(ky - sc * 0.28)
    _radial_glow(s, cx, cy, int(sc * 0.28), (210, 170, 255), 40)
    if cry:
        for i in range(4):
            rr = int(sc * (0.16 + i * 0.1))
            pygame.draw.arc(s, (255, 190, 120), (cx - rr, cy - rr + sc * 0.08, rr * 2, rr * 2), -0.9, 0.9, 3)
        pygame.draw.polygon(s, (255, 200, 130), [(cx - sc * 0.08, cy + sc * 0.12), (cx + sc * 0.08, cy + sc * 0.12), (cx, cy + sc * 0.24)])
    else:
        pygame.draw.line(s, (240, 220, 255), (cx, cy - sc * 0.18), (cx, cy + sc * 0.18), 4)
        pygame.draw.line(s, (240, 220, 255), (cx - sc * 0.14, cy), (cx + sc * 0.14, cy), 4)


def _paint_card_poison(s, w, h):
    _illustration_sky(s, w, h, (18, 42, 20), (4, 14, 6), (12, 28, 14), (2, 8, 4))
    sc = min(w, h) * 0.4
    kx, ky = int(w * 0.34), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash")
    dx, dy = int(kx + sc * 0.55), int(ky - sc * 0.18)
    pygame.draw.line(s, (170, 180, 190), (dx - sc * 0.08, dy + sc * 0.28), (dx + sc * 0.04, dy - sc * 0.22), 4)
    _radial_glow(s, dx, dy - int(sc * 0.18), 10, (80, 220, 70), 35)
    pygame.draw.circle(s, (70, 210, 60), (dx, dy - int(sc * 0.18)), 7)
    for dy_off in (0.04, 0.12, 0.2):
        pygame.draw.circle(s, (50, 170, 45), (dx + int(sc * 0.06), dy - int(sc * dy_off)), 3)


def _paint_card_draw(s, w, h):
    _illustration_sky(s, w, h, (22, 36, 56), (8, 12, 22), (16, 28, 44), (4, 8, 16))
    sc = min(w, h) * 0.36
    kx, ky = int(w * 0.34), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "block")
    cx, cy = int(w * 0.68), int(h * 0.42)
    for i in range(3):
        off = i * 10
        card = pygame.Rect(cx - int(w * 0.18) + off, cy - int(h * 0.14) + off // 2, int(w * 0.28), int(h * 0.32))
        _vgradient(s, card, _shade((175, 195, 225), -i * 0.06), _shade((130, 150, 185), -i * 0.06))
        pygame.draw.rect(s, (210, 225, 245), card, 1, border_radius=5)


def _paint_card_whirlwind(s, w, h):
    _illustration_sky(s, w, h, (48, 20, 20), (16, 6, 6), (28, 10, 10), (8, 2, 2))
    sc = min(w, h) * 0.38
    kx, ky = int(w * 0.42), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash")
    cx, cy = int(kx + sc * 0.08), int(ky - sc * 0.12)
    for ring in range(3):
        rr = int(sc * (0.22 + ring * 0.12))
        pygame.draw.arc(s, (255, 170, 170), (cx - rr, cy - rr, rr * 2, rr * 2), 0.2, 5.8, 3)
    for i in range(8):
        ang = i * math.pi / 4 + 0.3
        x1 = cx + int(math.cos(ang) * sc * 0.12)
        y1 = cy + int(math.sin(ang) * sc * 0.12)
        x2 = cx + int(math.cos(ang) * sc * 0.42)
        y2 = cy + int(math.sin(ang) * sc * 0.42)
        pygame.draw.line(s, (255, 190, 190), (x1, y1), (x2, y2), 3)


def _paint_card_execute(s, w, h):
    _illustration_sky(s, w, h, (38, 10, 10), (12, 2, 2), (24, 6, 6), (6, 0, 0))
    sc = min(w, h) * 0.4
    kx, ky = int(w * 0.36), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash")
    cx, cy = int(w * 0.72), int(h * 0.52)
    pygame.draw.rect(s, (100, 35, 35), (cx - int(w * 0.16), cy + int(h * 0.04), int(w * 0.32), int(h * 0.08)), border_radius=2)
    blade = [(cx - int(w * 0.14), cy + int(h * 0.04)), (cx + int(w * 0.14), cy + int(h * 0.04)), (cx + int(w * 0.16), cy - int(h * 0.22)), (cx - int(w * 0.16), cy - int(h * 0.22))]
    _poly(s, blade, (210, 218, 228))
    _poly(s, blade, (150, 160, 175), width=2)
    _radial_glow(s, cx, cy - int(h * 0.06), 12, (255, 80, 80), 30)


def _paint_card_ruin(s, w, h):
    _illustration_sky(s, w, h, (24, 8, 32), (6, 0, 10), (18, 4, 24), (4, 0, 6))
    sc = min(w, h) * 0.42
    kx, ky = int(w * 0.38), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "slash", heavy=True)
    cx, cy = int(w * 0.72), int(h * 0.46)
    _radial_glow(s, cx, cy, int(min(w, h) * 0.22), (170, 60, 210), 45)
    _poly(s, [(cx, cy - int(h * 0.18)), (cx + int(w * 0.1), cy + int(h * 0.14)), (cx - int(w * 0.1), cy + int(h * 0.14))], (130, 50, 170))
    for i in range(5):
        px = cx - int(w * 0.18) + i * int(w * 0.08)
        pygame.draw.line(s, (70, 25, 25), (px, cy + int(h * 0.16)), (px + 4, cy + int(h * 0.22)), 2)


def _paint_card_pulse(s, w, h):
    _illustration_sky(s, w, h, (12, 42, 52), (4, 14, 18), (8, 28, 36), (2, 8, 12))
    sc = min(w, h) * 0.38
    kx, ky = int(w * 0.38), int(h * 0.68)
    _draw_card_knight(s, kx, ky, sc, "block")
    cx, cy = int(kx + sc * 0.1), int(ky - sc * 0.18)
    for i in range(4):
        rr = int(sc * (0.14 + i * 0.1))
        col = _shade(COLORS["accent"], 0.15 - i * 0.05)
        pygame.draw.circle(s, col, (cx, cy), rr, 2)
    _radial_glow(s, cx, cy, int(sc * 0.1), COLORS["accent"], 35)


def _paint_card_default(s, w, h, card_type):
    top = COLORS.get(f"card_{card_type}", COLORS["panel_border"])
    _illustration_sky(s, w, h, _shade(top, 0.15), _shade(top, -0.35))
    sc = min(w, h) * 0.35
    _draw_card_knight(s, w // 2, int(h * 0.68), sc, "slash")


CARD_ART = {
    "strike": lambda s, w, h: _paint_card_strike(s, w, h, False),
    "heavy_blow": lambda s, w, h: _paint_card_strike(s, w, h, True),
    "quick_slash": _paint_card_quick_slash,
    "piercing_strike": _paint_card_pierce,
    "frost_edge": _paint_card_frost,
    "defend": lambda s, w, h: _paint_card_defend(s, w, h, False),
    "shield_wall": lambda s, w, h: _paint_card_defend(s, w, h, True),
    "iron_will": _paint_card_iron_will,
    "frontier_pulse": _paint_card_pulse,
    "rally": _paint_card_draw,
    "venom_dagger": _paint_card_poison,
    "battle_cry": lambda s, w, h: _paint_card_power(s, w, h, True),
    "whirlwind": _paint_card_whirlwind,
    "execute": _paint_card_execute,
    "ruin_strike": _paint_card_ruin,
}


def draw_card_art(screen, card, x, y, w, h):
    cid = card.get("id", card.get("effect", "strike"))
    ctype = card.get("type", "attack")
    painter = CARD_ART.get(cid)
    if painter:
        SPRITES.blit(screen, f"card_{cid}", w, h, painter, x, y, scale=CARD_RENDER_SCALE)
    else:
        SPRITES.blit(screen, f"card_type_{ctype}", w, h, lambda s, ww, hh: _paint_card_default(s, ww, hh, ctype), x, y, scale=CARD_RENDER_SCALE)


# --- УЗЛЫ И СЦЕНЫ ---

def _paint_node(node_type, surf, w, h):
    cx, cy = w // 2, h // 2
    r = min(w, h) // 2 - 2
    themes = {
        "battle": ((100, 38, 38), (36, 10, 10), (255, 110, 110)),
        "elite": ((78, 38, 102), (28, 10, 40), (230, 170, 255)),
        "rest": ((105, 58, 22), (38, 18, 6), (255, 175, 75)),
        "shop": ((38, 48, 82), (12, 16, 28), COLORS["gold"]),
        "event": ((48, 48, 70), (16, 16, 24), (255, 205, 115)),
        "boss": ((110, 22, 22), (36, 4, 4), (255, 70, 70)),
    }
    outer, inner, accent = themes.get(node_type, ((40, 40, 50), (18, 18, 26), (200, 200, 210)))

    for ring in range(r, max(r // 2, 1), -2):
        t = (r - ring) / max(1, r - r // 2)
        pygame.draw.circle(surf, _lerp(outer, inner, t), (cx, cy), ring)

    inner_disc = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    _vgradient(inner_disc, (0, 0, r * 2, r * 2), _rgba(_shade(inner, 0.15), 180), _rgba(_shade(inner, -0.2), 220))
    surf.blit(inner_disc, (cx - r, cy - r))

    _radial_glow(surf, cx, cy, r // 2 + 4, accent, 26)
    from icons import draw_node_icon
    draw_node_icon(surf, cx, cy, r - 10, node_type, (252, 252, 255))

    pygame.draw.circle(surf, _shade(accent, 0.1), (cx, cy), r - 2, 2)
    if node_type == "boss":
        for i in range(6):
            ang = i * math.pi / 3
            sx = int(cx + math.cos(ang) * (r - 4))
            sy = int(cy + math.sin(ang) * (r - 4))
            _sparkle(surf, sx, sy, accent, 2)
    elif node_type == "elite":
        pygame.draw.circle(surf, accent, (cx, cy), r - 6, 1)


def draw_node_sprite(screen, x, y, size, node_type):
    SPRITES.blit(screen, f"node_{node_type}", size, size, lambda s, w, h: _paint_node(node_type, s, w, h), x, y)


def draw_menu_hero(screen, x, y, w, h):
    def paint(surf, ww, hh):
        _vgradient(surf, (0, 0, ww, hh), (6, 10, 20), (20, 32, 48))
        for layer in range(3):
            mist = pygame.Surface((ww, hh // 3), pygame.SRCALPHA)
            mist.fill((COLORS["accent"][0] // 8, COLORS["accent"][1] // 8, COLORS["accent"][2] // 8, 30 + layer * 15))
            surf.blit(mist, (0, hh // 2 + layer * 12))

        moon_x, moon_y = ww - 56, 42
        _radial_glow(surf, moon_x, moon_y, 34, (210, 220, 240), 28)
        pygame.draw.circle(surf, (220, 230, 245), (moon_x, moon_y), 20)
        pygame.draw.circle(surf, (6, 10, 20), (moon_x + 7, moon_y - 5), 15)

        for i in range(7):
            mx = 16 + i * (ww - 32) // 6
            hgt = 28 + (i % 3) * 8
            col = (COLORS["accent"][0] // 5, COLORS["accent"][1] // 5, COLORS["accent"][2] // 5)
            pygame.draw.line(surf, col, (mx, hh - 10), (mx + 16, hh - 10 - hgt), 3)
            pygame.draw.circle(surf, col, (mx + 8, hh - 12 - hgt), 8)

        floor = pygame.Rect(8, hh - 32, ww - 16, 24)
        _vgradient(surf, floor, (24, 34, 46), (8, 12, 18))
        pygame.draw.rect(surf, _shade(COLORS["accent"], -0.35), floor, 1, border_radius=8)
        _radial_glow(surf, ww // 2, hh // 2 + 8, 58, COLORS["accent"], 22)
        draw_player_sprite(surf, ww // 2 - 52, hh // 2 - 62, 104, 118)

    SPRITES.blit(screen, "menu_hero", w, h, paint, x, y)


def draw_rest_campfire(screen, x, y, w, h):
    def paint(surf, ww, hh):
        _vgradient(surf, (0, 0, ww, hh), (10, 6, 4), (24, 16, 12))
        cx, cy = ww // 2, hh // 2 + hh * 0.08
        _radial_glow(surf, cx, cy - 12, 48, (255, 130, 50), 40)
        _radial_glow(surf, cx, cy - 8, 24, (255, 220, 120), 30)

        for i in range(7):
            col = (255, 100 + i * 16, 35 + i * 10)
            wob = (i - 3) * 2
            hgt = 10 + i * 10
            pygame.draw.polygon(surf, col, [(cx - 12 + wob, cy + 20), (cx + 12 - wob, cy + 20), (cx + wob // 2, cy + 20 - hgt)])

        stones = [(-34, 14), (-10, 18), (14, 16), (34, 12)]
        for sx, sy in stones:
            pygame.draw.ellipse(surf, (55, 38, 28), (cx + sx - 10, cy + sy, 20, 12))
            pygame.draw.ellipse(surf, (40, 26, 18), (cx + sx - 8, cy + sy + 6, 16, 8))

        for lx, ly, lw in [(-32, 12, 26), (-6, 16, 28), (18, 14, 24), (36, 10, 22)]:
            log = pygame.Rect(cx + lx, cy + ly, lw, 10)
            _hgradient(surf, log, (70, 45, 28), (45, 28, 18))
            pygame.draw.rect(surf, (35, 22, 14), log, 1, border_radius=4)

        for i in range(12):
            ang = i * 0.9
            px = int(cx + math.cos(ang) * (8 + i * 2))
            py = int(cy - 18 - i * 5)
            pygame.draw.circle(surf, (255, 225, 130), (px, py), 2)

    SPRITES.blit(screen, "rest_fire", w, h, paint, x, y)


def draw_shop_banner(screen, x, y, w, h):
    def paint(surf, ww, hh):
        _vgradient(surf, (0, 0, ww, hh), (28, 20, 10), (10, 6, 2))
        sign = pygame.Rect(6, 6, ww - 12, hh - 26)
        _vgradient(surf, sign, (88, 66, 32), (48, 34, 16))
        pygame.draw.rect(surf, COLORS["gold"], sign, 2, border_radius=10)
        for px in (16, ww - 16):
            pygame.draw.line(surf, (60, 42, 20), (px, 6), (px, 0), 3)
            pygame.draw.circle(surf, COLORS["gold"], (px, 0), 3)
        _radial_glow(surf, ww // 2, hh // 2 - 6, 26, COLORS["gold"], 30)
        from icons import draw_node_icon
        draw_node_icon(surf, ww // 2, hh // 2 - 6, 38, "shop", COLORS["gold"])
        shelf = pygame.Rect(10, hh - 20, ww - 20, 14)
        _hgradient(surf, shelf, (70, 52, 26), (40, 28, 12))
        for dx in range(-2, 3):
            pygame.draw.circle(surf, COLORS["gold"], (shelf.centerx + dx * 18, shelf.centery), 2)

    SPRITES.blit(screen, "shop_banner", w, h, paint, x, y)


def _paint_event_campfire(s, w, h):
    _vgradient(s, (0, 0, w, h), (12, 10, 18), (28, 18, 14))
    cx, cy = w // 2, h // 2 + 10
    _radial_glow(s, cx, cy - 8, int(min(w, h) * 0.38), (255, 130, 50), 45)
    for i in range(5):
        ang = -0.8 + i * 0.35
        fx = cx + int(math.cos(ang) * 16)
        fy = cy - int(math.sin(ang) * 28) - 8
        _poly(s, [(fx, fy + 20), (fx - 8, fy), (fx + 8, fy)], (255, 120 + i * 15, 40 + i * 10))
    logs = [(cx - 38, cy + 18), (cx - 8, cy + 24), (cx + 18, cy + 20), (cx + 36, cy + 26)]
    for lx, ly in logs:
        pygame.draw.line(s, (60, 38, 24), (lx - 16, ly), (lx + 16, ly), 6)
    for i in range(8):
        px = cx - 40 + i * 11
        py = cy + 30 + (i % 2) * 3
        pygame.draw.circle(s, _rgba((255, 200, 120), 120), (px, py), 2)


def _paint_event_ruins(s, w, h):
    _vgradient(s, (0, 0, w, h), (10, 8, 22), (32, 20, 48))
    cx, cy = w // 2, h // 2
    for i in range(4):
        px = cx - 50 + i * 28
        ph = 30 + (i % 2) * 18
        block = pygame.Rect(px, cy + 20 - ph, 22, ph)
        _vgradient(s, block, (70, 62, 88), (40, 34, 56))
        pygame.draw.rect(s, (110, 100, 140), block, 1, border_radius=2)
    _radial_glow(s, cx, cy - 10, int(min(w, h) * 0.32), (170, 90, 255), 35)
    for i in range(6):
        ang = i * math.pi / 3 + 0.2
        sx = int(cx + math.cos(ang) * 34)
        sy = int(cy - 10 + math.sin(ang) * 18)
        _sparkle(s, sx, sy, (210, 170, 255), 2)


def _paint_event_smith(s, w, h):
    _vgradient(s, (0, 0, w, h), (14, 12, 18), (36, 28, 22))
    cx, cy = w // 2, h // 2 + 12
    anvil = pygame.Rect(cx - 34, cy + 8, 68, 16)
    _metallic_plate(s, anvil, (58, 52, 60))
    block = pygame.Rect(cx - 18, cy - 28, 36, 36)
    _vgradient(s, block, (120, 70, 40), (70, 40, 24))
    pygame.draw.rect(s, (160, 100, 50), block, 2, border_radius=4)
    _radial_glow(s, cx + 24, cy - 8, 16, (255, 180, 60), 40)
    for i in range(10):
        ang = -1.2 + i * 0.25
        dist = 14 + (i % 3) * 6
        sx = cx + 24 + int(math.cos(ang) * dist)
        sy = cy - 8 - int(math.sin(ang) * dist)
        pygame.draw.circle(s, (255, 210, 80), (sx, sy), 2)


def _paint_event_fog(s, w, h):
    _vgradient(s, (0, 0, w, h), (18, 24, 36), (48, 56, 68))
    cx, cy = w // 2, h // 2 + 8
    for layer in range(4):
        mist = pygame.Surface((w, h // 3), pygame.SRCALPHA)
        alpha = 40 + layer * 18
        mist.fill((180, 200, 220, alpha))
        s.blit(mist, (0, cy - 30 + layer * 10))
    silhouette = [(cx - 20, cy + 30), (cx - 8, cy - 10), (cx + 6, cy + 30)]
    _poly(s, silhouette, (28, 36, 48))
    _radial_glow(s, cx, cy + 10, int(min(w, h) * 0.28), COLORS["accent"], 22)
    for i in range(5):
        px = cx - 50 + i * 24
        pygame.draw.line(s, (200, 220, 235), (px, cy + 34), (px + 12, cy + 20), 2)


def _paint_event_forest(s, w, h):
    _vgradient(s, (0, 0, w, h), (10, 22, 14), (28, 48, 32))
    cx, cy = w // 2, h // 2 + 6
    for i in range(6):
        tx = cx - 70 + i * 28
        th = 36 + (i % 3) * 14
        pygame.draw.line(s, (60, 120, 70), (tx, cy + 28), (tx + 10, cy + 28 - th), 4)
        pygame.draw.circle(s, (80, 150, 90), (tx + 5, cy + 24 - th), 12)
    _radial_glow(s, cx, cy, int(min(w, h) * 0.3), (90, 180, 110), 28)


def _paint_event_snow(s, w, h):
    _vgradient(s, (0, 0, w, h), (18, 28, 42), (48, 68, 88))
    cx, cy = w // 2, h // 2 + 10
    for i in range(8):
        px = cx - 60 + i * 18
        py = cy + 20 - (i % 3) * 8
        pygame.draw.circle(s, (210, 230, 245), (px, py), 3)
    pygame.draw.polygon(s, (180, 210, 230), [(cx - 30, cy + 24), (cx, cy - 20), (cx + 30, cy + 24)])
    _radial_glow(s, cx, cy, 24, (160, 200, 240), 24)


def _paint_event_desert(s, w, h):
    _vgradient(s, (0, 0, w, h), (36, 28, 16), (72, 56, 32))
    cx, cy = w // 2, h // 2 + 16
    pygame.draw.ellipse(s, (200, 170, 90), (cx - 40, cy - 8, 80, 20))
    pygame.draw.rect(s, (160, 120, 60), (cx - 18, cy - 22, 36, 18), border_radius=4)
    _radial_glow(s, cx, cy - 6, 20, (255, 210, 120), 30)


EVENT_SCENES = {
    "campfire": _paint_event_campfire,
    "ruins": _paint_event_ruins,
    "smith": _paint_event_smith,
    "fog": _paint_event_fog,
    "whispering_thicket": _paint_event_forest,
    "snow_echo": _paint_event_snow,
    "sand_tomb": _paint_event_desert,
    "void_altar": _paint_event_ruins,
    "alchemist": _paint_event_smith,
}


def draw_event_scene(screen, x, y, w, h, event_id="campfire"):
    painter = EVENT_SCENES.get(event_id, _paint_event_campfire)
    SPRITES.blit(screen, f"event_{event_id}", w, h, painter, x, y)


def draw_arena_character(screen, x, y, w, h, kind, enemy_id=None, accent=None, acting=False):
    cx, cy = x + w // 2, y + h // 2
    if acting and accent:
        _radial_glow(screen, cx, cy, max(w, h) // 2 + 6, accent, 28)
        ring = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*accent, 50), ring.get_rect(), 2)
        screen.blit(ring, (x - 6, y - 6))

    platform = pygame.Rect(x + 4, y + h - 10, w - 8, 8)
    plat_surf = pygame.Surface((platform.width, platform.height), pygame.SRCALPHA)
    pygame.draw.ellipse(plat_surf, (0, 0, 0, 55), plat_surf.get_rect())
    screen.blit(plat_surf, platform.topleft)

    if kind == "player":
        draw_player_sprite(screen, x, y, w, h)
    elif enemy_id:
        draw_enemy_sprite(screen, x, y, w, h, enemy_id, accent)
