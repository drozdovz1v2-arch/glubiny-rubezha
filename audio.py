"""Процедурные звуковые эффекты — без внешних файлов."""

import array
import math

import pygame

_SAMPLE_RATE = 22050

# Пентатоника — мягкие интервалы без диссонанса.
_PENTATONIC_MAJOR = (1.0, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2.0, 9 / 4, 5 / 2)
_PENTATONIC_MINOR = (1.0, 6 / 5, 4 / 3, 3 / 2, 9 / 5, 2.0, 12 / 5, 3.0)


def _make_tone(frequency, duration_ms, volume=0.22, sample_rate=_SAMPLE_RATE, fade_ms=8):
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
    sample_rate = _SAMPLE_RATE
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    buf = array.array("h", [0] * n_samples)
    fade_out = max(1, int(sample_rate * 0.08))
    for i in range(n_samples):
        t = i / sample_rate
        env = 1.0 if i < n_samples - fade_out else max(0.0, (n_samples - i) / fade_out)
        wave = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        buf[i] = int(volume * 32767 * env * wave)
    return pygame.mixer.Sound(buffer=buf)


def _scale_from_root(root_hz, ratios, indices):
    return [root_hz * ratios[i % len(ratios)] for i in indices]


def _soft_clip(value, drive=1.05):
    return math.tanh(value * drive)


def _make_ambient_music(
    root_hz,
    scale_ratios,
    melody_pattern,
    duration_sec=22,
    volume=0.042,
    bpm=46,
    pad_partials=None,
    sample_rate=_SAMPLE_RATE,
):
    """Тёплый ambient-пад с медленной мелодией в пентатонике."""
    pad_partials = pad_partials or (
        (1.0, 0.0, 0.46),
        (1.004, 0.4, 0.32),
        (1.5, 0.15, 0.24),
        (2.0, 0.2, 0.14),
        (2.5, 0.55, 0.08),
    )
    melody = _scale_from_root(root_hz * 2, scale_ratios, melody_pattern)
    n_samples = max(1, int(sample_rate * duration_sec))
    buf = array.array("h", [0] * n_samples)
    fade_samples = int(sample_rate * 1.8)
    beat_len = 60.0 / bpm

    for i in range(n_samples):
        t = i / sample_rate
        pad = 0.0
        for mult, phase, amp in pad_partials:
            freq = root_hz * mult * (1.0 + 0.0025 * math.sin(2 * math.pi * 0.07 * t + phase))
            pad += amp * math.sin(2 * math.pi * freq * t + phase)

        step = int(t / beat_len) % len(melody)
        local = (t % beat_len) / beat_len
        note_env = 0.35 + 0.65 * (0.5 - 0.5 * math.cos(2 * math.pi * local))
        next_step = (step + 1) % len(melody)
        blend = local * local * (3 - 2 * local)
        mel_freq = melody[step] * (1 - blend) + melody[next_step] * blend
        melody_wave = 0.22 * note_env * math.sin(2 * math.pi * mel_freq * t)

        breath = 0.76 + 0.24 * math.sin(2 * math.pi * 0.035 * t)
        shimmer = 1.0 + 0.06 * math.sin(2 * math.pi * 0.19 * t + 0.8)
        wave = _soft_clip((pad / 1.35 + melody_wave) * breath * shimmer)

        env = 1.0
        if i < fade_samples:
            env = i / fade_samples
        elif i > n_samples - fade_samples:
            env = max(0.0, (n_samples - i) / fade_samples)

        sample = int(volume * 32767 * env * wave)
        buf[i] = max(-32767, min(32767, sample))
    return pygame.mixer.Sound(buffer=buf)


def _make_ambient_loop(base_freq, harmonics, duration_sec=14, volume=0.07, arp=None, sample_rate=_SAMPLE_RATE):
    """Сохранено для совместимости — делегирует в новый генератор."""
    pattern = tuple(range(len(arp or (0, 2, 4, 2))))
    ratios = _PENTATONIC_MINOR if base_freq < 120 else _PENTATONIC_MAJOR
    return _make_ambient_music(base_freq, ratios, pattern, duration_sec, volume * 0.65, bpm=44)


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
            "menu": _make_ambient_music(
                130.81, _PENTATONIC_MAJOR, (0, 2, 4, 3, 2, 1, 3, 4),
                duration_sec=24, volume=0.040, bpm=42,
            ),
            "forest": _make_ambient_music(
                98.0, _PENTATONIC_MINOR, (0, 1, 3, 2, 4, 3, 1, 0),
                duration_sec=26, volume=0.044, bpm=44,
            ),
            "desert": _make_ambient_music(
                87.31, _PENTATONIC_MINOR, (0, 2, 1, 3, 2, 4, 2, 1),
                duration_sec=22, volume=0.041, bpm=48,
            ),
            "snow": _make_ambient_music(
                146.83, _PENTATONIC_MAJOR, (0, 2, 4, 5, 4, 2, 3, 1),
                duration_sec=28, volume=0.038, bpm=40,
                pad_partials=((1.0, 0.0, 0.42), (1.003, 0.5, 0.30), (1.5, 0.2, 0.22), (2.0, 0.35, 0.12)),
            ),
            "ruins": _make_ambient_music(
                92.5, _PENTATONIC_MINOR, (0, 1, 2, 4, 3, 2, 1, 3),
                duration_sec=24, volume=0.042, bpm=43,
            ),
            "combat": _make_ambient_music(
                103.83, _PENTATONIC_MINOR, (0, 1, 0, 2, 1, 3, 2, 1),
                duration_sec=18, volume=0.048, bpm=54,
                pad_partials=((1.0, 0.0, 0.50), (1.006, 0.25, 0.34), (1.5, 0.1, 0.26), (2.0, 0.45, 0.16)),
            ),
            "shop": _make_ambient_music(
                116.54, _PENTATONIC_MAJOR, (0, 2, 3, 2, 4, 3, 1, 2),
                duration_sec=20, volume=0.039, bpm=50,
            ),
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
