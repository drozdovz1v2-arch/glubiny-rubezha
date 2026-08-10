from cards import can_add_card_to_deck, deck_card_ids, removable_cards, roll_card_rewards, shop_removal_price, starter_deck, sync_discovered_cards, unique_upgradable_cards, upgrade_card
from combat import CombatState
from config import ACTS, clear_run_save, daily_seed, load_meta, save_meta, save_run_state
from difficulty import get_difficulty, gold_reward, init_difficulty
from enemies import roll_ambush_enemies, roll_battle_enemies, roll_boss
from mapgen import flatten_map, generate_map, get_act_info, get_node, layout_map, roll_event, visit_node
from relics import add_relic, apply_combat_end, discover_relic, roll_relic_rewards, shop_inventory, sync_discovered_relics
from achievements import check_meta_achievements, on_boss_relic, on_daily_win, on_potion_used, on_rest_upgrade, on_shop_remove, on_victory, set_achievement_listener
from tutorial import Tutorial

MENU = "menu"
HELP = "help"
SETTINGS = "settings"
CODEX = "codex"
ACHIEVEMENTS = "achievements"
TUTORIAL = "tutorial"
MAP = "map"
COMBAT = "combat"
REWARD = "reward"
RELIC_REWARD = "relic_reward"
REST = "rest"
REST_UPGRADE = "rest_upgrade"
REST_REMOVE = "rest_remove"
SHOP = "shop"
EVENT = "event"
ACT_TRANSITION = "act_transition"
VICTORY = "victory"
DEFEAT = "defeat"

PERSIST_SCREENS = {MAP, REST, REST_UPGRADE, REST_REMOVE, SHOP, EVENT, REWARD, ACT_TRANSITION}


