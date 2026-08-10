import math
import random
import sys

import pygame

from audio import Audio
import config
from config import COLORS, FPS, GAME_TITLE, NODE_COLORS, NODE_TYPES, clamp, daily_seed, get_display_preset, has_run_save, save_meta
from difficulty import get_difficulty, node_threat_label, pressure_tier
from enemies import intent_color, intent_label, get_next_intent
from game_state import ACHIEVEMENTS, ACT_TRANSITION, CODEX, COMBAT, DEFEAT, EVENT, HELP, MAP, MENU, RELIC_REWARD, REST, REST_REMOVE, REST_UPGRADE, REWARD, SETTINGS, SHOP, VICTORY, Game
from cards import preview_upgrade, sync_discovered_cards, shop_removal_price
from relics import RELIC_DEFS, draw_relic_icon
from icons import draw_card_type_icon, draw_intent_icon, draw_node_icon, draw_potion_icon
from potions import POTION_DEFS
from sprites import draw_arena_character, draw_enemy_sprite, draw_event_scene, draw_menu_hero, draw_player_sprite, draw_rest_campfire, draw_shop_banner
from mapgen import flatten_map, get_act_info, layout_map
from tutorial import TUTORIAL_STEPS
from ui_theme import (
    AnimatedBackground,
    ButtonRegistry,
    COMBAT_LAYOUT,
    draw_button,
    draw_card,
    draw_combat_arena,
    draw_combat_log,
    draw_flying_card,
    draw_combat_fx,
    draw_combat_chip_tooltip,
    draw_combat_relic_bar,
    draw_card_grid_overlay,
    draw_achievements_grid,
    draw_achievement_toast,
    draw_card_codex,
    draw_card_tooltip,
    draw_codex_tabs,
    draw_relic_codex,
    draw_relic_strip,
    draw_relic_tooltip,
    draw_map_node_tooltip,
    draw_map_depth_guides,
    draw_map_legend,
    draw_target_marker,
    draw_hit_pulse,
    combat_shake_offset,
    draw_entity_panel,
    draw_hand_tray,
    draw_map_node,
    draw_map_paths,
    draw_panel,
    draw_potion_bar,
    draw_potion_codex,
    draw_section_panel,
    draw_top_bar,
    draw_upgrade_preview,
    layout_card_grid,
    position_upgrade_preview,
    draw_actions_bar,
    layout_action_buttons,
    layout_hand_cards,
    layout_reward_cards,
    layout_shop_cards,
    MAP_LAYOUT,
    draw_volume_slider,
    load_fonts,
    rebuild_layouts,
    wrap_text,
)

pygame.init()
pygame.display.set_caption(GAME_TITLE)


