"""Процедурные звуковые эффекты — без внешних файлов."""

import array
import math

import pygame


def _make_tone(frequency, duration_ms, volume=0.22, sample_rate=22050, fade_ms=8):
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    fade_in = max(1, int(sample_rate * fade_ms / 1000))
    fade_out = max(1, int(sample_rate * (fade_ms + 12) / 1000))
    buf = array.array("h", [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0
        if i < fade_in:
            env = i / fade_in
        elif i > n_samples - fade_out:
            env = max(0.0, (n_samples - i) / fade_out)
        sample = int(volume * 32767 * env * math.sin(2 * math.pi * frequency * t))
        buf[i] = sample
    return pygame.mixer.Sound(buffer=buf)


def _make_chord(freqs, duration_ms, volume=0.16):
    sample_rate = 22050
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    buf = array.array("h", [0] * n_samples)
    fade_out = max(1, int(sample_rate * 0.08))
    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0 if i < n_samples - fade_out else max(0.0, (n_samples - i) / fade_out)
        wave = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        buf[i] = int(volume * 32767 * env * wave)
    return pygame.mixer.Sound(buffer=buf)


def _make_ambient_loop(base_freq, harmonics, duration_sec=14, volume=0.07, arp=None, sample_rate=22050):
    n_samples = max(1, int(sample_rate * duration_sec))
    buf = array.array("h", [0] * n_samples)
    arp = arp or []
    for i in range(n_samples):
        t = i / sample_rate
        wave = 0.0
        for idx, (mult, amp) in enumerate(harmonics):
            wave += amp * math.sin(2 * math.pi * base_freq * mult * t + idx * 0.65)
        wave /= max(1, len(harmonics))
        lfo = 0.72 + 0.28 * math.sin(2 * math.pi * 0.06 * t)
        if arp:
            step = int(t * 1.6) % len(arp)
            wave += 0.22 * math.sin(2 * math.pi * arp[step] * t)
        sample = int(volume * 32767 * lfo * wave)
        buf[i] = max(-32767, min(32767, sample))
    return pygame.mixer.Sound(buffer=buf)


class Audio:
    def __init__(self, music_volume=0.7, sfx_volume=0.85):
        self.enabled = True
        self._sounds = {}
        self._ambient = {}
        self._music_sound = None
        self._current_track = None
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._build()
        except pygame.error:
            self.enabled = False

    def _build(self):
        self._sounds = {
            "ui": _make_tone(520, 55, 0.14),
            "card": _make_tone(660, 70, 0.16),
            "attack": _make_tone(180, 95, 0.2),
            "block": _make_tone(320, 85, 0.17),
            "power": _make_chord([440, 554, 659], 140, 0.14),
            "hit": _make_tone(240, 60, 0.18),
            "hurt": _make_tone(120, 130, 0.22),
            "draw": _make_tone(780, 50, 0.12),
            "turn": _make_tone(420, 90, 0.13),
            "win": _make_chord([523, 659, 784], 320, 0.18),
            "lose": _make_chord([220, 196, 165], 360, 0.16),
            "map": _make_tone(880, 45, 0.1),
            "achievement": _make_chord([523, 659, 784, 988], 220, 0.2),
            "buzz": _make_tone(180, 40, 0.1),
        }
        self._ambient = {
            "menu": _make_ambient_loop(110, [(1, 1.0), (1.5, 0.35), (2.0, 0.18)], 16, 0.055, [220, 262, 330]),
            "forest": _make_ambient_loop(98, [(1, 1.0), (1.33, 0.45), (1.66, 0.28)], 18, 0.065, [196, 247, 294]),
            "desert": _make_ambient_loop(82, [(1, 1.0), (1.25, 0.42), (1.5, 0.22)], 14, 0.06, [165, 196, 220]),
            "snow": _make_ambient_loop(130, [(1, 1.0), (1.2, 0.38), (1.8, 0.2)], 20, 0.052, [262, 330, 392]),
            "ruins": _make_ambient_loop(92, [(1, 1.0), (1.35, 0.42), (1.7, 0.28), (2.05, 0.14)], 17, 0.056, [147, 185, 220]),
            "combat": _make_ambient_loop(72, [(1, 1.0), (1.5, 0.5), (2.0, 0.32)], 11, 0.072, [98, 123, 147]),
            "shop": _make_ambient_loop(88, [(1, 1.0), (1.4, 0.4), (1.75, 0.25)], 13, 0.048, [175, 220, 262]),
        }

    def play(self, name):
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.set_volume(self.sfx_volume)
            sound.play()

    def set_volumes(self, music_volume, sfx_volume):
        from config import clamp

        self.music_volume = clamp(music_volume, 0.0, 1.0)
        self.sfx_volume = clamp(sfx_volume, 0.0, 1.0)
        if self._current_track:
            ambient = self._ambient.get(self._current_track)
            if ambient:
                ambient.set_volume(self.music_volume)

    def set_music(self, track):
        if not self.enabled:
            return
        if track == self._current_track:
            return
        if self._music_sound:
            self._music_sound.stop()
            self._music_sound = None
        self._current_track = track
        if not track:
            return
        ambient = self._ambient.get(track)
        if ambient:
            ambient.set_volume(self.music_volume)
            self._music_sound = ambient.play(-1)

    def stop_music(self):
        self.set_music(None)

    def play_card(self, card_type):
        self.play("card")
        if card_type == "attack":
            self.play("attack")
        elif card_type == "skill":
            self.play("block")
        elif card_type == "power":
            self.play("power")

    def combat_sfx(self, kind, target_key):
        if kind == "damage" and target_key == "player":
            self.play("hurt")
        elif kind == "block" and target_key == "player":
            self.play("block")
        elif kind in ("damage", "blocked", "poison") and target_key.startswith("e"):
            self.play("hit")
        elif kind == "draw":
            self.play("draw")
