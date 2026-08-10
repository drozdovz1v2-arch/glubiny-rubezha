"""Интерактивное обучение для новых игроков."""

from config import save_meta

TUTORIAL_STEPS = [
    {
        "screen": "menu",
        "title": "Добро пожаловать, Страж!",
        "text": "Ты на Рубеже — опасной границе четырёх миров. Собери колоду, побеждай врагов и дойди до Владыки Пустоты. Нажми «Новый Забег».",
        "highlight": None,
        "advance": "click_new_run",
    },
    {
        "screen": "map",
        "title": "Карта пути",
        "text": "Светящиеся узлы — твой маршрут. Каждый шаг необратим. Планируй путь: привалы лечат, но их мало.",
        "highlight": "map_nodes",
        "advance": "click_node",
    },
    {
        "screen": "map",
        "title": "Типы узлов",
        "text": "Наведи курсор на узел — увидишь тип и угрозу. Меч — бой, череп — элита, огонь — привал, сумка — лавка, ? — событие, глаз — босс.",
        "highlight": "map_panel",
        "advance": "click_node",
    },
    {
        "screen": "combat",
        "title": "Бой: карты",
        "text": "Кликни по карте, чтобы сыграть. Число в углу — стоимость в энергии. Красные бьют, синие защищают, фиолетовые — силы на весь бой.",
        "highlight": "hand",
        "advance": "play_card",
    },
    {
        "screen": "combat",
        "title": "Намерения врага",
        "text": "Враг показывает, что сделает в свой ход. Видишь атаку — играй синие карты для блока. Блок сгорает каждый ход!",
        "highlight": "enemy_intent",
        "advance": "any",
    },
    {
        "screen": "combat",
        "title": "Энергия и цель",
        "text": "У тебя 3 энергии за ход — трать с умом. Tab переключает цель. Когда энергия закончится или не останется доступных карт, ход передаётся врагам автоматически.",
        "highlight": "energy",
        "advance": "end_turn",
    },
    {
        "screen": "combat",
        "title": "Зелья и давление",
        "text": "Z/X/C — зелья с пояса (до 3, одно за ход). С 5-го хода враги получают +1 силы — «давление Рубежа». Готовь защиту заранее.",
        "highlight": "potions",
        "advance": "any",
    },
    {
        "screen": "reward",
        "title": "Награда",
        "text": "После боя выбери одну карту или пропусти. Колода растёт — но слабые карты тоже попадают в руку. Строй синергии!",
        "highlight": "reward_cards",
        "advance": "pick_or_skip",
    },
    {
        "screen": "relic_reward",
        "title": "Реликвии",
        "text": "Элиты и боссы дают артефакты — пассивные бонусы на весь забег. Выбери один или откажись.",
        "highlight": "relic_choices",
        "advance": "pick_relic",
    },
    {
        "screen": "rest",
        "title": "Привал",
        "text": "Один выбор за визит: 1 — лечение, 2 — улучшение, 3 — удаление, 4 — сварить зелье (−60 зол.). Карту можно усилить снова на следующем привале.",
        "highlight": "rest_options",
        "advance": "rest_choice",
    },
    {
        "screen": "shop",
        "title": "Лавка Странника",
        "text": "Покупай карты, зелья и артефакты. H — лечение за золото, R — удаление карты. Нажми «Уйти», когда закончишь.",
        "highlight": "shop_cards",
        "advance": "shop_action",
    },
    {
        "screen": "map",
        "title": "Готов к испытанию",
        "text": "Четыре акта: лес, пустыня, лёд, руины. Клятва в меню усложняет обычный забег. Удачи, Страж!",
        "highlight": None,
        "advance": "click",
    },
]


class Tutorial:
    def __init__(self, meta):
        self.meta = meta
        self.active = not meta.get("tutorial_done", False)
        self.step_index = 0

    @property
    def step(self):
        if not self.active or self.step_index >= len(TUTORIAL_STEPS):
            return None
        return TUTORIAL_STEPS[self.step_index]

    def should_show(self, screen_name):
        if not self.active:
            return False
        step = self.step
        return step and step["screen"] == screen_name

    def advance(self, reason="click"):
        if not self.active:
            return
        step = self.step
        if not step:
            return
        needed = step["advance"]
        if needed in ("any", "click") or needed == reason:
            self.step_index += 1
            if self.step_index >= len(TUTORIAL_STEPS):
                self.complete()

    def complete(self):
        self.active = False
        self.meta["tutorial_done"] = True
        save_meta(self.meta)

    def skip(self):
        self.complete()
        save_meta(self.meta)