class App:
    def __init__(self):
        self.window = None
        self.display_scale = 1.0
        self.display_offset = (0, 0)
        self.clock = pygame.time.Clock()
        self.game = Game()
        self.bg = None
        self.fonts = None
        self.screen = None
        self.buttons = ButtonRegistry()
        self.mouse = (0, 0)
        self.highlight_rects = {}
        self.anim = 0.0
        meta = self.game.meta
        self.audio = Audio(meta.get("music_volume", 0.7), meta.get("sfx_volume", 0.85))
        self.last_screen = MENU
        self.settings_drag = None
        self.music_slider_rect = None
        self.sfx_slider_rect = None
        self.card_overlay = None
        self.relic_flash = 0
        self.upgrade_flash = 0
        self.boss_intro = None
        self.hovered_card = None
        self.codex_tab = "relics"
        self.toasts = []
        self.combat_log_offset = 0
        self.combat_log_rect = None
        self.card_shake = None
        self.gold_popup = None
        self.hovered_card_energy = None
        self.map_scroll_x = 0
        self.map_scroll_y = 0
        self.map_press = None
        self.last_target_index = 0
        self.combat_outro_sfx = False
        self.event_popup = None
        self.confirm_new_run = False
        self.pending_daily = False
        self.apply_display_mode()

    SCREEN_LABELS = {
        "map": "Карта",
        "rest": "Привал",
        "rest_upgrade": "Кузница",
        "rest_remove": "Очищение",
        "shop": "Лавка",
        "event": "Событие",
        "reward": "Награда",
        "act_transition": "Новый акт",
    }

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 16.0
            self.anim += dt * 0.06
            self.bg.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game.save()
                    pygame.quit()
                    sys.exit(0)
                gpos = self.window_to_game(event.pos) if hasattr(event, "pos") else self.mouse
                if event.type == pygame.MOUSEMOTION:
                    self.mouse = gpos
                    if self.map_press and self.game.screen == MAP:
                        self.update_map_pan(gpos)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.game.screen == MAP and self.map_clip_rect().collidepoint(gpos):
                        self.begin_map_press(gpos)
                    elif self.game.screen == SETTINGS:
                        self.handle_settings_click(gpos)
                    else:
                        self.buttons.hit(gpos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.map_press:
                        self.end_map_press()
                    if self.settings_drag:
                        self.save_settings()
                    self.settings_drag = None
                if event.type == pygame.MOUSEMOTION and self.settings_drag:
                    self.apply_slider_drag(gpos)
                if event.type == pygame.MOUSEWHEEL and self.game.screen == COMBAT and self.game.combat:
                    if self.combat_log_rect and self.combat_log_rect.collidepoint(self.mouse):
                        c = self.game.combat
                        max_off = max(0, len(c.log_lines) - 8)
                        self.combat_log_offset = max(0, min(self.combat_log_offset - event.y, max_off))
                if event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            self.game.update()
            if (
                self.game.screen == COMBAT
                and self.game.combat
                and not self.game.combat_end_pending
                and self.game.combat.try_auto_end_turn()
            ):
                self.audio.play("turn")
                self.game.on_end_turn()
            if self.game.combat_end_pending and not self.combat_outro_sfx:
                self.combat_outro_sfx = True
                self.audio.play("win" if self.game.combat_end_pending == "won" else "lose")
            for ach_id in self.game.pop_toasts():
                self.toasts.append({"id": ach_id, "timer": 180})
                self.audio.play("achievement")
            for toast in self.toasts:
                toast["timer"] -= 1
            self.toasts = [t for t in self.toasts if t["timer"] > 0]
            if self.card_shake and self.card_shake["timer"] > 0:
                self.card_shake["timer"] -= 1
            elif self.card_shake:
                self.card_shake = None
            if self.gold_popup and self.gold_popup["timer"] > 0:
                self.gold_popup["timer"] -= 1
            elif self.gold_popup:
                self.gold_popup = None
            if self.event_popup and self.event_popup["timer"] > 0:
                self.event_popup["timer"] -= 1
            elif self.event_popup:
                self.event_popup = None
            self.draw()
            self.draw_relic_flash()
            self.draw_upgrade_flash()
            self.draw_boss_intro()
            self.draw_combat_outro()
            self.draw_tutorial_overlay()
            self.draw_achievement_toasts()
            self.draw_gold_popup()
            self.draw_event_popup()
            self.present()
            self.track_screen_change()
            self.update_music()

    def track_screen_change(self):
        screen = self.game.screen
        if screen == self.last_screen:
            return
        self.close_card_overlay()
        if screen == COMBAT:
            self.combat_log_offset = 0
            self.last_target_index = 0
            self.combat_outro_sfx = False
        if screen == MAP:
            self.map_scroll_x = 0
            self.map_scroll_y = 0
            self.map_press = None
            self._map_layout_key = None
            self.refresh_map_layout(recenter=True)
        if screen in (REWARD, RELIC_REWARD):
            if self.game.last_gold_gain > 0 or self.game.last_potion_gain:
                self.gold_popup = {
                    "amount": self.game.last_gold_gain,
                    "potion": self.game.last_potion_gain,
                    "timer": 120,
                }
        if screen == VICTORY:
            if not self.combat_outro_sfx:
                self.audio.play("win")
            self.audio.stop_music()
        elif screen == DEFEAT:
            if not self.combat_outro_sfx:
                self.audio.play("lose")
            self.audio.stop_music()
        elif screen == COMBAT and self.game.run and self.game.combat:
            node = (self.game.run.get("current_node") or {}).get("type")
            if node == "boss" and self.game.combat.living_enemies():
                self.boss_intro = {"name": self.game.combat.living_enemies()[0]["name"], "timer": 90}
        self.last_screen = screen

    def update_music(self):
        screen = self.game.screen
        if screen in (VICTORY, DEFEAT):
            return
        if screen == COMBAT:
            track = "combat"
        elif screen == SHOP:
            track = "shop"
        elif screen in (MENU, HELP, SETTINGS):
            track = "menu"
        elif screen == ACT_TRANSITION and self.game.run:
            track = get_act_info(self.game.run["act"])["biome"]
        elif self.game.run:
            track = get_act_info(self.game.run["act"])["biome"]
        else:
            track = "menu"
        self.audio.set_music(track)

    ACT_LORE = {
        0: "Лесной Рубеж — здесь тьма просачивается сквозь корни и шёпот.",
        1: "Пустынные Глубины — песок скрывает руины и древних стражей.",
        2: "Ледяной Предел — холод сжимает сердце, но путь вперёд один.",
        3: "Руины Предела — здесь реальность трескается, а Пустота смотрит в ответ.",
    }

    def current_biome(self):
        if self.game.run and self.game.screen in (MAP, COMBAT, REWARD, REST, REST_UPGRADE, REST_REMOVE, SHOP, EVENT, RELIC_REWARD, ACT_TRANSITION):
            return get_act_info(self.game.run["act"])["biome"]
        return None

    def select_map_node(self, node_id):
        self.audio.play("ui")
        self.game.select_node(node_id)

    def handle_key(self, key):
        if self.card_overlay:
            if key == pygame.K_LEFT:
                self.set_overlay_page(max(0, self.card_overlay.get("page", 0) - 1))
                return
            if key == pygame.K_RIGHT:
                self.set_overlay_page(self.card_overlay.get("page", 0) + 1)
                return
        if key == pygame.K_ESCAPE:
            if self.card_overlay:
                self.close_card_overlay()
                return
            if self.confirm_new_run:
                self.confirm_new_run = False
                return
            screen = self.game.screen
            if screen in (CODEX, ACHIEVEMENTS, HELP, SETTINGS):
                self.game.screen = MENU
                return
            if screen in (REST_UPGRADE, REST_REMOVE):
                if screen == REST_REMOVE and self.game.pending_remove_index is not None:
                    self.game.pending_remove_index = None
                elif screen == REST_REMOVE:
                    self.game.cancel_rest_remove()
                else:
                    self.game.screen = MAP
                return
            if screen == SHOP:
                self.leave_shop()
                return
            if screen == MENU:
                self.quit_game()
                return
        if self.game.screen == MENU and key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.confirm_new_run:
                self.do_new_run()
            elif has_run_save(self.game.meta):
                self.continue_run()
            else:
                self.do_new_run()
        screen = self.game.screen
        if screen == REWARD:
            if key in (pygame.K_s,):
                self.audio.play("ui")
                self.game.pick_reward(-1)
            elif pygame.K_1 <= key <= pygame.K_3:
                idx = key - pygame.K_1
                if idx < len(self.game.reward_cards):
                    self.audio.play("card")
                    self.game.pick_reward(idx)
        elif screen == RELIC_REWARD:
            if key in (pygame.K_s,):
                self.audio.play("ui")
                self.game.pick_relic(-1)
            elif pygame.K_1 <= key <= pygame.K_3:
                idx = key - pygame.K_1
                if idx < len(self.game.relic_choices):
                    self.pick_relic_reward(idx)
        elif screen == SHOP:
            if key in (pygame.K_q,):
                self.leave_shop()
            elif key in (pygame.K_r,):
                if not self.game.run.get("shop_removal_used") and len(self.game.run.get("deck", [])) > 5 and self.game.run["gold"] >= shop_removal_price():
                    self.audio.play("ui")
                    self.game.shop_remove()
                else:
                    self.audio.play("buzz")
            elif key in (pygame.K_h,):
                from difficulty import shop_price
                price = shop_price(55)
                can_heal = (
                    not self.game.run.get("shop_heal_used")
                    and self.game.run["gold"] >= price
                    and self.game.run["hp"] < self.game.run["max_hp"]
                )
                if can_heal:
                    self.audio.play("ui")
                    self.game.shop_heal()
                else:
                    self.audio.play("buzz")
            elif pygame.K_1 <= key <= pygame.K_6:
                idx = key - pygame.K_1
                if idx < len(self.game.shop_items):
                    item = self.game.shop_items[idx]
                    if self.game.run["gold"] >= item["price"]:
                        if item.get("type") == "potion":
                            from potions import can_add_potion
                            if not can_add_potion(self.game.run):
                                self.audio.play("buzz")
                                return
                        self.audio.play("card")
                        self.game.buy_shop_item(idx)
                    else:
                        self.audio.play("buzz")
        elif screen == EVENT:
            ev = self.game.current_event
            if ev and pygame.K_1 <= key <= pygame.K_9:
                idx = key - pygame.K_1
                if idx < len(ev["choices"]):
                    self.pick_event_choice(idx)
        elif screen == REST:
            if key == pygame.K_1:
                self.audio.play("ui")
                self.game.rest_heal()
            elif key == pygame.K_2:
                self.audio.play("ui")
                self.game.rest_upgrade()
            elif key == pygame.K_3:
                self.audio.play("ui")
                self.game.rest_remove()
            elif key == pygame.K_4:
                from potions import can_add_potion
                if can_add_potion(self.game.run) and self.game.run["hp"] > 12:
                    self.audio.play("ui")
                    self.game.rest_brew()
                else:
                    self.audio.play("buzz")
        elif screen == ACT_TRANSITION:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.audio.play("ui")
                self.game.continue_act()
        elif screen in (VICTORY, DEFEAT):
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.request_new_run()
            elif key == pygame.K_m:
                self.audio.play("ui")
                self.game.to_menu()
        elif screen == CODEX:
            if key == pygame.K_1:
                self.set_codex_tab("relics")
            elif key == pygame.K_2:
                self.set_codex_tab("cards")
            elif key == pygame.K_3:
                self.set_codex_tab("potions")
        if self.game.screen == COMBAT and self.game.combat:
            c = self.game.combat
            if c.is_player_turn and not self.game.combat_end_pending:
                if key == pygame.K_TAB:
                    c.target_index += 1
                    self.audio.play("ui")
                if pygame.K_1 <= key <= pygame.K_9:
                    self.try_play_hand_card(c, key - pygame.K_1)
                for pot_key, pot_idx in ((pygame.K_z, 0), (pygame.K_x, 1), (pygame.K_c, 2)):
                    if key == pot_key:
                        if self.game.use_potion(pot_idx):
                            self.audio.play("ui")
                        else:
                            self.audio.play("buzz")

    def run_save_preview(self):
        payload = self.game.meta.get("run_save")
        if not payload or not payload.get("run"):
            return ""
        run = payload["run"]
        act = get_act_info(run["act"])["name"]
        screen = payload.get("screen", "map")
        place = self.SCREEN_LABELS.get(screen, screen)
        return f"{act} · {run['hp']}/{run['max_hp']} HP · {run['gold']} золота · {place}"

    def do_new_run(self):
        self.confirm_new_run = False
        daily = self.pending_daily
        self.pending_daily = False
        self.audio.play("ui")
        if daily:
            random.seed(daily_seed())
        self.game.new_run(daily=daily)
        if daily:
            random.seed()

    def request_new_run(self):
        self.pending_daily = False
        if has_run_save(self.game.meta):
            self.confirm_new_run = True
        else:
            self.do_new_run()

    def request_daily_run(self):
        from datetime import date
        if self.game.meta.get("daily_win_date") == date.today().isoformat():
            return
        self.pending_daily = True
        if has_run_save(self.game.meta):
            self.confirm_new_run = True
        else:
            self.do_new_run()

    def map_content_rect(self):
        margin = config.sx(8)
        top = config.sy(78)
        bottom = config.SCREEN_HEIGHT - config.sy(24)
        return pygame.Rect(margin, top, config.SCREEN_WIDTH - margin * 2, max(config.sy(420), bottom - top))

    def map_legend_rect(self):
        content = self.map_content_rect()
        h = config.sy(38)
        return pygame.Rect(content.x + config.sx(14), content.bottom - h - config.sy(8), content.width - config.sx(28), h)

    def map_clip_rect(self):
        legend = self.map_legend_rect()
        inner = self.map_content_rect().inflate(-config.sx(6), -config.sy(28))
        return pygame.Rect(inner.x, inner.y, inner.w, max(config.sy(200), legend.top - inner.y - config.sy(6)))

    def map_node_hit_radius(self):
        return config.sy(42)

    def refresh_map_layout(self, recenter=False):
        if not self.game.run or not self.game.run.get("map"):
            return
        clip = self.map_clip_rect()
        key = (clip.x, clip.y, clip.w, clip.h)
        if getattr(self, "_map_layout_key", None) != key:
            self._map_layout_key = key
            layout_map(self.game.run["map"], clip)
            recenter = True
        if recenter:
            self.auto_map_scroll()

    def map_scroll_limits_x(self):
        if not self.game.run:
            return 0, 0
        nodes = flatten_map(self.game.run["map"])
        clip = self.map_clip_rect()
        margin = config.sy(48)
        xs = [n["x"] for n in nodes]
        scroll_min = clip.left + margin - min(xs)
        scroll_max = clip.right - margin - max(xs)
        if scroll_min > scroll_max:
            mid = (scroll_min + scroll_max) // 2
            return mid, mid
        return int(scroll_min), int(scroll_max)

    def map_scroll_limits(self):
        if not self.game.run:
            return 0, 0
        nodes = flatten_map(self.game.run["map"])
        clip = self.map_clip_rect()
        margin = config.sy(48)
        ys = [n["y"] for n in nodes]
        scroll_min = clip.bottom - margin - max(ys)
        scroll_max = clip.top + margin - min(ys)
        if scroll_min > scroll_max:
            mid = (scroll_min + scroll_max) // 2
            return mid, mid
        return int(scroll_min), int(scroll_max)

    def map_node_at(self, pos):
        if not self.game.run:
            return None
        x_off = self.map_scroll_x
        y_off = self.map_scroll_y
        hit_r = self.map_node_hit_radius()
        for node in flatten_map(self.game.run["map"]):
            nx, ny = node["x"] + x_off, node["y"] + y_off
            if pygame.Rect(nx - hit_r, ny - hit_r, hit_r * 2, hit_r * 2).collidepoint(pos):
                return node
        return None

    def begin_map_press(self, pos):
        node = self.map_node_at(pos)
        pick = node if node and node["available"] and not node["visited"] else None
        self.map_press = {
            "pos": pos,
            "scroll_x": self.map_scroll_x,
            "scroll": self.map_scroll_y,
            "node": pick,
            "dragging": False,
        }

    def update_map_pan(self, pos):
        if not self.map_press:
            return
        dx = pos[0] - self.map_press["pos"][0]
        dy = pos[1] - self.map_press["pos"][1]
        if abs(dx) > 4 or abs(dy) > 4:
            self.map_press["dragging"] = True
        if self.map_press["dragging"]:
            x_lo, x_hi = self.map_scroll_limits_x()
            y_lo, y_hi = self.map_scroll_limits()
            self.map_scroll_x = int(clamp(self.map_press["scroll_x"] + dx, x_lo, x_hi))
            self.map_scroll_y = int(clamp(self.map_press["scroll"] + dy, y_lo, y_hi))

    def end_map_press(self):
        press = self.map_press
        self.map_press = None
        if press and not press.get("dragging") and press.get("node"):
            self.select_map_node(press["node"]["id"])

    def auto_map_scroll(self):
        run = self.game.run
        if not run:
            return
        nodes = flatten_map(run["map"])
        x_lo, x_hi = self.map_scroll_limits_x()
        y_lo, y_hi = self.map_scroll_limits()
        focus = [n for n in nodes if n["available"] and not n["visited"]]
        if not focus:
            focus = [n for n in nodes if n["visited"]] or nodes
        target_x = sum(n["x"] for n in focus) / len(focus)
        target_y = sum(n["y"] for n in focus) / len(focus)
        clip = self.map_clip_rect()
        self.map_scroll_x = int(clamp(clip.centerx - target_x, x_lo, x_hi))
        self.map_scroll_y = int(clamp(clip.centery - target_y, y_lo, y_hi))

    def window_to_game(self, pos):
        ox, oy = self.display_offset
        scale = max(self.display_scale, 0.001)
        gx = (pos[0] - ox) / scale
        gy = (pos[1] - oy) / scale
        return int(clamp(gx, 0, config.SCREEN_WIDTH - 1)), int(clamp(gy, 0, config.SCREEN_HEIGHT - 1))

    def apply_display_mode(self):
        preset = get_display_preset(self.game.meta)
        fullscreen = self.game.meta.get("fullscreen", False)
        flags = pygame.FULLSCREEN if fullscreen else 0
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), flags)
        else:
            self.screen = pygame.display.set_mode((preset["width"], preset["height"]), flags)
        self.window = self.screen
        config.SCREEN_WIDTH, config.SCREEN_HEIGHT = self.screen.get_size()
        rebuild_layouts(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        scale = config.SCREEN_HEIGHT / 720
        self.fonts = load_fonts(scale)
        self.bg = AnimatedBackground()
        self.display_scale = 1.0
        self.display_offset = (0, 0)
        self._map_layout_key = None
        if self.game.screen == MAP:
            self.refresh_map_layout(recenter=True)

    def present(self):
        pygame.display.flip()

    def cycle_display_preset(self):
        from config import DISPLAY_PRESETS

        if self.game.meta.get("fullscreen", False):
            return
        presets = DISPLAY_PRESETS
        cur = self.game.meta.get("display_preset", "1280x720")
        idx = next((i for i, p in enumerate(presets) if p["id"] == cur), 0)
        nxt = presets[(idx + 1) % len(presets)]
        self.game.meta["display_preset"] = nxt["id"]
        self.apply_display_mode()
        save_meta(self.game.meta)
        self.audio.play("ui")

    def toggle_fullscreen(self):
        self.game.meta["fullscreen"] = not self.game.meta.get("fullscreen", False)
        self.apply_display_mode()
        save_meta(self.game.meta)
        self.audio.play("ui")

    def try_play_hand_card(self, c, idx):
        if not c.is_player_turn or idx < 0 or idx >= len(c.hand):
            return
        sx, sy, cw, ch, gap = layout_hand_cards(len(c.hand))
        x = sx + idx * (cw + gap)
        card = c.hand[idx]
        if c.can_play(card):
            if c.play_card(idx, (x + cw // 2, sy + ch // 2), (cw, ch)):
                self.audio.play_card(card["type"])
                self.game.on_play_card()
        else:
            self.card_shake = {"idx": idx, "timer": 12}
            self.audio.play("buzz")

    def combat_entity_w(self, enemy_count=1):
        arena = COMBAT_LAYOUT["arena"]
        gap = config.sx(12)
        inset = config.sx(28)
        max_w = max(config.sx(200), arena.width // 2 - inset)
        if enemy_count <= 1:
            return min(config.sx(300), max_w)
        total_gaps = (enemy_count - 1) * gap
        avail = max(config.sx(200), arena.width // 2 - inset)
        return max(config.sx(200), (avail - total_gaps) // enemy_count)

    def combat_entity_h(self):
        return config.sy(84)

    def accent_for_screen(self):
        if self.game.run:
            return get_act_info(self.game.run["act"])["color"]
        return COLORS["accent"]

    def draw(self):
        self.buttons.clear()
        self.highlight_rects = {}
        self.hovered_card = None
        self.hovered_card_energy = None
        accent = self.accent_for_screen()
        self.bg.draw(self.screen, accent, self.current_biome())

        screen = self.game.screen
        if screen == MENU:
            self.draw_menu()
        elif screen == HELP:
            self.draw_help()
        elif screen == SETTINGS:
            self.draw_settings()
        elif screen == CODEX:
            self.draw_codex()
        elif screen == ACHIEVEMENTS:
            self.draw_achievements()
        elif screen == MAP:
            self.draw_map_screen(accent)
        elif screen == COMBAT:
            self.draw_combat(accent)
        elif screen == REWARD:
            self.draw_reward(accent)
        elif screen == RELIC_REWARD:
            self.draw_relic_reward(accent)
        elif screen == REST:
            self.draw_rest(accent)
        elif screen == REST_UPGRADE:
            self.draw_rest_upgrade(accent)
        elif screen == REST_REMOVE:
            self.draw_rest_remove(accent)
        elif screen == ACT_TRANSITION:
            self.draw_act_transition(accent)
        elif screen == SHOP:
            self.draw_shop(accent)
        elif screen == EVENT:
            self.draw_event(accent)
        elif screen == VICTORY:
            self.draw_end(True)
        elif screen == DEFEAT:
            self.draw_end(False)

        self.draw_footer_hint()
        if self.card_overlay:
            self.draw_card_overlay(accent)
        if self.hovered_card:
            draw_card_tooltip(self.screen, self.fonts, self.hovered_card, self.mouse, draw_card_type_icon, energy=self.hovered_card_energy)

    def open_card_overlay(self, title, cards, on_pick=None):
        self.card_overlay = {"title": title, "cards": list(cards), "on_pick": on_pick, "page": 0}

    def close_card_overlay(self):
        self.card_overlay = None

    def set_overlay_page(self, page):
        if self.card_overlay:
            cards = self.card_overlay["cards"]
            limit = 24
            total_pages = max(1, (len(cards) + limit - 1) // limit)
            self.card_overlay["page"] = max(0, min(page, total_pages - 1))
            self.audio.play("ui")

    def draw_card_overlay(self, accent):
        ov = self.card_overlay
        if not ov:
            return
        on_close = lambda: self.close_card_overlay()
        on_pick = ov.get("on_pick")
        _, hovered = draw_card_grid_overlay(
            self.screen, self.fonts, ov["title"], ov["cards"], self.mouse, self.buttons,
            draw_card_type_icon, on_pick=on_pick, on_close=on_close, accent=accent,
            page=ov.get("page", 0), on_page=self.set_overlay_page,
        )
        if hovered:
            self.hovered_card = hovered

    def draw_footer_hint(self):
        hints = {
            MENU: "Enter — продолжить или новый забег  ·  Esc — выход",
            MAP: "Клик по подсвеченному узлу — идти  ·  перетаскивание — прокрутка карты",
            COMBAT: "1–9 — карта  ·  Z/X/C — зелья  ·  Tab — сменить цель  ·  ход передаётся автоматически" if not (self.game.combat and not self.game.combat.is_player_turn) else (self.game.combat.action_banner or "Ход врага..."),
            REWARD: "1–3 — выбрать карту  ·  S — пропустить",
            RELIC_REWARD: "1–3 — взять реликвию  ·  S — отказаться",
            REST: "1 — лечение  ·  2 — улучшение  ·  3 — удаление  ·  4 — сварить зелье (−12 HP)",
            REST_UPGRADE: "Кликни карту для усиления — наведи для превью  ·  Esc — назад",
            REST_REMOVE: "Выбери карту — затем подтверди удаление  ·  Esc — назад",
            SHOP: "1–6 — купить  ·  H — лечение  ·  R — удалить  ·  Q/Esc — уйти",
            EVENT: "1–3 — выбор  ·  наведи для подсказки",
            ACT_TRANSITION: "Enter — вперёд в новый акт",
            HELP: "Esc — назад в меню",
            SETTINGS: "Esc — назад в меню",
            VICTORY: "Enter — новый забег  ·  M — меню",
            DEFEAT: "Enter — новый забег  ·  M — меню",
            CODEX: "1/2/3 — вкладки  ·  Esc — назад",
            ACHIEVEMENTS: "Esc — назад в меню",
        }
        if self.card_overlay:
            text = "←/→ — страницы  ·  Esc — закрыть"
        else:
            text = hints.get(self.game.screen, "")
        if not text:
            return
        panel_w = min(config.sx(760), config.SCREEN_WIDTH - config.sx(40))
        panel_h = config.sy(28)
        footer_y = config.SCREEN_HEIGHT - config.sy(20)
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - panel_w // 2, footer_y - panel_h, panel_w, panel_h)
        draw_panel(self.screen, panel, fill=(10, 14, 22), border=COLORS["panel_border"], radius=12, alpha=180, shadow=False)
        txt = self.fonts["sm"].render(text, True, COLORS["text_dim"])
        self.screen.blit(txt, txt.get_rect(center=panel.center))

    def draw_tutorial_overlay(self):
        tut = self.game.tutorial
        screen_map = {MENU: "menu", MAP: "map", COMBAT: "combat", REWARD: "reward", RELIC_REWARD: "relic_reward", REST: "rest", SHOP: "shop"}
        if not tut.should_show(screen_map.get(self.game.screen, self.game.screen)):
            return
        step = tut.step
        if not step:
            return

        dim = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        hl = step.get("highlight")
        if hl and hl in self.highlight_rects:
            r = self.highlight_rects[hl]
            pygame.draw.rect(dim, (0, 0, 0, 0), r.inflate(12, 12))
            draw_panel(self.screen, r.inflate(12, 12), fill=(0, 0, 0, 0), border=COLORS["accent"], radius=10, alpha=0, shadow=False)
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 280, config.SCREEN_HEIGHT - 180, 560, 150)
        draw_panel(self.screen, panel, fill=(14, 18, 28), border=COLORS["accent"], radius=16, alpha=240)
        self.screen.blit(self.fonts["title_sm"].render(step["title"], True, COLORS["accent"]), (panel.x + 20, panel.y + 14))
        wrap_text(self.screen, self.fonts["md"], step["text"], panel.x + 20, panel.y + 46, panel.width - 40, COLORS["text"])
        step_num = self.fonts["sm"].render(f"Обучение {tut.step_index + 1}/{len(TUTORIAL_STEPS)}", True, COLORS["text_dim"])
        self.screen.blit(step_num, (panel.x + 20, panel.bottom - 30))
        if step["advance"] in ("any", "click"):
            draw_button(self.screen, self.fonts, pygame.Rect(panel.right - 220, panel.bottom - 42, 90, 34), "Далее", self.mouse, self.buttons, lambda: tut.advance("click"))
        draw_button(self.screen, self.fonts, pygame.Rect(panel.right - 120, panel.bottom - 42, 100, 34), "Пропустить", self.mouse, self.buttons, tut.skip, primary=False)

    def quit_game(self):
        self.game.save()
        pygame.quit()
        sys.exit(0)

    def _menu_setting_row(self, x, y, w, prefix, value, color, callback):
        row_h = config.sy(42)
        btn_w = config.sx(98)
        pad = config.sx(12)
        draw_panel(self.screen, pygame.Rect(x, y, w, row_h), fill=(18, 14, 28), border=color, radius=10, alpha=200, shadow=False)
        label = f"{prefix}: {value}"
        if len(label) > 26:
            label = label[:24] + "…"
        txt = self.fonts["sm"].render(label, True, color)
        max_w = w - btn_w - pad * 3
        if txt.get_width() > max_w:
            while len(label) > 3 and self.fonts["sm"].size(label + "…")[0] > max_w:
                label = label[:-1]
            label += "…"
            txt = self.fonts["sm"].render(label, True, color)
        ty = y + (row_h - txt.get_height()) // 2
        self.screen.blit(txt, (x + pad, ty))
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(x + w - btn_w - pad, y + (row_h - config.sy(30)) // 2, btn_w, config.sy(30)),
            "Сменить", self.mouse, self.buttons,
            lambda: (self.audio.play("ui"), callback()),
            primary=False,
        )
        return y + row_h + config.sy(10)

    def draw_menu(self):
        accent = COLORS["accent"]
        panel_w = config.sx(520)
        panel_h = config.sy(560)
        gap = config.sx(28)
        total_w = panel_w * 2 + gap
        footer_space = config.sy(34)
        start_x = max(config.sx(16), (config.SCREEN_WIDTH - total_w) // 2)
        start_y = max(config.sy(20), (config.SCREEN_HEIGHT - panel_h - footer_space) // 2)

        hero_panel = pygame.Rect(start_x, start_y, panel_w, panel_h)
        hero_content = draw_section_panel(self.screen, hero_panel, "Глубины Рубежа", self.fonts, accent=accent, alpha=210)
        art_h = config.sy(130)
        draw_menu_hero(self.screen, hero_content.x + config.sx(24), hero_content.y + config.sy(6), hero_content.width - config.sx(48), art_h)

        tagline = self.fonts["md"].render("Deckbuilder Roguelike", True, COLORS["text"])
        self.screen.blit(tagline, tagline.get_rect(center=(hero_content.centerx, hero_content.y + art_h + config.sy(28))))
        lore = [
            "Четыре акта. Четыре биома. Один Страж.",
            "Собери колоду, читай намерения врагов,",
            "дойди до Владыки Пустоты и удержи Рубеж.",
        ]
        lore_y = hero_content.y + art_h + config.sy(56)
        for i, line in enumerate(lore):
            self.screen.blit(
                self.fonts["sm"].render(line, True, COLORS["text_dim"]),
                (hero_content.x + config.sx(20), lore_y + i * config.sy(22)),
            )

        meta = self.game.meta
        stats_h = config.sy(92)
        stats_panel = pygame.Rect(
            hero_content.x + config.sx(12),
            hero_content.bottom - stats_h - config.sy(8),
            hero_content.width - config.sx(24),
            stats_h,
        )
        draw_panel(self.screen, stats_panel, fill=(14, 18, 28), border=COLORS["panel_border"], radius=12, alpha=200, shadow=False)
        from achievements import ACHIEVEMENT_DEFS
        from cards import all_card_ids
        found = len(meta.get("relics_found", []))
        ach = len(meta.get("achievements", []))
        stat_lines = [
            f"Побед: {meta.get('wins', 0)}  ·  Забегов: {meta.get('runs', 0)}",
            f"Артефактов: {found}/{len(RELIC_DEFS)}  ·  Карт: {len(meta.get('cards_found', []))}/{len(all_card_ids())}",
            f"Достижений: {ach}/{len(ACHIEVEMENT_DEFS)}  ·  Рекорд: акт {meta.get('best_act', 0)}, боёв {meta.get('best_combats', 0)}",
        ]
        line_y = stats_panel.y + config.sy(12)
        for line in stat_lines:
            surf = self.fonts["sm"].render(line, True, COLORS["text_dim"])
            self.screen.blit(surf, (stats_panel.x + config.sx(14), line_y))
            line_y += config.sy(24)

        menu_panel = pygame.Rect(start_x + panel_w + gap, start_y, panel_w, panel_h)
        menu_content = draw_section_panel(self.screen, menu_panel, "Страж Рубежа", self.fonts, accent=accent, alpha=210)
        pad = config.sx(18)
        inner_w = menu_content.width - pad * 2
        btn_x = menu_content.x + pad
        y = menu_content.y + config.sy(6)

        diff_name = get_difficulty()["name"]
        y = self._menu_setting_row(btn_x, y, inner_w, "Сложность", diff_name, COLORS["danger"], self.game.cycle_difficulty)

        from mutators import oath_label
        oath_name = oath_label(self.game.meta.get("oath", "none"))
        y = self._menu_setting_row(btn_x, y, inner_w, "Клятва", oath_name, COLORS["accent_warm"], self.game.cycle_oath)

        if self.confirm_new_run:
            panel = pygame.Rect(btn_x, y, inner_w, config.sy(180))
            draw_panel(self.screen, panel, fill=(14, 18, 28), border=COLORS["danger"], radius=16, alpha=240, shadow=True)
            warn = self.fonts["md"].render("Текущий забег будет удалён.", True, COLORS["text"])
            self.screen.blit(warn, warn.get_rect(center=(panel.centerx, panel.y + config.sy(36))))
            preview = self.run_save_preview()
            if preview:
                prev = self.fonts["sm"].render(preview, True, COLORS["text_dim"])
                self.screen.blit(prev, prev.get_rect(center=(panel.centerx, panel.y + config.sy(68))))
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(panel.centerx - config.sx(150), panel.y + config.sy(100), config.sx(140), config.sy(44)),
                "Удалить", self.mouse, self.buttons, self.do_new_run,
            )
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(panel.centerx + config.sx(10), panel.y + config.sy(100), config.sx(140), config.sy(44)),
                "Отмена", self.mouse, self.buttons,
                lambda: (setattr(self, "confirm_new_run", False), setattr(self, "pending_daily", False)),
                primary=False,
            )
            return

        btn_h = config.sy(42)
        if has_run_save(self.game.meta):
            draw_button(self.screen, self.fonts, pygame.Rect(btn_x, y, inner_w, btn_h), "Продолжить", self.mouse, self.buttons, self.continue_run)
            preview = self.run_save_preview()
            if preview:
                if len(preview) > 42:
                    preview = preview[:40] + "…"
                prev = self.fonts["sm"].render(preview, True, COLORS["accent"])
                self.screen.blit(prev, prev.get_rect(center=(btn_x + inner_w // 2, y + btn_h + config.sy(14))))
            y += btn_h + config.sy(30)
        else:
            y += config.sy(4)

        draw_button(self.screen, self.fonts, pygame.Rect(btn_x, y, inner_w, btn_h), "Новый Забег", self.mouse, self.buttons, self.request_new_run)
        y += btn_h + config.sy(10)

        from datetime import date
        daily_done = self.game.meta.get("daily_win_date") == date.today().isoformat()
        daily_label = "Ежедневный ✓" if daily_done else "Ежедневный Забег"
        draw_button(
            self.screen, self.fonts, pygame.Rect(btn_x, y, inner_w, config.sy(38)),
            daily_label, self.mouse, self.buttons, self.request_daily_run,
            primary=not daily_done,
        )
        y += config.sy(42)
        info = f"Сид: {daily_seed()}"
        if not daily_done:
            from mutators import MUTATOR_DEFS, roll_daily_mutators
            mut_name = MUTATOR_DEFS.get(roll_daily_mutators(daily_seed(), 1)[0], {}).get("name", "")
            if mut_name:
                info += f"   ·   Мод.: {mut_name}"
        if len(info) > 48:
            info = info[:46] + "…"
        info_surf = self.fonts["sm"].render(info, True, COLORS["gold"] if not daily_done else COLORS["text_dim"])
        self.screen.blit(info_surf, info_surf.get_rect(center=(btn_x + inner_w // 2, y + config.sy(10))))
        y += config.sy(28)

        col_w = (inner_w - config.sx(12)) // 2
        grid = [
            ("Обучение", lambda: self.game.replay_tutorial()),
            ("Справка", lambda: setattr(self.game, "screen", HELP)),
            ("Коллекция", lambda: setattr(self.game, "screen", CODEX)),
            ("Достижения", lambda: setattr(self.game, "screen", ACHIEVEMENTS)),
            ("Настройки", lambda: setattr(self.game, "screen", SETTINGS)),
            ("Выход", self.quit_game),
        ]
        row_h = config.sy(40)
        for i, (label, action) in enumerate(grid):
            col = i % 2
            row = i // 2
            bx = btn_x + col * (col_w + config.sx(12))
            by = y + row * row_h
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(bx, by, col_w, config.sy(36)), label, self.mouse, self.buttons,
                lambda cb=action: (self.audio.play("ui"), cb()),
                primary=False,
            )

    def continue_run(self):
        self.audio.play("ui")
        if self.game.continue_run():
            from difficulty import init_difficulty
            init_difficulty(self.game.meta)

    def draw_achievements(self):
        accent = COLORS["accent"]
        draw_top_bar(self.screen, self.fonts, "Достижения", "Награды за подвиги Стража", accent=accent)
        draw_achievements_grid(self.screen, self.fonts, self.game.meta, accent=accent)

    def set_codex_tab(self, tab):
        self.codex_tab = tab
        self.audio.play("ui")

    def draw_codex(self):
        accent = COLORS["gold"]
        title_map = {"relics": "Кодекс Артефактов", "cards": "Кодекс Карт", "potions": "Кодекс Зелий"}
        hint_map = {
            "relics": "Открывай реликвии в забегах",
            "cards": "Находи карты в наградах и лавке",
            "potions": "Покупай, варите на привале и находи с элит",
        }
        title = title_map.get(self.codex_tab, "Коллекция")
        hint = hint_map.get(self.codex_tab, "")
        draw_top_bar(self.screen, self.fonts, title, hint, accent=accent)
        draw_codex_tabs(self.screen, self.fonts, self.mouse, self.buttons, self.codex_tab, self.set_codex_tab, accent=accent)
        if self.codex_tab == "relics":
            draw_relic_codex(self.screen, self.fonts, self.game.meta, self.mouse, self.buttons, accent=accent)
        elif self.codex_tab == "potions":
            draw_potion_codex(self.screen, self.fonts, self.game.meta, self.mouse, draw_potion_icon, accent=COLORS["success"])
        else:
            draw_card_codex(self.screen, self.fonts, self.game.meta, self.mouse, draw_card_type_icon, accent=COLORS["accent"])
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(config.SCREEN_WIDTH // 2 - 100, 630, 200, 44),
            "Назад", self.mouse, self.buttons,
            lambda: setattr(self.game, "screen", MENU),
            primary=False,
        )

    def draw_help(self):
        accent = COLORS["accent"]
        draw_top_bar(self.screen, self.fonts, "Справка", get_difficulty()["name"], accent=accent)

        rules = pygame.Rect(60, 96, 740, 580)
        rules_content = draw_section_panel(self.screen, rules, "Правила", self.fonts, accent=accent, alpha=210)
        lines = [
            "Карта — выбирай светящиеся узлы. Каждый шаг необратим.",
            "Красные карты — атака, синие — блок, фиолетовые — силы на бой.",
            "Энергия: 3 за ход. Карт в руке: 4. Блок сгорает каждый ход.",
            "Враги показывают намерение — готовь защиту заранее.",
            "Tab — сменить цель. E — конец хода. 1–9 — сыграть карту.",
            "Награда: 1–3 выбор, S — пропуск. Реликвия: 1–3, S — отказ.",
            "Привал: 1 лечение, 2 улучшение, 3 удаление, 4 сварить зелье (−12 HP).",
            "Лавка: карты, зелья, артефакт, лечение (H), удаление (R).",
            "Зелья (до 3): Z/X/C в бою, 1 за ход. Лавка, элиты, привал (4).",
            "Клятва в меню — опциональный модификатор обычного забега.",
            "Ежедневный забег — один сид, модификатор дня, победа раз в день.",
            "4 акта: лес → пустыня → лёд → руины. Финальный босс — Владыка Пустоты.",
            "Уязвимость: враг получает +50% урона. Слабость/яд — ослабляют врага.",
            "Боссы впадают в ярость ниже 50% HP — меняют тактику.",
            "С 5-го хода боя враги получают +1 силы каждый ход — «давление Рубежа» (на Кошмаре — с 4-го).",
            "Охотник Рубежа может появиться в обычном бою — сильный враг, +55 золота, иногда с приставкой.",
            "Проклятия засоряют колоду; снять — на привале или в лавке (R).",
            "Чем больше боёв в забеге — тем сильнее враги. Элиты иногда с соратником.",
            "Акт II–III: опасные враги. Наведи на узел — увидишь уровень угрозы.",
            "Колода: ←/→ страницы, Esc закрыть. Карта: перетаскивание, легенда типов внизу.",
            "Enter — продолжить/новый забег. M — меню с экрана победы.",
            "Элиты и боссы опасны. Привалов мало — лечись экономно.",
            "Элиты и боссы дают реликвии — пассивные артефакты забега.",
            "На привале можно улучшить или удалить карту — один выбор за визит.",
            "«Рубеж» — проще, «Суровый Рубеж» — для опытных, «Кошмар» — экстрим. Смена в меню.",
            "Забег сохраняется автоматически — «Продолжить» в меню.",
        ]
        for i, line in enumerate(lines):
            self.screen.blit(self.fonts["md"].render(line, True, COLORS["text"]), (rules_content.x + 8, rules_content.y + 8 + i * 28))

        cards_panel = pygame.Rect(rules_content.x, rules_content.y + 196, rules_content.width, 150)
        draw_panel(self.screen, cards_panel, fill=(12, 16, 24), border=COLORS["panel_border"], radius=12, alpha=200, shadow=False)
        self.screen.blit(self.fonts["sm"].render("Типы карт", True, accent), (cards_panel.x + 14, cards_panel.y + 10))
        for i, (label, color_key) in enumerate((("Атака", "card_attack"), ("Навык", "card_skill"), ("Сила", "card_power"), ("Проклятие", "card_curse"))):
            cx = cards_panel.x + 40 + (i % 2) * 210
            cy = cards_panel.y + 58 + (i // 2) * 44
            chip = pygame.Rect(cx - 28, cy - 18, 56, 36)
            pygame.draw.rect(self.screen, COLORS[color_key], chip, border_radius=8)
            self.screen.blit(self.fonts["sm"].render(label, True, COLORS["text"]), (cx + 36, cy - 8))

        ref_panel = pygame.Rect(820, 96, 400, 580)
        ref_content = draw_section_panel(self.screen, ref_panel, "Узлы карты", self.fonts, accent=accent, alpha=210)
        for i, (nt, label) in enumerate(NODE_TYPES.items()):
            cx = ref_content.x + 36 + (i % 2) * 170
            cy = ref_content.y + 24 + (i // 2) * 72
            node_color = NODE_COLORS.get(nt, accent)
            draw_map_node(self.screen, cx, cy, nt, node_color, True, False, self.anim, draw_node_icon)
            self.screen.blit(self.fonts["sm"].render(label, True, COLORS["text_dim"]), (cx + 34, cy - 8))

        draw_button(
            self.screen, self.fonts,
            pygame.Rect(config.SCREEN_WIDTH // 2 - 100, 690, 200, 44),
            "Назад", self.mouse, self.buttons,
            lambda: setattr(self.game, "screen", MENU),
            primary=False,
        )

    def draw_settings(self):
        accent = COLORS["accent"]
        draw_top_bar(self.screen, self.fonts, "Настройки", "Звук и экран сохраняются между сессиями", accent=accent)
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - config.sx(280), config.sy(120), config.sx(560), config.sy(500))
        content = draw_section_panel(self.screen, panel, "Звук и экран", self.fonts, accent=accent, alpha=220)

        self.music_slider_rect = draw_volume_slider(
            self.screen, self.fonts,
            pygame.Rect(content.x + 24, content.y + 20, content.width - 48, 40),
            "Музыка", self.audio.music_volume, accent,
        )
        self.sfx_slider_rect = draw_volume_slider(
            self.screen, self.fonts,
            pygame.Rect(content.x + 24, content.y + 90, content.width - 48, 40),
            "Эффекты", self.audio.sfx_volume, COLORS["accent_warm"],
        )

        hint = self.fonts["sm"].render("Перетащи ползунок или кликни по дорожке", True, COLORS["text_dim"])
        self.screen.blit(hint, hint.get_rect(center=(content.centerx, content.y + 168)))

        test_rect = pygame.Rect(content.x + 24, content.y + 196, content.width - 48, 44)
        draw_panel(self.screen, test_rect, fill=(12, 16, 24), border=COLORS["panel_border"], radius=12, alpha=200, shadow=False)
        draw_button(self.screen, self.fonts, pygame.Rect(test_rect.x + 16, test_rect.y + 4, 150, 36), "Тест SFX", self.mouse, self.buttons, lambda: self.audio.play("ui"), primary=False)
        draw_button(self.screen, self.fonts, pygame.Rect(test_rect.right - 166, test_rect.y + 4, 150, 36), "Тест музыки", self.mouse, self.buttons, lambda: self.audio.set_music("menu"), primary=False)

        display_y = content.y + 260
        self.screen.blit(self.fonts["md"].render("Экран", True, accent), (content.x + 24, display_y))
        preset = get_display_preset(self.game.meta)
        fs = self.game.meta.get("fullscreen", False)
        cur_size = f"{config.SCREEN_WIDTH}×{config.SCREEN_HEIGHT}"
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.x + 24, display_y + 34, content.width - 48, 44),
            f"Разрешение: {preset['label']}" if not fs else f"Разрешение: {cur_size}",
            self.mouse, self.buttons, self.cycle_display_preset, primary=False,
        )
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.x + 24, display_y + 90, content.width - 48, 44),
            "Полный экран: да" if fs else "Полный экран: нет",
            self.mouse, self.buttons, self.toggle_fullscreen, primary=fs,
        )
        if fs:
            disp_hint = self.fonts["sm"].render("В полном экране — разрешение монитора. Выключите для выбора пресета.", True, COLORS["text_dim"])
        else:
            disp_hint = self.fonts["sm"].render(f"Сейчас {cur_size}. Клик — следующий пресет.", True, COLORS["text_dim"])
        self.screen.blit(disp_hint, (content.x + 24, display_y + 146))

        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.centerx - 100, content.bottom - 52, 200, 44),
            "Назад", self.mouse, self.buttons,
            lambda: setattr(self.game, "screen", MENU),
            primary=False,
        )

    def save_settings(self):
        self.game.meta["music_volume"] = self.audio.music_volume
        self.game.meta["sfx_volume"] = self.audio.sfx_volume
        save_meta(self.game.meta)

    def apply_slider_drag(self, pos):
        if self.settings_drag == "music" and self.music_slider_rect:
            self._set_slider_value(self.music_slider_rect, pos[0], "music")
        elif self.settings_drag == "sfx" and self.sfx_slider_rect:
            self._set_slider_value(self.sfx_slider_rect, pos[0], "sfx")

    def handle_settings_click(self, pos):
        if self.music_slider_rect and self.music_slider_rect.collidepoint(pos):
            self.settings_drag = "music"
            self._set_slider_value(self.music_slider_rect, pos[0], "music")
        elif self.sfx_slider_rect and self.sfx_slider_rect.collidepoint(pos):
            self.settings_drag = "sfx"
            self._set_slider_value(self.sfx_slider_rect, pos[0], "sfx")
        else:
            self.buttons.hit(pos)

    def _set_slider_value(self, track_rect, mouse_x, kind):
        inner = pygame.Rect(track_rect.x, track_rect.y + 24, track_rect.width, 10)
        value = clamp((mouse_x - inner.x) / max(1, inner.width), 0.0, 1.0)
        if kind == "music":
            self.audio.set_volumes(value, self.audio.sfx_volume)
        else:
            self.audio.set_volumes(self.audio.music_volume, value)
        self.save_settings()

    def run_stats(self, run):
        stats = [
            ("HP", f"{run['hp']}/{run['max_hp']}", COLORS["danger"]),
            ("Золото", str(run["gold"]), COLORS["gold"]),
            ("Колода", str(len(run.get("deck", []))), COLORS["text_dim"]),
        ]
        potions = len(run.get("potions", []))
        if potions:
            stats.append(("Зелья", str(potions), COLORS["success"]))
        return stats

    def draw_deck_button(self, run):
        if not run:
            return
        rect = pygame.Rect(config.SCREEN_WIDTH - 132, 18, 108, 36)
        draw_button(
            self.screen, self.fonts, rect, f"Колода ({len(run['deck'])})",
            self.mouse, self.buttons,
            lambda: self.open_card_overlay(f"Колода ({len(run['deck'])})", run["deck"]),
            primary=False,
        )

    def draw_map_screen(self, accent):
        run = self.game.run
        act = get_act_info(run["act"])
        subtitle = f"Акт {run['act'] + 1} · {get_difficulty()['name']}"
        if run.get("daily") and run.get("mutators"):
            from mutators import mutator_labels
            names = mutator_labels(run["mutators"])
            if names:
                subtitle += f" · {names[0]}"
        elif run.get("oath") and run.get("oath") != "none":
            from mutators import oath_label
            subtitle += f" · {oath_label(run['oath'])}"
        tier_name, _tier_color = pressure_tier(self.game.combats_won)
        subtitle += f" · Напряжение: {tier_name}"
        deck_cb = lambda: self.open_card_overlay(f"Колода ({len(run['deck'])})", run["deck"])
        draw_top_bar(
            self.screen, self.fonts, act["name"], subtitle,
            stats=self.run_stats(run), accent=accent,
            buttons=self.buttons, stat_clicks={"Колода": deck_cb},
        )

        map_rect = self.map_content_rect()
        MAP_LAYOUT["map"] = map_rect
        self.refresh_map_layout()
        draw_section_panel(self.screen, map_rect, "Карта Рубежа", self.fonts, accent=accent, alpha=150)

        nodes = flatten_map(run["map"])
        x_off = self.map_scroll_x
        y_off = self.map_scroll_y
        clip = self.map_clip_rect()
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(clip)
        draw_map_depth_guides(self.screen, self.fonts, clip, nodes, x_off, y_off, accent)
        draw_map_paths(self.screen, nodes, accent, self.anim, x_offset=x_off, y_offset=y_off)

        node_rects = []
        current = (self.game.run.get("current_node") or {}).get("id")
        hovered_node = None
        hit_r = self.map_node_hit_radius()
        for node in nodes:
            active = node["available"] and not node["visited"]
            is_here = current and node["id"] == current and node["visited"]
            nx, ny = node["x"] + x_off, node["y"] + y_off
            node_hit = pygame.Rect(nx - hit_r, ny - hit_r, hit_r * 2, hit_r * 2)
            hovered = active and node_hit.collidepoint(self.mouse)
            if hovered:
                hovered_node = node
            ntype = node["type"]
            node_color = NODE_COLORS.get(ntype, accent)
            if active:
                color = node_color
            elif node["visited"]:
                color = tuple(int(c * 0.55 + 40) for c in node_color)
            else:
                color = tuple(int(c * 0.35 + 28) for c in node_color)
            nr = draw_map_node(
                self.screen, nx, ny, ntype,
                color, active, node["visited"], self.anim,
                draw_node_icon, hovered=hovered,
                fonts=self.fonts, show_label=active or hovered,
            )
            if is_here:
                pulse = int(32 + math.sin(self.anim * 2.2) * 4)
                ring = pygame.Surface((pulse * 2 + 4, pulse * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring, (*COLORS["gold"], 120), (pulse + 2, pulse + 2), pulse, 2)
                self.screen.blit(ring, (nx - pulse - 2, ny - pulse - 2))
            node_rects.append(nr)
        self.screen.set_clip(prev_clip)

        if node_rects:
            box = node_rects[0].copy()
            for nr in node_rects[1:]:
                box = box.union(nr)
            self.highlight_rects["map_nodes"] = box

        relics = run.get("relics", [])
        if relics:
            icon_size = config.sy(28)
            strip_w = min(len(relics), 8) * (icon_size + config.sx(8)) + config.sx(16)
            strip_x = map_rect.right - strip_w - config.sx(12)
            strip_y = map_rect.y + config.sy(34)
            strip = pygame.Rect(strip_x, strip_y, strip_w, icon_size + config.sy(8))
            draw_panel(self.screen, strip, fill=(10, 14, 22), border=accent, radius=10, alpha=190, shadow=False)
            relic_hits = draw_relic_strip(
                self.screen, self.fonts, relics, strip.x + config.sx(8), strip.y + config.sy(4),
                max_count=8, size=icon_size,
            )
            draw_relic_tooltip(self.screen, self.fonts, self.mouse, relic_hits)

        if hovered_node:
            threat = node_threat_label(hovered_node["type"], run["act"], self.game.combats_won)
            draw_map_node_tooltip(
                self.screen, self.fonts, self.mouse,
                NODE_TYPES.get(hovered_node["type"], hovered_node["type"]),
                accent=NODE_COLORS.get(hovered_node["type"], accent), subtitle=f"Угроза: {threat}",
            )
        draw_map_legend(self.screen, self.fonts, self.map_legend_rect(), accent)
        self.highlight_rects["map_panel"] = map_rect

    def draw_card_ui(self, card, x, y, w, h, playable, on_click, hand_idx=None, hotkey=None):
        shake = 0
        if hand_idx is not None and self.card_shake and self.card_shake.get("idx") == hand_idx and self.card_shake["timer"] > 0:
            shake = int(math.sin(self.anim * 10) * 5)
        x += shake
        hovered = pygame.Rect(x, y, w, h).collidepoint(self.mouse) or pygame.Rect(x, y - 8, w, h + 8).collidepoint(self.mouse)
        rect = draw_card(self.screen, self.fonts, card, x, y, w, h, playable, hovered, draw_card_type_icon)
        if hotkey and hotkey <= 9:
            key_lbl = self.fonts["sm"].render(str(hotkey), True, COLORS["gold"])
            self.screen.blit(key_lbl, (x + 6, y + 4))
        if hovered:
            self.hovered_card = card
        if on_click:
            self.buttons.add(rect, on_click)
        return rect

    def draw_combat_outro(self):
        pending = self.game.combat_end_pending
        if not pending:
            return
        won = pending == "won"
        accent = COLORS["gold"] if won else COLORS["danger"]
        timer = self.game.combat_end_timer
        alpha = min(200, int(200 * (75 - timer) / 20)) if timer > 55 else min(200, int(200 * timer / 25))
        dim = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(120, alpha // 2)))
        self.screen.blit(dim, (0, 0))
        banner = pygame.Rect(config.SCREEN_WIDTH // 2 - config.sx(220), config.SCREEN_HEIGHT // 2 - config.sy(50), config.sx(440), config.sy(88))
        border = accent
        draw_panel(self.screen, banner, fill=(14, 18, 28), border=border, radius=16, alpha=min(240, alpha + 40), shadow=True)
        title = "ПОБЕДА!" if won else "ПОРАЖЕНИЕ"
        title_surf = self.fonts["hero"].render(title, True, accent)
        self.screen.blit(title_surf, title_surf.get_rect(center=(banner.centerx, banner.centery)))

    def draw_boss_intro(self):
        if not self.boss_intro:
            return
        self.boss_intro["timer"] -= 1
        if self.boss_intro["timer"] <= 0:
            self.boss_intro = None
            return
        alpha = min(220, self.boss_intro["timer"] * 3)
        dim = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(140, alpha)))
        self.screen.blit(dim, (0, 0))
        banner = pygame.Rect(config.SCREEN_WIDTH // 2 - 280, config.SCREEN_HEIGHT // 2 - 60, 560, 100)
        draw_panel(self.screen, banner, fill=(20, 12, 28), border=COLORS["danger"], radius=16, alpha=min(240, alpha + 20), shadow=True)
        title = self.fonts["title_sm"].render("БОСС", True, COLORS["danger"])
        self.screen.blit(title, title.get_rect(center=(banner.centerx, banner.y + 28)))
        name = self.fonts["hero"].render(self.boss_intro["name"], True, COLORS["text"])
        self.screen.blit(name, name.get_rect(center=(banner.centerx, banner.y + 62)))

    def draw_combat(self, accent):
        c = self.game.combat
        if not c:
            return

        rebuild_layouts(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        shake_x, shake_y = combat_shake_offset(c, self.anim)
        fx_positions = {}

        if c.sfx_callback is None:
            c.sfx_callback = self.audio.combat_sfx

        arena = COMBAT_LAYOUT["arena"]
        from mutators import pressure_turn
        pt = pressure_turn(c.run_mutators, get_difficulty().get("pressure_turn", 5), c.run_act)
        pressure_note = f" · Давление с хода {pt}" if c.turn < pt else f" · ⚠ Давление активно"
        deck = c.sync_deck()
        draw_top_bar(
            self.screen, self.fonts, "Бой", f"Ход {c.turn}{pressure_note}",
            stats=self.run_stats({"hp": c.player["hp"], "max_hp": c.player["max_hp"], "gold": c.player["gold"], "deck": deck}),
            accent=accent,
            energy=(c.player["energy"], c.player["max_energy"]),
            buttons=self.buttons,
            stat_clicks={"Колода": lambda: self.open_card_overlay(f"Колода ({len(deck)})", deck)},
        )
        potion_panel = draw_potion_bar(
            self.screen, self.fonts, c.potions, self.mouse, self.buttons,
            lambda idx: self.game.use_potion(idx) and self.audio.play("ui"),
            accent, used_this_turn=c.potion_used_this_turn, draw_icon=draw_potion_icon,
            panel_rect=COMBAT_LAYOUT.get("potions"),
        )
        self.highlight_rects["potions"] = potion_panel
        combat_relic_hits = draw_combat_relic_bar(self.screen, self.fonts, c.relics)
        draw_relic_tooltip(self.screen, self.fonts, self.mouse, [h for h in combat_relic_hits if h[1] != "overflow"])
        for rect, rid in combat_relic_hits:
            if rid == "overflow" and rect.collidepoint(self.mouse):
                hidden = c.relics[8:]
                tip_w = 220
                tip = pygame.Rect(min(self.mouse[0] + 14, config.SCREEN_WIDTH - tip_w - 12), self.mouse[1] + 14, tip_w, 20 + len(hidden) * 16)
                draw_panel(self.screen, tip, fill=(12, 16, 24), border=COLORS["gold"], radius=10, alpha=235, shadow=True)
                for j, hr in enumerate(hidden):
                    info = RELIC_DEFS.get(hr, {})
                    self.screen.blit(self.fonts["sm"].render(info.get("name", hr), True, info.get("color", COLORS["text"])), (tip.x + 10, tip.y + 8 + j * 16))
        self.highlight_rects["energy"] = pygame.Rect(COMBAT_LAYOUT["hud"].centerx - 50, COMBAT_LAYOUT["hud"].y + 18, 100, 36)

        draw_combat_arena(self.screen, accent)

        player_turn = c.is_player_turn and not self.game.combat_end_pending
        entity_h = self.combat_entity_h()
        entity_y = arena.y + config.sy(32) + shake_y
        living = c.living_enemies()
        player_w = min(config.sx(300), arena.width // 2 - config.sx(28))
        enemy_w = self.combat_entity_w(max(1, len(living)))
        arena_inset = config.sx(24)
        stage_top = entity_y + entity_h + config.sy(10)
        stage = pygame.Rect(arena.x + config.sx(14), stage_top, arena.width - config.sx(28), arena.bottom - stage_top - config.sy(12))
        stage_y = stage.centery - config.sy(48)
        player_sprite_x = stage.x + config.sx(32) + shake_x
        player_sprite_y = stage_y + shake_y
        player_center = (player_sprite_x + 48, player_sprite_y + 42)
        fx_positions["player"] = player_center

        def player_icon(surf, px, py, pw, ph):
            draw_player_sprite(surf, px, py, pw, ph)

        chip_hits = []
        draw_entity_panel(
            self.screen, self.fonts, "Страж Рубежа", c.player,
            arena.x + arena_inset + shake_x, entity_y, COLORS["accent"], player_icon,
            highlight=player_turn, chip_hits=chip_hits, w=player_w, h=entity_h,
        )

        enemy_gap = config.sx(12)
        enemy_x_start = arena.right - arena_inset - enemy_w
        if len(living) > 1:
            enemy_x_start = arena.right - arena_inset - len(living) * enemy_w - (len(living) - 1) * enemy_gap

        draw_arena_character(self.screen, player_sprite_x, player_sprite_y, 96, 100, "player", acting=player_turn)
        if c.pulse_key == "player" and c.pulse_timer > 0:
            draw_hit_pulse(self.screen, player_center, 58, c.pulse_timer, COLORS["danger"])

        for i, enemy in enumerate(living):
            ex = enemy_x_start + i * (enemy_w + enemy_gap)
            is_target = c.target_enemy() is enemy
            is_acting = c.is_active_enemy(enemy)
            enemy_key = c._target_key(enemy)

            def make_icon(eid=enemy.get("id", "slime"), col=enemy["color"]):
                return lambda surf, px, py, pw, ph: draw_enemy_sprite(surf, px, py, pw, ph, eid, col)

            rect = draw_entity_panel(
                self.screen, self.fonts, enemy["name"], enemy, ex + shake_x, entity_y, enemy["color"],
                make_icon(), enemy.get("intent"),
                draw_intent_icon, intent_label, intent_color, is_target, is_acting,
                chip_hits=chip_hits, next_intent=get_next_intent(enemy), w=enemy_w, h=entity_h,
            )
            if player_turn and not self.game.combat_end_pending:
                def pick_target(idx=i):
                    if c.target_index != idx:
                        c.target_index = idx
                        self.audio.play("ui")

                self.buttons.add(rect, pick_target, primary=False)
            if is_target and enemy.get("intent"):
                self.highlight_rects["enemy_intent"] = pygame.Rect(rect.right - 138, rect.y + 8, 128, 22)

            sx = ex + enemy_w // 2 - 48 + shake_x
            sy = stage_y + shake_y
            enemy_center = (sx + 48, sy + 42)
            fx_positions[enemy_key] = enemy_center
            draw_arena_character(self.screen, sx, sy, 96, 100, "enemy", enemy.get("id", "slime"), enemy["color"], is_acting)
            if is_target and player_turn:
                draw_target_marker(self.screen, enemy_center[0], enemy_center[1] + 52, self.anim, COLORS["gold"])
            if c.pulse_key == enemy_key and c.pulse_timer > 0:
                draw_hit_pulse(self.screen, enemy_center, 58, c.pulse_timer, COLORS["accent_warm"])

        draw_combat_chip_tooltip(self.screen, self.fonts, self.mouse, chip_hits)

        if c.action_banner and not player_turn:
            banner = pygame.Rect(stage.centerx - 170, stage.y + 6, 340, 30)
            draw_panel(self.screen, banner, fill=(40, 20, 20), border=COLORS["danger"], radius=10, alpha=220, shadow=False)
            txt = self.fonts["md"].render(c.action_banner, True, COLORS["text"])
            self.screen.blit(txt, txt.get_rect(center=banner.center))

        draw_combat_fx(self.screen, self.fonts, c.fx, fx_positions)

        if c.card_anim:
            target_pos = fx_positions.get(c.card_anim["target"])
            draw_flying_card(self.screen, self.fonts, c.card_anim, target_pos, draw_card_type_icon)

        _, deck_rect, discard_rect, scroll_rect = draw_combat_log(
            self.screen, self.fonts, c.log_lines, len(c.deck), len(c.discard),
            accent=accent, offset=self.combat_log_offset,
        )
        self.combat_log_rect = scroll_rect
        self.buttons.add(deck_rect, lambda: self.open_card_overlay(f"Колода ({len(c.deck)})", c.deck), primary=False)
        self.buttons.add(discard_rect, lambda: self.open_card_overlay(f"Сброс ({len(c.discard)})", c.discard), primary=False)
        draw_hand_tray(self.screen, self.fonts, accent=accent)

        hand_tray = COMBAT_LAYOUT["hand"]
        hand_clip = pygame.Rect(hand_tray.x + config.sx(4), hand_tray.y + config.sy(32), hand_tray.width - config.sx(8), hand_tray.height - config.sy(36))
        prev_hand_clip = self.screen.get_clip()
        self.screen.set_clip(hand_clip)

        sx, sy, cw, ch, gap = layout_hand_cards(len(c.hand))
        hand_rects = []
        for i, card in enumerate(c.hand):
            x = sx + i * (cw + gap)
            hotkey = i + 1 if player_turn and i < 9 else None

            def play(idx=i):
                self.try_play_hand_card(c, idx)

            rect = self.draw_card_ui(
                card, x, sy, cw, ch, c.can_play(card),
                play if player_turn else None, hand_idx=i, hotkey=hotkey,
            )
            if rect.collidepoint(self.mouse) or pygame.Rect(x, sy - 8, cw, ch + 8).collidepoint(self.mouse):
                self.hovered_card_energy = c.player["energy"]
            hand_rects.append(pygame.Rect(x, sy - 8, cw, ch + 8))

        if hand_rects:
            box = hand_rects[0].copy()
            for r in hand_rects[1:]:
                box = box.union(r)
            self.highlight_rects["hand"] = box

        self.screen.set_clip(prev_hand_clip)

        btn_target = layout_action_buttons()
        actions_content = draw_actions_bar(self.screen, self.fonts, accent=accent)
        living_count = len(living)

        if player_turn and living_count > 1:
            t_num = (c.target_index % living_count) + 1
            status = f"Цель {t_num}/{living_count}"
            draw_button(
                self.screen, self.fonts, btn_target, "Tab — цель",
                self.mouse, self.buttons,
                lambda: (setattr(c, "target_index", c.target_index + 1), self.audio.play("ui")),
                primary=False,
            )
            status_surf = self.fonts["sm"].render(status, True, COLORS["text_dim"])
            max_w = max(config.sx(60), btn_target.x - actions_content.x - config.sx(10))
            if status_surf.get_width() > max_w:
                status = f"{t_num}/{living_count}"
                status_surf = self.fonts["sm"].render(status, True, COLORS["text_dim"])
            self.screen.blit(status_surf, status_surf.get_rect(midleft=(actions_content.x, actions_content.centery)))
        elif not player_turn:
            wait_txt = self.fonts["md"].render(c.action_banner or "Враги действуют...", True, COLORS["text_dim"])
            self.screen.blit(wait_txt, wait_txt.get_rect(center=actions_content.center))

    def draw_reward(self, accent=None):
        accent = accent or COLORS["accent"]
        draw_top_bar(self.screen, self.fonts, "Награда", "Выбери карту или пропусти", stats=self.run_stats(self.game.run), accent=accent)
        self.draw_deck_button(self.game.run)
        cards = self.game.reward_cards
        sync_discovered_cards(self.game.meta, cards)
        panel, sx, sy, cw, ch, gap = layout_reward_cards(len(cards))
        draw_section_panel(self.screen, panel, "Новые карты", self.fonts, accent=accent, alpha=180)
        rects = []
        for i, card in enumerate(cards):
            rx = sx + i * (cw + gap)
            self.draw_card_ui(card, rx, sy, cw, ch, True, lambda idx=i: self.game.pick_reward(idx))
            rects.append(pygame.Rect(rx, sy - 8, cw, ch + 8))
        if rects:
            box = rects[0].copy()
            for r in rects[1:]:
                box = box.union(r)
            self.highlight_rects["reward_cards"] = box
        actions = pygame.Rect(config.SCREEN_WIDTH // 2 - 140, 530, 280, 44)
        draw_section_panel(self.screen, actions, "Решение", self.fonts, accent=COLORS["panel_border"], alpha=200)
        draw_button(self.screen, self.fonts, pygame.Rect(actions.centerx - 110, actions.y + 4, 220, 36), "Пропустить", self.mouse, self.buttons, lambda: self.game.pick_reward(-1), primary=False)

    def draw_rest(self, accent):
        from cards import removable_cards
        from potions import can_add_potion

        heal = max(get_difficulty()["rest_heal"], int(self.game.run["max_hp"] * get_difficulty()["rest_heal_pct"]))
        can_remove = bool(removable_cards(self.game.run["deck"]))
        can_brew = can_add_potion(self.game.run) and self.game.run["hp"] > 12
        draw_top_bar(self.screen, self.fonts, "Привал", "Огонь потрескивает в темноте", stats=self.run_stats(self.game.run), accent=accent)
        self.draw_deck_button(self.game.run)
        camp = pygame.Rect(config.SCREEN_WIDTH // 2 - 260, 118, 520, 400)
        content = draw_section_panel(self.screen, camp, "Лагерь", self.fonts, accent=COLORS["accent_warm"], alpha=190)
        fire = pygame.Rect(content.centerx - 90, content.y + 12, 180, 150)
        draw_panel(self.screen, fire, fill=(20, 14, 10), border=COLORS["accent_warm"], radius=80, alpha=200, shadow=False)
        draw_rest_campfire(self.screen, fire.x + 20, fire.y + 20, fire.width - 40, fire.height - 40)
        draw_button(self.screen, self.fonts, pygame.Rect(content.x + 24, content.bottom - 238, content.width - 48, 48), f"Отдохнуть (+{heal} HP)", self.mouse, self.buttons, self.game.rest_heal)
        self.highlight_rects["rest_options"] = pygame.Rect(content.x + 24, content.bottom - 178, content.width - 48, 120).inflate(0, 20)
        half_w = (content.width - 56) // 2
        draw_button(self.screen, self.fonts, pygame.Rect(content.x + 24, content.bottom - 178, half_w, 48), "Улучшить карту", self.mouse, self.buttons, self.game.rest_upgrade, primary=False)
        remove_cb = self.game.rest_remove if can_remove else lambda: None
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.x + 32 + half_w, content.bottom - 178, half_w, 48),
            "Удалить карту" if can_remove else "Нельзя удалить",
            self.mouse, self.buttons, remove_cb, primary=False,
        )
        brew_cb = self.game.rest_brew if can_brew else lambda: None
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.x + 24, content.bottom - 118, content.width - 48, 48),
            "Сварить зелье (−12 HP)" if can_brew else "Зелья: пояс полон или мало HP",
            self.mouse, self.buttons, brew_cb, primary=False,
        )
        if not can_remove:
            hint = self.fonts["sm"].render("Минимум 5 карт в колоде (проклятия — исключение)", True, COLORS["text_dim"])
            self.screen.blit(hint, hint.get_rect(center=(content.centerx, content.bottom - 58)))

    def draw_rest_remove(self, accent):
        from_shop = self.game.after_remove_screen == SHOP
        title = "Очищение в лавке" if from_shop else "Очищение"
        hint = "Выбери карту для удаления (платно)" if from_shop else "Выбери карту для удаления из колоды"
        draw_top_bar(self.screen, self.fonts, title, hint, stats=self.run_stats(self.game.run), accent=COLORS["accent_warm"])
        self.draw_deck_button(self.game.run)
        cards = self.game.remove_choices
        pending = self.game.pending_remove_index

        if pending is not None and 0 <= pending < len(cards):
            card = cards[pending]
            panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 220, 180, 440, 320)
            draw_section_panel(self.screen, panel, "Подтверждение", self.fonts, accent=COLORS["danger"], alpha=220)
            self.draw_card_ui(card, panel.centerx - 64, panel.y + 48, 128, 132, True, None)
            warn = self.fonts["md"].render(f"Удалить «{card['name']}» навсегда?", True, COLORS["text"])
            self.screen.blit(warn, warn.get_rect(center=(panel.centerx, panel.y + 200)))
            if self.game.remove_cost > 0:
                cost = self.fonts["sm"].render(f"Стоимость: {self.game.remove_cost} золота", True, COLORS["gold"])
                self.screen.blit(cost, cost.get_rect(center=(panel.centerx, panel.y + 228)))
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(panel.centerx - 190, panel.bottom - 58, 180, 42),
                "Удалить", self.mouse, self.buttons,
                lambda: (self.audio.play("ui"), self.game.confirm_rest_remove()),
            )
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(panel.centerx + 10, panel.bottom - 58, 180, 42),
                "Отмена", self.mouse, self.buttons,
                lambda: setattr(self.game, "pending_remove_index", None),
                primary=False,
            )
            return

        panel = pygame.Rect(40, 118, config.SCREEN_WIDTH - 80, 392)
        draw_section_panel(self.screen, panel, "Удаление", self.fonts, accent=COLORS["danger"], alpha=180)
        cw, ch, gap = 128, 132, 14
        cols = min(6, max(1, len(cards)))
        rows = (len(cards) + cols - 1) // cols
        total_w = cols * cw + (cols - 1) * gap
        sx = panel.x + max(20, (panel.width - total_w) // 2)
        sy = panel.y + 48
        for i, card in enumerate(cards):
            col = i % cols
            row = i // cols
            x = sx + col * (cw + gap)
            y = sy + row * (ch + gap)
            self.draw_card_ui(card, x, y, cw, ch, True, lambda idx=i: self.game.select_rest_remove(idx))
        draw_button(self.screen, self.fonts, pygame.Rect(config.SCREEN_WIDTH // 2 - 100, 530, 200, 40), "Отмена", self.mouse, self.buttons, self.game.cancel_rest_remove, primary=False)

    def pick_rest_remove(self, index):
        self.audio.play("ui")
        self.game.select_rest_remove(index)

    def draw_act_transition(self, accent):
        run = self.game.run
        act = get_act_info(run["act"])
        draw_top_bar(self.screen, self.fonts, f"Акт {run['act'] + 1}", act["name"], stats=self.run_stats(run), accent=act["color"])
        self.draw_deck_button(run)
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 320, 120, 640, 420)
        content = draw_section_panel(self.screen, panel, "Новый Рубеж", self.fonts, accent=act["color"], alpha=220)
        hero = pygame.Rect(content.x + 24, content.y + 16, content.width - 48, 180)
        draw_panel(self.screen, hero, fill=(8, 12, 20), border=act["color"], radius=16, alpha=210, shadow=False)
        draw_menu_hero(self.screen, hero.x + 40, hero.y + 20, hero.width - 80, hero.height - 40)
        lore = self.ACT_LORE.get(run["act"], "Впереди — новые испытания Рубежа.")
        wrap_text(self.screen, self.fonts["md"], lore, content.x + 32, content.y + 210, content.width - 64, COLORS["text"], line_h=26)
        heal_note = self.fonts["sm"].render("После победы над боссом ты восстановил часть сил.", True, COLORS["success"])
        self.screen.blit(heal_note, heal_note.get_rect(center=(content.centerx, content.y + 300)))
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.centerx - 110, content.bottom - 58, 220, 48),
            "Вперёд", self.mouse, self.buttons,
            lambda: (self.audio.play("ui"), self.game.continue_act()),
        )

    def draw_rest_upgrade(self, accent):
        from collections import Counter

        draw_top_bar(self.screen, self.fonts, "Кузница", "Выбери одну карту для усиления", stats=self.run_stats(self.game.run), accent=COLORS["accent_warm"])
        self.draw_deck_button(self.game.run)
        cards = self.game.upgrade_choices
        id_counts = Counter(c["id"] for c in self.game.run.get("deck", []))
        panel, sx, sy, cw, ch, gap, cols = layout_card_grid(len(cards), top=118, bottom_pad=58)
        draw_section_panel(self.screen, panel, "Улучшение", self.fonts, accent=COLORS["accent_warm"], alpha=180)
        preview_card = None
        preview_data = None
        hover_rect = None
        for i, card in enumerate(cards):
            col = i % cols
            row = i // cols
            x = sx + col * (cw + gap)
            y = sy + row * (ch + gap)
            card_rect = pygame.Rect(x, y, cw, ch)
            if card_rect.collidepoint(self.mouse):
                preview_data = preview_upgrade(card)
                if preview_data:
                    preview_card = card
                    hover_rect = card_rect
            self.draw_card_ui(card, x, y, cw, ch, True, lambda idx=i: self.pick_rest_upgrade(idx))
            count = id_counts.get(card["id"], 1)
            if count > 1:
                badge = self.fonts["sm"].render(f"×{count}", True, COLORS["gold"])
                badge_bg = pygame.Rect(x + cw - badge.get_width() - 10, y + 6, badge.get_width() + 8, badge.get_height() + 4)
                pygame.draw.rect(self.screen, (20, 16, 8), badge_bg, border_radius=6)
                pygame.draw.rect(self.screen, COLORS["gold"], badge_bg, 1, border_radius=6)
                self.screen.blit(badge, (badge_bg.x + 4, badge_bg.y + 2))

        if preview_card and preview_data and hover_rect:
            px, py = position_upgrade_preview(hover_rect)
            draw_upgrade_preview(self.screen, self.fonts, preview_card, preview_data, px, py, draw_card_type_icon)

        cancel_y = panel.bottom + config.sy(10)
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(config.SCREEN_WIDTH // 2 - 100, cancel_y, 200, 40),
            "Отмена", self.mouse, self.buttons, self.game.cancel_rest_remove, primary=False,
        )

    def pick_rest_upgrade(self, index):
        self.audio.play("ui")
        self.upgrade_flash = 20
        self.game.pick_rest_upgrade(index)

    def draw_upgrade_flash(self):
        if self.upgrade_flash <= 0:
            return
        self.upgrade_flash -= 1
        alpha = int(100 * (self.upgrade_flash / 20))
        flash = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        flash.fill((*COLORS["accent_warm"], alpha))
        self.screen.blit(flash, (0, 0))

    def draw_relic_reward(self, accent):
        action = self.game.post_relic_action
        subtitle = "Награда босса" if action == "boss_advance" else "Награда элиты"
        draw_top_bar(self.screen, self.fonts, "Реликвия", "Выбери один артефакт", stats=self.run_stats(self.game.run), accent=COLORS["gold"])
        self.draw_deck_button(self.game.run)
        relics = self.game.relic_choices
        panel = pygame.Rect(80, 118, config.SCREEN_WIDTH - 160, 400)
        content = draw_section_panel(self.screen, panel, subtitle, self.fonts, accent=COLORS["gold"], alpha=190)
        slot_w = (content.width - 80) // max(1, len(relics))
        if relics:
            box = pygame.Rect(content.x + 20, content.y + 16, content.width - 40, content.height - 80)
            self.highlight_rects["relic_choices"] = box
        for i, rid in enumerate(relics):
            info = RELIC_DEFS[rid]
            rx = content.x + 20 + i * slot_w
            box = pygame.Rect(rx, content.y + 16, slot_w - 20, content.height - 80)
            draw_panel(self.screen, box, fill=(12, 16, 24), border=info["color"], radius=14, alpha=220, shadow=False)
            draw_relic_icon(self.screen, box.centerx - 28, box.y + 16, 56, rid)
            title = self.fonts["md"].render(info["name"], True, info["color"])
            self.screen.blit(title, title.get_rect(center=(box.centerx, box.y + 88)))
            wrap_text(self.screen, self.fonts["sm"], info["desc"], box.x + 12, box.y + 110, box.width - 24, COLORS["text_dim"], line_h=16)
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(box.x + 12, box.bottom - 44, box.width - 24, 36),
                "Взять", self.mouse, self.buttons,
                lambda idx=i: self.pick_relic_reward(idx),
            )
        actions = pygame.Rect(config.SCREEN_WIDTH // 2 - 140, 530, 280, 44)
        draw_section_panel(self.screen, actions, "Решение", self.fonts, accent=COLORS["panel_border"], alpha=200)
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(actions.centerx - 110, actions.y + 4, 220, 36),
            "Отказаться", self.mouse, self.buttons,
            lambda: self.pick_relic_reward(-1),
            primary=False,
        )

    def pick_relic_reward(self, index):
        self.audio.play("power")
        self.relic_flash = 24
        self.game.pick_relic(index)

    def leave_shop(self):
        self.game.tutorial.advance("shop_action")
        self.game.screen = MAP
        self.game._persist()

    def draw_relic_flash(self):
        if self.relic_flash <= 0:
            return
        self.relic_flash -= 1
        alpha = int(120 * (self.relic_flash / 24))
        flash = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        flash.fill((*COLORS["gold"], alpha))
        self.screen.blit(flash, (0, 0))

    def draw_achievement_toasts(self):
        for i, toast in enumerate(self.toasts[:4]):
            draw_achievement_toast(self.screen, self.fonts, toast["id"], toast["timer"], y_offset=i * 78)

    def draw_shop(self, accent):
        draw_top_bar(self.screen, self.fonts, "Лавка Странника", "Карты, зелья, артефакты и удаление из колоды", stats=self.run_stats(self.game.run), accent=accent)
        self.draw_deck_button(self.game.run)
        draw_shop_banner(self.screen, 56, 108, 180, 72)
        items = self.game.shop_items
        card_items = [item for item in items if item.get("type") == "card"]
        sync_discovered_cards(self.game.meta, [item["card"] for item in card_items if "card" in item])
        panel, sx, sy, cw, ch, gap = layout_shop_cards(len(items))
        draw_section_panel(self.screen, panel, "Товар", self.fonts, accent=accent, alpha=160)
        shop_rects = []
        for i, item in enumerate(items):
            x = sx + i * (cw + gap)
            can = self.game.run["gold"] >= item["price"]

            def try_buy(idx=i):
                item = self.game.shop_items[idx]
                if self.game.run["gold"] < item["price"]:
                    self.audio.play("hurt")
                    return
                if item.get("type") == "potion":
                    from potions import can_add_potion
                    if not can_add_potion(self.game.run):
                        self.audio.play("buzz")
                        return
                self.audio.play("card" if item.get("type") != "relic" else "achievement")
                self.game.buy_shop_item(idx)

            if item.get("type") == "relic":
                rid = item["relic_id"]
                info = RELIC_DEFS.get(rid, {})
                slot = pygame.Rect(x, sy, cw, ch)
                hovered = slot.collidepoint(self.mouse)
                draw_panel(self.screen, slot, fill=(20, 16, 28), border=info.get("color", COLORS["gold"]), radius=12, alpha=220 if hovered else 180, shadow=hovered)
                draw_relic_icon(self.screen, x + cw // 2 - 28, sy + 24, 56, rid)
                name = self.fonts["card"].render(info.get("name", rid)[:16], True, COLORS["text"])
                self.screen.blit(name, name.get_rect(center=(x + cw // 2, sy + ch - 36)))
                tag = self.fonts["sm"].render("Артефакт", True, COLORS["gold"])
                self.screen.blit(tag, tag.get_rect(center=(x + cw // 2, sy + 12)))
                if can:
                    self.buttons.add(slot, try_buy)
                shop_rects.append(slot.inflate(0, 8))
            elif item.get("type") == "potion":
                pid = item["potion_id"]
                info = POTION_DEFS.get(pid, {})
                slot = pygame.Rect(x, sy, cw, ch)
                hovered = slot.collidepoint(self.mouse)
                draw_panel(self.screen, slot, fill=(16, 20, 28), border=info.get("color", accent), radius=12, alpha=220 if hovered else 180, shadow=hovered)
                draw_potion_icon(self.screen, x + cw // 2 - 28, sy + 24, 56, pid)
                name = self.fonts["card"].render(info.get("name", pid)[:16], True, COLORS["text"])
                self.screen.blit(name, name.get_rect(center=(x + cw // 2, sy + ch - 36)))
                tag = self.fonts["sm"].render("Зелье", True, COLORS["success"])
                self.screen.blit(tag, tag.get_rect(center=(x + cw // 2, sy + 12)))
                if can:
                    from potions import can_add_potion
                    if can_add_potion(self.game.run):
                        self.buttons.add(slot, try_buy)
                shop_rects.append(slot.inflate(0, 8))
            else:
                self.draw_card_ui(item["card"], x, sy, cw, ch, can, try_buy)
                shop_rects.append(pygame.Rect(x, sy - 8, cw, ch + 8))
            price_panel = pygame.Rect(x + 16, sy + ch + 10, cw - 32, 28)
            draw_panel(self.screen, price_panel, fill=(20, 16, 8), border=COLORS["gold"], radius=8, alpha=200, shadow=False)
            price = self.fonts["md"].render(f"{item['price']} золота", True, COLORS["gold"])
            self.screen.blit(price, price.get_rect(center=price_panel.center))
        if shop_rects:
            box = shop_rects[0].copy()
            for r in shop_rects[1:]:
                box = box.union(r)
            self.highlight_rects["shop_cards"] = box
        footer = pygame.Rect(config.SCREEN_WIDTH // 2 - config.sx(280), config.sy(540), config.sx(560), config.sy(44))
        draw_section_panel(self.screen, footer, "Лавка", self.fonts, accent=COLORS["panel_border"], alpha=200)
        removal_price = shop_removal_price()
        from difficulty import shop_price
        heal_price = shop_price(55)
        heal_amt = max(10, int(self.game.run["max_hp"] * 0.22))
        can_remove = (
            not self.game.run.get("shop_removal_used")
            and len(self.game.run.get("deck", [])) > 5
            and self.game.run["gold"] >= removal_price
        )
        can_heal = (
            not self.game.run.get("shop_heal_used")
            and self.game.run["gold"] >= heal_price
            and self.game.run["hp"] < self.game.run["max_hp"]
        )
        btn_w = footer.width // 3 - 14
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(footer.x + 12, footer.y + 4, btn_w, 36),
            f"Лечение +{heal_amt} ({heal_price} з.)" if not self.game.run.get("shop_heal_used") else "Лечение куплено",
            self.mouse, self.buttons,
            lambda: (self.audio.play("ui"), self.game.shop_heal()) if can_heal else self.audio.play("buzz"),
            primary=False,
        )
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(footer.x + 12 + btn_w + 8, footer.y + 4, btn_w, 36),
            f"Удалить ({removal_price} з.)" if not self.game.run.get("shop_removal_used") else "Удаление куплено",
            self.mouse, self.buttons,
            lambda: (self.audio.play("ui"), self.game.shop_remove()) if can_remove else self.audio.play("buzz"),
            primary=False,
        )
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(footer.right - btn_w - 12, footer.y + 4, btn_w, 36),
            "Уйти", self.mouse, self.buttons, self.leave_shop,
        )

    def draw_event(self, accent=None):
        accent = accent or COLORS["accent_warm"]
        ev = self.game.current_event
        event_id = ev.get("id", "campfire")
        draw_top_bar(self.screen, self.fonts, ev["title"], "Судьбоносный выбор", stats=self.run_stats(self.game.run), accent=accent)
        self.draw_deck_button(self.game.run)

        scene = pygame.Rect(80, 108, config.SCREEN_WIDTH - 160, 420)
        content = draw_section_panel(self.screen, scene, "Событие", self.fonts, accent=accent, alpha=195)

        art = pygame.Rect(content.x + 20, content.y + 12, 280, 200)
        draw_panel(self.screen, art, fill=(8, 10, 16), border=accent, radius=14, alpha=220, shadow=False)
        draw_event_scene(self.screen, art.x + 8, art.y + 8, art.width - 16, art.height - 16, event_id)

        text_panel = pygame.Rect(content.x + 316, content.y + 12, content.width - 336, 200)
        draw_panel(self.screen, text_panel, fill=(14, 18, 28), border=COLORS["panel_border"], radius=14, alpha=220, shadow=False)
        wrap_text(self.screen, self.fonts["md"], ev["text"], text_panel.x + 18, text_panel.y + 18, text_panel.width - 36, COLORS["text"], line_h=24)

        choice_y = content.y + 228
        choice_w = (content.width - 56) // 2
        for i, choice in enumerate(ev["choices"]):
            label = choice[0]
            hint = choice[2] if len(choice) > 2 else ""
            cx = content.x + 20 + (i % 2) * (choice_w + 16)
            cy = choice_y + (i // 2) * 72
            draw_button(
                self.screen, self.fonts,
                pygame.Rect(cx, cy, choice_w, 48), label, self.mouse, self.buttons,
                lambda idx=i: self.pick_event_choice(idx),
                primary=(i == 0),
            )
            if hint:
                hint_txt = self.fonts["sm"].render(hint, True, COLORS["text_dim"])
                self.screen.blit(hint_txt, hint_txt.get_rect(center=(cx + choice_w // 2, cy + 58)))

    def draw_gold_popup(self):
        if not self.gold_popup or self.gold_popup["timer"] <= 0:
            return
        t = self.gold_popup["timer"]
        alpha = min(255, int(255 * min(1.0, t / 30)))
        amount = self.gold_popup.get("amount", 0)
        potion = self.gold_popup.get("potion")
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 140, 88, 280, 44)
        draw_panel(self.screen, panel, fill=(20, 16, 8), border=COLORS["gold"] if amount else COLORS["success"], radius=12, alpha=alpha, shadow=True)
        if potion and amount:
            txt = self.fonts["md"].render(f"+{amount} золота · {potion}", True, COLORS["gold"])
        elif potion:
            txt = self.fonts["md"].render(f"Зелье: {potion}", True, COLORS["success"])
        else:
            txt = self.fonts["md"].render(f"+{amount} золота", True, COLORS["gold"])
        self.screen.blit(txt, txt.get_rect(center=panel.center))

    def draw_event_popup(self):
        if not self.event_popup or self.event_popup["timer"] <= 0:
            return
        t = self.event_popup["timer"]
        alpha = min(255, int(255 * min(1.0, t / 30)))
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 180, 88, 360, 44)
        draw_panel(self.screen, panel, fill=(14, 18, 28), border=COLORS["accent"], radius=12, alpha=alpha, shadow=True)
        txt = self.fonts["md"].render(self.event_popup["text"], True, COLORS["text"])
        self.screen.blit(txt, txt.get_rect(center=panel.center))

    def pick_event_choice(self, index):
        self.audio.play("ui")
        self.game.pick_event(index)
        if self.game.event_result:
            self.event_popup = {"text": self.game.event_result, "timer": 120}
            self.game.event_result = None

    def draw_end(self, victory):
        accent = COLORS["gold"] if victory else COLORS["danger"]
        title = "Победа!" if victory else "Поражение"
        panel = pygame.Rect(config.SCREEN_WIDTH // 2 - 310, 78, 620, 600)
        content = draw_section_panel(self.screen, panel, title, self.fonts, accent=accent, alpha=225)

        sprite_y = content.y + 10
        if victory:
            draw_player_sprite(self.screen, content.centerx - 52, sprite_y, 104, 112)
        else:
            draw_enemy_sprite(self.screen, content.centerx - 52, sprite_y, 104, 112, "wraith")

        run = self.game.run
        sub = "Рубеж устоял благодаря тебе" if victory else "Тьма поглотила тебя на этот раз"
        if victory and run and run.get("daily"):
            sub = "Ежедневный Рубеж пройден!"
        sub_surf = self.fonts["md"].render(sub, True, COLORS["text_dim"])
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(content.centerx, content.y + 138)))

        stats_box = pygame.Rect(content.x + 24, content.y + 168, content.width - 48, 130)
        draw_panel(self.screen, stats_box, fill=(12, 16, 24), border=accent, radius=14, alpha=210, shadow=False)
        lines = [f"Всего побед: {self.game.meta.get('wins', 0)}"]
        if run:
            if victory:
                vs = self.game.last_victory_stats or {}
                diff_name = {"border": "Рубеж", "harsh": "Суровый Рубеж", "nightmare": "Кошмар"}.get(vs.get("difficulty", self.game.meta.get("difficulty", "harsh")), "Рубеж")
                lines.extend([
                    f"Пройдено актов: {run['act'] + 1}",
                    f"Боёв выиграно: {self.game.combats_won}",
                    f"Сложность: {diff_name}",
                    f"Золото: {run['gold']}  ·  Колода: {len(run.get('deck', []))} карт",
                ])
                if vs.get("potions_used"):
                    lines.append(f"Зелий использовано: {vs['potions_used']}")
                if vs.get("mutators"):
                    from mutators import MUTATOR_DEFS
                    mut = MUTATOR_DEFS.get(vs["mutators"][0], {}).get("name", "")
                    if mut:
                        lines.append(f"Модификатор: {mut}")
            else:
                act = get_act_info(run["act"])
                lines.extend([
                    f"Акт: {act['name']}",
                    f"Боёв выиграно: {self.game.combats_won}",
                    f"Золото: {run['gold']}  ·  Колода: {len(run.get('deck', []))} карт",
                ])
        for i, line in enumerate(lines):
            color = accent if i == 0 and victory else COLORS["text"]
            self.screen.blit(self.fonts["md"].render(line, True, color), (stats_box.x + 20, stats_box.y + 14 + i * 24))

        if run and run.get("relics"):
            relic_box = pygame.Rect(content.x + 24, content.y + 282, content.width - 48, 110)
            draw_panel(self.screen, relic_box, fill=(12, 16, 24), border=COLORS["gold"], radius=14, alpha=210, shadow=False)
            self.screen.blit(self.fonts["sm"].render("Реликвии забега", True, COLORS["gold"]), (relic_box.x + 16, relic_box.y + 10))
            relic_hits = draw_relic_strip(self.screen, self.fonts, run["relics"], relic_box.x + 16, relic_box.y + 36, max_count=8, size=24)
            draw_relic_tooltip(self.screen, self.fonts, self.mouse, relic_hits)
            names_y = relic_box.y + 72
            for i, rid in enumerate(run["relics"][:4]):
                info = RELIC_DEFS.get(rid, {})
                self.screen.blit(
                    self.fonts["sm"].render(info.get("name", rid), True, info.get("color", COLORS["text_dim"])),
                    (relic_box.x + 16 + i * 140, names_y),
                )

        if victory:
            for i in range(6):
                px = content.x + 40 + i * 90
                py = content.bottom - 120 + int(math.sin(self.anim * 2 + i) * 6)
                pygame.draw.circle(self.screen, (accent[0] // 2, accent[1] // 2, accent[2] // 3), (px, py), 4)

        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.centerx - 290, content.bottom - 58, 280, 48),
            "Новый забег", self.mouse, self.buttons,
            lambda: (self.audio.play("ui"), self.request_new_run()),
            primary=victory,
        )
        draw_button(
            self.screen, self.fonts,
            pygame.Rect(content.centerx + 10, content.bottom - 58, 280, 48),
            "В меню", self.mouse, self.buttons, self.game.to_menu,
            primary=not victory,
        )


def main():
    App().run()


if __name__ == "__main__":
    main()