class Game:
    def __init__(self):
        self.meta = load_meta()
        init_difficulty(self.meta)
        self.tutorial = Tutorial(self.meta)
        self.screen = MENU
        self.run = None
        self.combat = None
        self.reward_cards = []
        self.relic_choices = []
        self.upgrade_choices = []
        self.remove_choices = []
        self.post_relic_action = None
        self.shop_items = []
        self.current_event = None
        self.combats_won = 0
        self.pending_toasts = []
        self.last_gold_gain = 0
        self.last_potion_gain = None
        self.last_victory_stats = None
        self.combat_end_pending = None
        self.combat_end_timer = 0
        self.event_result = None
        self.pending_remove_index = None
        self.after_remove_screen = MAP
        self.remove_cost = 0
        set_achievement_listener(self._queue_toast)
        check_meta_achievements(self.meta)

    def _queue_toast(self, ach_id):
        self.pending_toasts.append(ach_id)

    def pop_toasts(self):
        items = self.pending_toasts[:]
        self.pending_toasts = []
        return items

    def _persist(self):
        if not self.run or self.screen not in PERSIST_SCREENS:
            return
        save_run_state(self.meta, {
            "run": self.run,
            "screen": self.screen,
            "combats_won": self.combats_won,
            "shop_items": self.shop_items,
        })

    def continue_run(self):
        payload = self.meta.get("run_save")
        if not payload or not payload.get("run"):
            return False
        self.run = payload["run"]
        self.screen = payload.get("screen", MAP)
        self.combats_won = payload.get("combats_won", 0)
        self.shop_items = payload.get("shop_items", [])
        self.combat = None
        layout_map(self.run["map"])
        sync_discovered_relics(self.meta, self.run.get("relics", []))
        sync_discovered_cards(self.meta, self.run.get("deck", []))
        return True

    def _record_run_stats(self, won):
        if not self.run:
            return
        if won and self.run["act"] >= len(ACTS) - 1:
            progress = len(ACTS)
        else:
            progress = self.run["act"] + 1
        self.meta["best_act"] = max(self.meta.get("best_act", 0), progress)
        self.meta["best_combats"] = max(self.meta.get("best_combats", 0), self.combats_won)
        sync_discovered_relics(self.meta, self.run.get("relics", []))
        check_meta_achievements(self.meta)
        save_meta(self.meta)

    def new_run(self, daily=False):
        clear_run_save(self.meta)
        self.meta["runs"] = self.meta.get("runs", 0) + 1
        save_meta(self.meta)
        self.combats_won = 0
        d = get_difficulty()
        self.run = {
            "hp": d["player_hp"],
            "max_hp": d["player_max_hp"],
            "gold": d["starting_gold"],
            "deck": starter_deck(),
            "act": 0,
            "map": generate_map(0),
            "current_node": None,
            "bonus_energy": 0,
            "relics": [],
            "potions": [],
            "potions_used": 0,
            "mutators": [],
            "daily": daily,
        }
        if daily:
            from mutators import roll_daily_mutators
            self.run["mutators"] = roll_daily_mutators(daily_seed())
            self.run["oath"] = "none"
        else:
            self.run["oath"] = self.meta.get("oath", "none")
        from mutators import apply_start_modifiers
        apply_start_modifiers(self.run)
        layout_map(self.run["map"])
        sync_discovered_cards(self.meta, self.run["deck"])
        self.screen = MAP
        self.tutorial.advance("click_new_run")
        self._persist()

    def select_node(self, node_id):
        node = get_node(self.run["map"], node_id)
        if not node or not node["available"] or node["visited"]:
            return
        self.run["current_node"] = node
        self.tutorial.advance("click_node")
        t = node["type"]
        if t in ("battle", "elite"):
            self.start_combat(elite=(t == "elite"))
        elif t == "boss":
            self.start_boss()
        else:
            visit_node(self.run["map"], node_id)
            if t == "rest":
                self.screen = REST
            elif t == "shop":
                self.shop_items = shop_inventory(
                    self.run["act"],
                    self.run.get("relics", []),
                    deck_card_ids(self.run.get("deck", [])),
                )
                self.run["shop_removal_used"] = False
                self.run["shop_heal_used"] = False
                self.screen = SHOP
            elif t == "event":
                self.current_event = roll_event(self.run["act"])
                self.screen = EVENT
            self._persist()

    def start_combat(self, elite=False, ambush=False):
        biome = get_act_info(self.run["act"])["biome"]
        from mutators import run_modifiers
        from mapgen import map_node_tier

        mods = run_modifiers(self.run)
        node = self.run.get("current_node") or {}
        map_tier = node.get("tier") or map_node_tier(node.get("row", 99))
        if ambush:
            enemies = roll_ambush_enemies(biome, self.run["act"], self.combats_won, mods)
        else:
            enemies = roll_battle_enemies(
                biome, elite, self.run["act"], self.combats_won, mods, map_tier=map_tier,
            )
        self.combat = CombatState(self.run, enemies)
        if ambush:
            self.combat.log("⚠ Засада! Враги ослаблены, но их несколько.")
        elif any(e.get("hunter") for e in enemies):
            self.combat.log("⚠ Охотник Рубежа — особая добыча, особая опасность!")
        self.combat.start_turn()
        self.screen = COMBAT

    def start_boss(self):
        from mutators import run_modifiers
        enemies = roll_boss(self.run["act"], self.combats_won, run_modifiers(self.run))
        self.combat = CombatState(self.run, enemies)
        self.combat.start_turn()
        self.screen = COMBAT

    def finish_combat(self):
        if not self.combat or self.combat.finished:
            return
        self.combat.finished = True
        self.run["hp"] = self.combat.player["hp"]
        self.run["deck"] = self.combat.sync_deck()
        self.run["potions"] = list(self.combat.potions)
        node = self.run.get("current_node") or {}
        is_hunter = any(e.get("hunter") for e in self.combat.enemies)
        reward_type = "hunter" if is_hunter else node.get("type", "battle")
        gain = gold_reward(reward_type)
        from mutators import gold_mult, run_modifiers
        gain = max(8, int(gain * gold_mult(run_modifiers(self.run))))
        self.last_gold_gain = gain
        self.last_potion_gain = None
        self.run["gold"] += gain
        apply_combat_end(self.run, self.run.get("relics", []), reward_type)

        if self.combat.won:
            node = self.run.get("current_node") or {}
            if node.get("id"):
                visit_node(self.run["map"], node["id"])
            self.combats_won += 1
            node_type = node.get("type", "battle")
            if node_type == "boss":
                if self.run["act"] >= len(ACTS) - 1:
                    self.meta["wins"] = self.meta.get("wins", 0) + 1
                    save_meta(self.meta)
                    if self.tutorial.active:
                        self.tutorial.complete()
                    clear_run_save(self.meta)
                    self._record_run_stats(True)
                    on_victory(self.meta, self.meta.get("difficulty", "harsh"), self.run)
                    if self.run.get("daily"):
                        on_daily_win(self.meta)
                    self.last_victory_stats = {
                        "difficulty": self.meta.get("difficulty", "harsh"),
                        "mutators": list(self.run.get("mutators", [])),
                        "combats_won": self.combats_won,
                        "potions_used": self.run.get("potions_used", 0),
                        "daily": self.run.get("daily", False),
                    }
                    self.screen = VICTORY
                else:
                    self._open_relic_reward("boss_advance")
            elif node_type == "elite":
                import random
                from potions import POTION_DEFS, add_potion, discover_potion, roll_elite_potion

                self.last_potion_gain = None
                if random.random() < 0.42:
                    pid = roll_elite_potion()
                    if add_potion(self.run, pid):
                        discover_potion(self.meta, pid)
                        self.last_potion_gain = POTION_DEFS[pid]["name"]
                self._open_relic_reward("card_reward")
            else:
                self.reward_cards = roll_card_rewards(3, self.run["act"], deck_card_ids(self.run["deck"]))
                self.screen = REWARD
        else:
            self._record_run_stats(False)
            clear_run_save(self.meta)
            self.screen = DEFEAT
        self.combat = None
        self._persist()

    def _open_relic_reward(self, action):
        boss = action == "boss_advance"
        self.relic_choices = roll_relic_rewards(3, set(self.run.get("relics", [])), boss=boss)
        self.post_relic_action = action
        if self.relic_choices:
            self.screen = RELIC_REWARD
        else:
            self._resolve_post_relic()

    def _resolve_post_relic(self):
        action = self.post_relic_action
        self.relic_choices = []
        self.post_relic_action = None
        if action == "card_reward":
            self.reward_cards = roll_card_rewards(3, self.run["act"], deck_card_ids(self.run["deck"]))
            self.screen = REWARD
        elif action == "boss_advance":
            self.run["act"] += 1
            heal = max(8, int(self.run["max_hp"] * 0.15))
            self.run["hp"] = min(self.run["max_hp"], self.run["hp"] + heal)
            self.run["map"] = generate_map(self.run["act"])
            layout_map(self.run["map"])
            self.screen = ACT_TRANSITION
        else:
            self.screen = MAP
        self._persist()

    def pick_reward(self, index):
        if index >= 0 and index < len(self.reward_cards):
            card = self.reward_cards[index]
            if can_add_card_to_deck(self.run["deck"], card["id"]):
                self.run["deck"].append(card)
                sync_discovered_cards(self.meta, [card])
        self.tutorial.advance("pick_or_skip")
        self.last_gold_gain = 0
        self.screen = MAP
        self._persist()

    def rest_heal(self):
        d = get_difficulty()
        heal = max(d["rest_heal"], int(self.run["max_hp"] * d["rest_heal_pct"]))
        self.run["hp"] = min(self.run["max_hp"], self.run["hp"] + heal)
        self.screen = MAP
        self.tutorial.advance("rest_choice")
        self._persist()

    def rest_brew(self):
        from potions import add_potion, can_add_potion, discover_potion, roll_rest_potion
        if not can_add_potion(self.run) or self.run["hp"] <= 12:
            return
        self.run["hp"] -= 12
        pid = roll_rest_potion()
        add_potion(self.run, pid)
        discover_potion(self.meta, pid)
        self.screen = MAP
        self.tutorial.advance("rest_choice")
        self._persist()

    def rest_upgrade(self):
        choices = unique_upgradable_cards(self.run["deck"])
        if not choices:
            self.screen = MAP
            self._persist()
            return
        self.upgrade_choices = choices
        self.screen = REST_UPGRADE
        self.tutorial.advance("rest_choice")

    def continue_act(self):
        self.screen = MAP
        self._persist()

    def rest_remove(self):
        choices = removable_cards(self.run["deck"])
        if not choices:
            return
        self.remove_choices = choices
        self.after_remove_screen = MAP
        self.remove_cost = 0
        self.screen = REST_REMOVE
        self.tutorial.advance("rest_choice")

    def shop_remove(self):
        if self.run.get("shop_removal_used"):
            return
        price = shop_removal_price()
        if self.run["gold"] < price:
            return
        choices = removable_cards(self.run["deck"])
        if not choices:
            return
        self.remove_choices = choices
        self.after_remove_screen = SHOP
        self.remove_cost = price
        self.screen = REST_REMOVE

    def select_rest_remove(self, index):
        if 0 <= index < len(self.remove_choices):
            self.pending_remove_index = index

    def confirm_rest_remove(self):
        if self.pending_remove_index is not None:
            self.pick_rest_remove(self.pending_remove_index)
            self.pending_remove_index = None

    def cancel_rest_remove(self):
        self.pending_remove_index = None
        self.screen = self.after_remove_screen

    def pick_rest_remove(self, index):
        if 0 <= index < len(self.remove_choices):
            if self.remove_cost > 0 and self.run["gold"] < self.remove_cost:
                return
            uid = self.remove_choices[index]["uid"]
            self.run["deck"] = [c for c in self.run["deck"] if c["uid"] != uid]
            if self.remove_cost > 0:
                self.run["gold"] -= self.remove_cost
                self.run["shop_removal_used"] = True
                on_shop_remove(self.meta)
        self.remove_choices = []
        self.pending_remove_index = None
        self.remove_cost = 0
        self.screen = self.after_remove_screen
        self._persist()

    def pick_rest_upgrade(self, index):
        if 0 <= index < len(self.upgrade_choices):
            upgrade_card(self.upgrade_choices[index])
            on_rest_upgrade(self.meta)
        self.upgrade_choices = []
        self.screen = MAP
        self._persist()

    def pick_relic(self, index):
        if 0 <= index < len(self.relic_choices):
            rid = self.relic_choices[index]
            add_relic(self.run, rid)
            discover_relic(self.meta, rid)
            if rid in {"crown_shard", "abyss_heart", "storm_ring", "void_crown"}:
                on_boss_relic(self.meta)
        self._resolve_post_relic()
        self.tutorial.advance("pick_relic")
        self._persist()

    def shop_heal(self):
        from difficulty import shop_price
        if self.run.get("shop_heal_used"):
            return
        price = shop_price(55)
        heal = max(10, int(self.run["max_hp"] * 0.22))
        if self.run["gold"] < price or self.run["hp"] >= self.run["max_hp"]:
            return
        self.run["gold"] -= price
        self.run["hp"] = min(self.run["max_hp"], self.run["hp"] + heal)
        self.run["shop_heal_used"] = True
        self.screen = MAP
        self._persist()

    def buy_shop_item(self, index):
        if index < 0 or index >= len(self.shop_items):
            return
        item = self.shop_items[index]
        if self.run["gold"] < item["price"]:
            return
        if item.get("type") == "potion":
            from potions import add_potion, can_add_potion, discover_potion
            if not can_add_potion(self.run):
                return
        self.run["gold"] -= item["price"]
        if item.get("type") == "relic":
            rid = item["relic_id"]
            add_relic(self.run, rid)
            discover_relic(self.meta, rid)
        elif item.get("type") == "potion":
            from potions import add_potion, discover_potion
            add_potion(self.run, item["potion_id"])
            discover_potion(self.meta, item["potion_id"])
        else:
            card = item["card"]
            if can_add_card_to_deck(self.run["deck"], card["id"]):
                self.run["deck"].append(card)
                sync_discovered_cards(self.meta, [card])
        self.shop_items.pop(index)
        self.tutorial.advance("shop_action")
        self._persist()

    def buy_card(self, index):
        self.buy_shop_item(index)

    def pick_event(self, index):
        if self.current_event and 0 <= index < len(self.current_event["choices"]):
            before_hp = self.run["hp"]
            before_gold = self.run["gold"]
            before_relics = set(self.run.get("relics", []))
            before_energy = self.run.get("bonus_energy", 0)
            before_potions = len(self.run.get("potions", []))
            choice = self.current_event["choices"][index]
            choice[1](self.run)
            sync_discovered_relics(self.meta, self.run.get("relics", []))
            sync_discovered_cards(self.meta, self.run.get("deck", []))
            parts = []
            hp_delta = self.run["hp"] - before_hp
            if hp_delta:
                parts.append(f"{hp_delta:+d} HP")
            gold_delta = self.run["gold"] - before_gold
            if gold_delta:
                parts.append(f"{gold_delta:+d} золота")
            for rid in self.run.get("relics", []):
                if rid not in before_relics:
                    from relics import RELIC_DEFS
                    parts.append(f"Реликвия: {RELIC_DEFS.get(rid, {}).get('name', rid)}")
            energy_delta = self.run.get("bonus_energy", 0) - before_energy
            if energy_delta:
                parts.append(f"{energy_delta:+d} энергия в боях")
            if len(self.run.get("potions", [])) > before_potions:
                parts.append("Зелье получено")
            self.event_result = " · ".join(parts) if parts else None
        if self.run.get("pending_ambush"):
            self.run["pending_ambush"] = False
            self.screen = COMBAT
            self.start_combat(ambush=True)
            self._persist()
            return
        if self.run.get("pending_event_reward") == "rare":
            from cards import roll_rare_card_reward
            self.reward_cards = roll_rare_card_reward(deck_card_ids(self.run.get("deck", [])))
            self.run["pending_event_reward"] = None
            self.screen = REWARD
        else:
            self.screen = MAP
        self._persist()

    def on_play_card(self):
        self.tutorial.advance("play_card")

    def on_end_turn(self):
        self.tutorial.advance("end_turn")

    def use_potion(self, index):
        if not self.combat or not self.combat.is_player_turn:
            return False
        from potions import use_potion_in_combat
        if not use_potion_in_combat(self.combat, index):
            return False
        self.run["potions"] = list(self.combat.potions)
        self.run["potions_used"] = self.run.get("potions_used", 0) + 1
        on_potion_used(self.meta, self.run)
        return True

    def update(self):
        if self.combat_end_pending:
            self.combat_end_timer -= 1
            if self.combat_end_timer <= 0:
                self.finish_combat()
                self.combat_end_pending = None
            return
        if self.combat:
            self.combat.update()
            if self.combat.won or self.combat.lost:
                self.combat_end_pending = "won" if self.combat.won else "lost"
                self.combat_end_timer = 75

    def to_menu(self):
        self.screen = MENU
        self.run = None
        self.combat = None

    def cycle_difficulty(self):
        from difficulty import cycle_difficulty

        cycle_difficulty(self.meta)
        save_meta(self.meta)

    def cycle_oath(self):
        from mutators import cycle_oath
        cycle_oath(self.meta)
        save_meta(self.meta)

    def replay_tutorial(self):
        self.tutorial.active = True
        self.tutorial.step_index = 0
        self.meta["tutorial_done"] = False
        save_meta(self.meta)
        self.screen = MENU

    def save(self):
        self._persist()
        save_meta(self.meta)
