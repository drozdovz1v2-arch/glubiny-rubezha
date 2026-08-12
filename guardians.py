"""Архетипы Стража — разные стартовые колоды и эксклюзивные карты."""

GUARDIAN_DEFS = {
    "steel": {
        "id": "steel",
        "name": "Стальной Страж",
        "desc": "Классика Рубежа: удары, блок и выносливость. +2 блока от навыков защиты.",
        "color": (72, 210, 200),
        "starter": ["strike", "strike", "strike", "strike", "defend", "defend", "defend", "defend", "defend", "fortify"],
        "exclusive": ["aegis_strike", "bulwark", "shield_bash", "hold_the_line"],
        "relic_start": None,
    },
    "shadow": {
        "id": "shadow",
        "name": "Теневой Страж",
        "desc": "Яд, быстрые удары и риск. Карты с ядом накладывают +1 яда.",
        "color": (160, 120, 220),
        "starter": ["strike", "strike", "strike", "defend", "defend", "defend", "plague_knife", "plague_knife", "venom_dagger", "quick_slash"],
        "exclusive": ["shadow_stab", "toxin_wave", "night_veil", "assassin_mark"],
        "relic_start": None,
    },
    "flame": {
        "id": "flame",
        "name": "Пламенный Страж",
        "desc": "Ожог и взрывной урон. Карты с ожогом накладывают +1 ожога.",
        "color": (255, 120, 50),
        "starter": ["strike", "strike", "strike", "defend", "defend", "cinder_strike", "cinder_strike", "ember_strike", "ember_strike", "quick_slash"],
        "exclusive": ["ember_strike", "flame_wave", "inferno_core", "scorch_mark"],
        "relic_start": None,
    },
}


def guardian_def(guardian_id):
    return GUARDIAN_DEFS.get(guardian_id, GUARDIAN_DEFS["steel"])


def guardian_label(guardian_id):
    return guardian_def(guardian_id)["name"]


def guardian_desc(guardian_id):
    return guardian_def(guardian_id)["desc"]


def cycle_guardian(meta):
    ids = list(GUARDIAN_DEFS.keys())
    cur = meta.get("guardian", "steel")
    nxt = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else ids[0]
    meta["guardian"] = nxt
    return nxt


def card_guardian(card_id):
    for gid, info in GUARDIAN_DEFS.items():
        if card_id in info.get("exclusive", []):
            return gid
    return None


def guardian_card_pool(guardian_id):
    info = guardian_def(guardian_id)
    return set(info.get("exclusive", []))
