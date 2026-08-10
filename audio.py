"""Процедурные звуковые эффекты — без внешних файлов."""

import array
import math

import pygame

_SAMPLE_RATE = 22050

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


def _scale_freq(root_hz, ratios, index):
    return root_hz * ratios[index % len(ratios)]


def _soft_clip(value, drive=0.92):
    return math.tanh(value * drive)


def _loop_crossfade(buf, sample_rate, xfade_sec=5.0):
    xfade = min(len(buf) // 4, int(sample_rate * xfade_sec))
    if xfade < 64:
        return buf
    n = len(buf)
    for i in range(xfade):
        t = i / max(1, xfade - 1)
        blend = t * t * (3 - 2 * t)
        tail = n - xfade + i
        mixed = int(buf[i] * blend + buf[tail] * (1 - blend))
        buf[i] = mixed
        buf[tail] = mixed
    return buf


def _lowpass(buf, passes=1):
    if passes <= 0 or len(buf) < 3:
        return buf
    for _ in range(passes):
        prev = buf[0]
        for i in range(1, len(buf)):
            cur = buf[i]
            buf[i] = int(prev * 0.42 + cur * 0.58)
            prev = cur
    return buf


def _note_env(progress, attack=0.18, release=0.32):
    if progress < attack:
        return progress / max(attack, 0.001)
    if progress > 1.0 - release:
        return max(0.0, (1.0 - progress) / max(release, 0.001))
    return 1.0


def _build_phrases(root_hz, ratios, phrases, duration_sec, bpm=38):
    """Редкие ноты с паузами — без постоянного арпеджio."""
    beat = 60.0 / bpm
    events = []
    cursor = duration_sec * 0.06
    gap_range = (beat * 1.6, beat * 3.4)
    pr = 0.0
    for phrase in phrases:
        for note_idx, hold_beats in phrase:
            if cursor >= duration_sec * 0.92:
                break
            hold = beat * hold_beats
            freq = _scale_freq(root_hz * 2, ratios, note_idx)
            events.append((cursor, hold, freq))
            cursor += hold + gap_range[0] + (gap_range[1] - gap_range[0]) * pr
            pr = (pr * 0.618 + 0.382) % 1.0
        cursor += beat * 2.2
    return events


def _make_ambient_piece(
    root_hz,
    scale_ratios,
    phrases,
    duration_sec=68,
    volume=0.034,
    bpm=38,
    pad_mix=0.78,
    melody_mix=0.14,
    xfade_sec=5.5,
    sample_rate=_SAMPLE_RATE,
):
    """Длинный ambient с бесшовным зацикливанием и редкой мелодией."""
    n_samples = max(1, int(sample_rate * duration_sec))
    buf = array.array("h", [0] * n_samples)
    events = _build_phrases(root_hz, scale_ratios, phrases, duration_sec, bpm=bpm)

    pad_freqs = []
    for k in (1, 2, 3, 5):
        cycles = max(1, round(k * root_hz * duration_sec))
        pad_freqs.append((cycles / duration_sec, 0.34 / k, k * 0.7))

    for i in range(n_samples):
        t = i / sample_rate
        pad = 0.0
        for freq, amp, phase in pad_freqs:
            wobble = 1.0 + 0.0018 * math.sin(2 * math.pi * 0.023 * t + phase)
            pad += amp * math.sin(2 * math.pi * freq * wobble * t + phase)

        melody = 0.0
        for start, hold, freq in events:
            if t < start or t > start + hold:
                continue
            local = (t - start) / max(hold, 0.001)
            env = _note_env(local)
            partial = math.sin(2 * math.pi * freq * t)
            partial += 0.28 * math.sin(2 * math.pi * freq * 2.01 * t)
            melody += melody_mix * env * partial

        breath = 0.84 + 0.16 * math.sin(2 * math.pi * t / duration_sec)
        wave = _soft_clip((pad * pad_mix + melody) * breath)
        buf[i] = max(-32767, min(32767, int(volume * 32767 * wave)))

    buf = _lowpass(buf, passes=1)
    buf = _loop_crossfade(buf, sample_rate, xfade_sec=xfade_sec)
    return pygame.mixer.Sound(buffer=buf)


_AMBIENT_SPECS = {
    "menu": dict(
        root_hz=130.81, scale_ratios=_PENTATONIC_MAJOR,
        phrases=[
            [(0, 2.5), (2, 2.0), (4, 3.0)],
            [(3, 2.0), (1, 2.5), (4, 2.0)],
            [(2, 3.0), (0, 2.0), (3, 2.5)],
        ],
        duration_sec=72, volume=0.032, bpm=36,
    ),
    "forest": dict(
        root_hz=98.0, scale_ratios=_PENTATONIC_MINOR,
        phrases=[
            [(0, 2.5), (1, 2.0), (3, 3.0)],
            [(2, 2.5), (4, 2.0), (1, 2.5)],
            [(3, 2.0), (0, 3.0), (2, 2.0)],
        ],
        duration_sec=76, volume=0.033, bpm=34,
    ),
    "desert": dict(
        root_hz=87.31, scale_ratios=_PENTATONIC_MINOR,
        phrases=[
            [(0, 2.0), (2, 2.5), (1, 2.0)],
            [(3, 2.5), (2, 2.0), (4, 2.5)],
            [(1, 2.0), (0, 3.0)],
        ],
        duration_sec=68, volume=0.031, bpm=38,
    ),
    "snow": dict(
        root_hz=146.83, scale_ratios=_PENTATONIC_MAJOR,
        phrases=[
            [(0, 3.0), (2, 2.0), (4, 2.5)],
            [(5, 2.0), (3, 2.5), (1, 2.0)],
            [(2, 2.5), (4, 3.0)],
        ],
        duration_sec=80, volume=0.030, bpm=32, melody_mix=0.12,
    ),
    "ruins": dict(
        root_hz=92.5, scale_ratios=_PENTATONIC_MINOR,
        phrases=[
            [(0, 2.5), (1, 2.0), (2, 3.0)],
            [(4, 2.0), (3, 2.5), (1, 2.0)],
            [(2, 2.5), (0, 2.0)],
        ],
        duration_sec=74, volume=0.032, bpm=35,
    ),
    "combat": dict(
        root_hz=103.83, scale_ratios=_PENTATONIC_MINOR,
        phrases=[
            [(0, 1.8), (1, 1.5), (0, 1.8)],
            [(2, 1.5), (1, 2.0), (3, 1.5)],
            [(1, 1.8), (2, 1.5)],
        ],
        duration_sec=58, volume=0.034, bpm=42, pad_mix=0.82, melody_mix=0.10,
    ),
    "shop": dict(
        root_hz=116.54, scale_ratios=_PENTATONIC_MAJOR,
        phrases=[
            [(0, 2.0), (2, 2.5), (3, 2.0)],
            [(4, 2.0), (2, 2.0), (1, 2.5)],
            [(3, 2.5), (1, 2.0)],
        ],
        duration_sec=64, volume=0.031, bpm=40,
    ),
}


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
                pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._build_sfx()
        except pygame.error:
            self.enabled = False

    def _get_ambient(self, track):
        sound = self._ambient.get(track)
        if sound is not None:
            return sound
        spec = _AMBIENT_SPECS.get(track)
        if not spec:
            return None
        sound = _make_ambient_piece(**spec)
        self._ambient[track] = sound
        return sound

    def _build_sfx(self):
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
            ambient = self._get_ambient(self._current_track)
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
        ambient = self._get_ambient(track)
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
