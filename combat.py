from cards import play_card_effect
from config import COLORS, rand_int, shuffle
from difficulty import get_difficulty
from mutators import pressure_turn, run_modifiers
from relics import apply_combat_start, apply_enemy_thorns, check_iron_heart, check_wraith_cloak, relic_bonus_block, relic_bonus_damage, relic_bonus_poison, relic_on_attack_hit, relic_on_block_stolen, relic_on_curse_played
from enemies import (
    add_status,
    advance_pattern,
    apply_block_damage,
    check_boss_enrage,
    decay_statuses,
    get_intent,
    scaled_damage,
    tick_statuses,
)

ENEMY_ACTION_DELAY = 55
ENEMY_WINDUP_DELAY = 28


class CombatContext:
    def __init__(self, combat):
        self.combat = combat

    def deal_damage(self, amount, pierce=False):
        enemy = self.combat.target_enemy()
        if not enemy:
            return
        dmg = scaled_damage(amount, self.combat.player, enemy)
        dmg = relic_bonus_damage(self.combat.relics, self.combat.current_card, dmg, self.combat)
        before_hp = enemy["hp"]
        before_block = enemy.get("block", 0)
        hp_lost = apply_block_damage(enemy, dmg, pierce)
        block_used = before_block - enemy.get("block", 0)
        if hp_lost > 0:
            self.combat.spawn_fx("damage", hp_lost, enemy)
            self.combat.log(f"{hp_lost} урона -> {enemy['name']}")
            check_boss_enrage(self.combat, enemy)
            card = self.combat.current_card
            if card and card.get("type") == "attack":
                relic_on_attack_hit(self.combat.relics, self.combat, enemy)
        elif block_used > 0:
            self.combat.spawn_fx("blocked", block_used, enemy)
            self.combat.log(f"Заблокировано {block_used} -> {enemy['name']}")
        else:
            self.combat.log(f"0 урона -> {enemy['name']}")
        self.combat.pulse(enemy)

    def gain_block(self, amount):
        amount = relic_bonus_block(self.combat.relics, self.combat.current_card, amount, self.combat)
        self.combat.player["block"] += amount
        self.combat.spawn_fx("block", amount, "player")

    def draw_cards(self, n):
        self.combat.draw_cards(n)
        if n > 0:
            self.combat.spawn_fx("draw", n, "player")

    def discard_random(self, n):
        for _ in range(n):
            if not self.combat.hand:
                break
            idx = rand_int(0, len(self.combat.hand) - 1)
            self.combat.discard.append(self.combat.hand.pop(idx))

    def apply_status(self, key, amount):
        enemy = self.combat.target_enemy()
        if enemy:
            if key == "poison":
                amount = relic_bonus_poison(self.combat.relics, amount)
            add_status(enemy, key, amount)

    def enemy_has_status(self, key):
        enemy = self.combat.target_enemy()
        return bool(enemy and enemy.get("statuses", {}).get(key, 0) > 0)

    def enemy_has_any_status(self):
        enemy = self.combat.target_enemy()
        return bool(enemy and any(v > 0 for v in enemy.get("statuses", {}).values()))

    def heal(self, amount):
        before = self.combat.player["hp"]
        self.combat.player["hp"] = min(self.combat.player["max_hp"], self.combat.player["hp"] + amount)
        gained = self.combat.player["hp"] - before
        if gained > 0:
            self.combat.spawn_fx("heal", gained, "player")

    def gain_power(self, key, amount):
        self.combat.player.setdefault("powers", {})[key] = self.combat.player["powers"].get(key, 0) + amount

    def self_damage(self, amount):
        before_hp = self.combat.player["hp"]
        apply_block_damage(self.combat.player, amount)
        hp_lost = before_hp - self.combat.player["hp"]
        if hp_lost > 0:
            self.combat.spawn_fx("self", hp_lost, "player")
            self.combat.shake = max(self.combat.shake, min(10, 4 + hp_lost // 4))
            check_iron_heart(self.combat, hp_lost)
            check_wraith_cloak(self.combat, hp_lost)

    def enemy_hp_percent(self):
        enemy = self.combat.target_enemy()
        return enemy["hp"] / enemy["max_hp"] if enemy else 1.0

    def player_hp_percent(self):
        p = self.combat.player
        return p["hp"] / max(1, p["max_hp"])

    def player_block(self):
        return self.combat.player.get("block", 0)

    def deal_shatter_guard(self, base, bonus):
        enemy = self.combat.target_enemy()
        extra = bonus if enemy and enemy.get("block", 0) > 0 else 0
        if extra and enemy:
            enemy["block"] = 0
        self.deal_damage(base + extra)


class CombatState:
    def __init__(self, run, enemies):
        self.player = {
            "hp": run["hp"],
            "max_hp": run["max_hp"],
            "block": 0,
            "energy": get_difficulty()["base_energy"],
            "max_energy": get_difficulty()["base_energy"] + run.get("bonus_energy", 0),
            "gold": run["gold"],
            "statuses": {},
            "powers": {},
        }
        self.enemies = []
        for e in enemies:
            copy = dict(e)
            copy["statuses"] = dict(e.get("statuses", {}))
            copy["powers"] = dict(e.get("powers", {}))
            copy["intent"] = get_intent(copy)
            self.enemies.append(copy)
        self.deck = shuffle(list(run["deck"]))
        self.hand = []
        self.discard = []
        self.turn = 1
        self.phase = "player"
        self.enemy_subphase = None
        self.enemy_queue = []
        self.enemy_queue_idx = 0
        self.active_enemy_idx = None
        self.step_timer = 0
        self.action_banner = ""
        self.target_index = 0
        self.log_lines = []
        self.fx = []
        self.shake = 0
        self.pulse_key = None
        self.pulse_timer = 0
        self.card_anim = None
        self.sfx_callback = None
        self.relics = list(run.get("relics", []))
        self.potions = list(run.get("potions", []))
        self.run_mutators = run_modifiers(run)
        self.run_act = run.get("act", 0)
        self.potion_used_this_turn = False
        self.current_card = None
        self.ember_used_this_turn = False
        self.storm_used_this_turn = False
        self.bark_used_this_turn = False
        self.mark_used_this_turn = False
        self.iron_heart_used = False
        self.wraith_cloak_used = False
        self.runic_flask_used = False
        self.won = False
        self.lost = False
        self.finished = False

    @property
    def is_player_turn(self):
        return self.phase == "player" and not self.won and not self.lost

    def start_turn(self):
        self.player["block"] = 0
        self.player["energy"] = self.player["max_energy"]
        for e in self.enemies:
            e["block"] = 0
        if self.player.get("powers", {}).get("strength"):
            self.player["statuses"]["strength"] = self.player["powers"]["strength"]
        elif "strength" in self.player.get("statuses", {}):
            self.player["statuses"].pop("strength", None)
        if self.player.get("powers", {}).get("metallicize"):
            bonus = self.player["powers"]["metallicize"]
            self.player["block"] += bonus
            self.spawn_fx("block", bonus, "player")
        pact = self.player.get("powers", {}).get("blood_pact", 0)
        if pact > 0:
            hp_before = self.player["hp"]
            apply_block_damage(self.player, 2)
            check_iron_heart(self, max(0, hp_before - self.player["hp"]))
            check_wraith_cloak(self, max(0, hp_before - self.player["hp"]))
            add_status(self.player, "strength", pact)
            self.log(f"Кровавый Пакт: −2 HP, +{pact} силы")
        self.draw_cards(get_difficulty()["cards_per_turn"])
        for e in self.enemies:
            if e["hp"] > 0:
                e["intent"] = get_intent(e)
        self.phase = "player"
        self.enemy_subphase = None
        self.active_enemy_idx = None
        self.action_banner = ""
        self.log("— Твой ход —")
        self.ember_used_this_turn = False
        self.storm_used_this_turn = False
        self.bark_used_this_turn = False
        self.mark_used_this_turn = False
        self.potion_used_this_turn = False
        if self.turn >= pressure_turn(self.run_mutators, get_difficulty().get("pressure_turn", 5), self.run_act):
            living = self.living_enemies()
            if living:
                for e in living:
                    add_status(e, "strength", 1)
                self.log(f"⚠ Рубеж давит — враги +1 силы (ход {self.turn})")
                self.action_banner = "Рубеж давит!"
        if self.turn == 1:
            apply_combat_start(self)

    def draw_cards(self, n):
        for _ in range(n):
            if not self.deck and self.discard:
                self.deck = shuffle(self.discard)
                self.discard = []
            if not self.deck:
                break
            self.hand.append(self.deck.pop())

    def living_enemies(self):
        return [e for e in self.enemies if e["hp"] > 0]

    def target_enemy(self):
        living = self.living_enemies()
        if not living:
            return None
        return living[self.target_index % len(living)]

    def can_play(self, card):
        if card.get("unplayable") or card.get("type") == "curse" and card.get("cost", 0) < 0:
            return False
        return self.is_player_turn and card["cost"] <= self.player["energy"]

    def has_playable_card(self):
        return any(self.can_play(card) for card in self.hand)

    def should_auto_end_turn(self):
        if not self.is_player_turn or self.won or self.lost or self.card_anim:
            return False
        if self.player["energy"] <= 0:
            return True
        return not self.has_playable_card()

    def try_auto_end_turn(self):
        if not self.should_auto_end_turn():
            return False
        self.end_turn()
        return True

    def play_card(self, index, from_pos=None, card_size=None):
        if index < 0 or index >= len(self.hand):
            return False
        card = self.hand[index]
        if not self.can_play(card):
            return False
        self.player["energy"] -= card["cost"]
        self.hand.pop(index)
        self.discard.append(card)
        self.current_card = card
        play_card_effect(card["effect"], CombatContext(self))
        if card.get("type") == "curse":
            relic_on_curse_played(self.relics, self)
        self.current_card = None
        target = self.target_enemy() if card["type"] == "attack" else "player"
        if target:
            self.pulse(target)
        anim_target = self._target_key(target or "player")
        self.card_anim = {
            "card": card,
            "from": from_pos or (640, 520),
            "size": card_size or (128, 132),
            "progress": 0,
            "duration": 22,
            "target": anim_target,
        }
        self.check_end()
        return True

    def _target_key(self, target):
        if target == "player" or target is self.player:
            return "player"
        if isinstance(target, int):
            return f"e{target}"
        try:
            return f"e{self.enemies.index(target)}"
        except ValueError:
            return "player"

    def spawn_fx(self, kind, value, target):
        key = self._target_key(target)
        styles = {
            "damage": (f"-{value}", COLORS["danger"]),
            "self": (f"-{value}", COLORS["danger"]),
            "poison": (f"-{value}", (120, 220, 100)),
            "heal": (f"+{value}", COLORS["success"]),
            "block": (f"+{value}", COLORS["accent"]),
            "blocked": (f"Блок {value}", COLORS["accent"]),
            "draw": (f"+{value}", COLORS["success"]),
        }
        text, color = styles.get(kind, (str(value), COLORS["text"]))
        self.fx.append(
            {
                "text": text,
                "color": color,
                "target": key,
                "life": 52,
                "max_life": 52,
                "y": 0.0,
                "offset_x": rand_int(-10, 10),
            }
        )
        if kind in ("damage", "self") and value >= 6:
            self.shake = max(self.shake, min(12, 4 + value // 3))
        if self.sfx_callback:
            self.sfx_callback(kind, key)

    def pulse(self, target=None):
        target = target or self.target_enemy()
        if target:
            self.pulse_key = self._target_key(target)
            self.pulse_timer = 16

    def tick_fx(self):
        for fx in self.fx:
            fx["life"] -= 1
            fx["y"] += 1.1
        self.fx = [fx for fx in self.fx if fx["life"] > 0]
        if self.card_anim:
            self.card_anim["progress"] += 1
            if self.card_anim["progress"] >= self.card_anim["duration"]:
                self.card_anim = None
        if self.shake > 0:
            self.shake -= 1
        if self.pulse_timer > 0:
            self.pulse_timer -= 1
        elif self.pulse_key:
            self.pulse_key = None

    def end_turn(self):
        if not self.is_player_turn:
            return
        self.discard.extend(self.hand)
        self.hand = []
        self.phase = "enemy_turn"
        self.enemy_subphase = "windup"
        self.enemy_queue = [i for i, e in enumerate(self.enemies) if e["hp"] > 0]
        self.enemy_queue_idx = 0
        self.active_enemy_idx = None
        self.step_timer = ENEMY_WINDUP_DELAY
        self.action_banner = "Ход врагов..."
        decay_statuses(self.player)
        self.log("— Ход врагов —")

    def update(self):
        self.tick_fx()
        if self.phase != "enemy_turn" or self.won or self.lost:
            return
        if self.step_timer > 0:
            self.step_timer -= 1
            return

        if self.enemy_queue_idx >= len(self.enemy_queue):
            self._finish_enemy_round()
            return

        idx = self.enemy_queue[self.enemy_queue_idx]
        enemy = self.enemies[idx]
        if enemy["hp"] <= 0:
            self.enemy_queue_idx += 1
            self.enemy_subphase = "windup"
            self.step_timer = ENEMY_WINDUP_DELAY // 2
            return

        if self.enemy_subphase == "windup":
            self.active_enemy_idx = idx
            self.action_banner = f"Ход: {enemy['name']}"
            self.enemy_subphase = "act"
            self.step_timer = ENEMY_WINDUP_DELAY
            return

        if self.enemy_subphase == "act":
            decay_statuses(enemy)
            poison_dmg = tick_statuses(enemy)
            if poison_dmg:
                self.spawn_fx("poison", poison_dmg, enemy)
                self.log(f"{enemy['name']}: {poison_dmg} урона от яда")
                check_boss_enrage(self, enemy)
            self.execute_intent(enemy, enemy["intent"])
            advance_pattern(enemy)
            if enemy["hp"] > 0:
                enemy["intent"] = get_intent(enemy)
            self.check_end()
            self.enemy_queue_idx += 1
            self.enemy_subphase = "windup"
            self.step_timer = ENEMY_ACTION_DELAY
            if self.won or self.lost:
                self.active_enemy_idx = None
                self.action_banner = ""

    def _finish_enemy_round(self):
        self.active_enemy_idx = None
        self.action_banner = ""
        self.enemy_subphase = None
        self.check_end()
        if not self.won and not self.lost:
            self.turn += 1
            self.start_turn()

    def execute_intent(self, enemy, intent):
        kind = intent.get("intent")
        if kind == "attack":
            dmg = scaled_damage(intent["value"], enemy, self.player)
            hp_lost = apply_block_damage(self.player, dmg)
            if hp_lost > 0:
                self.spawn_fx("damage", hp_lost, "player")
            check_iron_heart(self, hp_lost)
            check_wraith_cloak(self, hp_lost)
            apply_enemy_thorns(self, enemy, hp_lost)
            self.log(f"{enemy['name']} атакует: {hp_lost or 'блок'}")
        elif kind == "multi":
            total = 0
            for _ in range(intent["hits"]):
                total += apply_block_damage(self.player, scaled_damage(intent["value"], enemy, self.player))
            if total > 0:
                self.spawn_fx("damage", total, "player")
            check_iron_heart(self, total)
            check_wraith_cloak(self, total)
            apply_enemy_thorns(self, enemy, total)
            self.log(f"{enemy['name']}: {intent['value']}x{intent['hits']}")
        elif kind == "block":
            enemy["block"] += intent["value"]
            self.spawn_fx("block", intent["value"], enemy)
            self.log(f"{enemy['name']} блок +{intent['value']}")
        elif kind == "buff":
            add_status(enemy, intent.get("status", "strength"), intent["value"])
            self.log(f"{enemy['name']}: +{intent['value']} силы")
        elif kind == "debuff":
            add_status(self.player, intent["status"], intent["value"])
            self.log(f"{enemy['name']}: {intent['status']} {intent['value']}")
        elif kind == "steal_block":
            stolen = self.player["block"]
            self.player["block"] = 0
            enemy["block"] += stolen
            relic_on_block_stolen(self.relics, self, stolen)
            dmg = intent.get("bonus_dmg", 7)
            hp_lost = apply_block_damage(self.player, dmg)
            if hp_lost > 0:
                self.spawn_fx("damage", hp_lost, "player")
            check_iron_heart(self, hp_lost)
            check_wraith_cloak(self, hp_lost)
            self.log(f"{enemy['name']} крадёт блок и бьёт на {hp_lost or dmg}")
        elif kind == "curse":
            from cards import create_card
            cid = intent.get("curse_id", "curse_doubt")
            self.discard.append(create_card(cid))
            self.log(f"⚠ {enemy['name']} вплетает проклятие в колоду!")

    def check_end(self):
        if not self.living_enemies():
            self.won = True
        if self.player["hp"] <= 0:
            self.lost = True

    def log(self, text):
        self.log_lines.insert(0, text)
        if len(self.log_lines) > 50:
            self.log_lines.pop()

    def sync_deck(self):
        return self.deck + self.hand + self.discard

    def is_active_enemy(self, enemy):
        if self.active_enemy_idx is None:
            return False
        return self.enemies[self.active_enemy_idx] is enemy
