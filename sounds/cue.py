#!/usr/bin/env python3
"""Короткие мажорные сигналы для хуков Claude Code.

    cue.py gen                          — сгенерировать все варианты
    cue.py preview [done|ask|done-5]    — прослушать (фильтр по префиксу)
    cue.py pick done-5-tryam ask-5-mew  — назначить done.wav / ask.wav
    cue.py --selftest                   — проверка генератора

Хуки играют только done.wav / ask.wav (симлинки), поэтому смена звука
не требует правки settings.json.
"""

import math
import os
import random
import struct
import subprocess
import sys
import time
import wave

SR = 44100
DIR = os.path.dirname(os.path.abspath(__file__))

# Равномерная темперация, A4 = 440 Гц
C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
C5, D5, E5, F5, G5, A5, B5 = 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77
C6, D6, E6, G6, A6, B6 = 1046.50, 1174.66, 1318.51, 1567.98, 1760.00, 1975.53

# harm — (множитель частоты, амплитуда); vib — глубина вибрато в долях частоты
TIMBRES = {
    # звонкий колокольчик: яркие обертоны, резкая атака
    "bright": dict(harm=[(1, 1.0), (2, 0.25), (3, 0.08)],
                   attack=0.005, decay=5.0, tail=0.25, vib=0.0, peak=0.85),
    # мягкий мурчащий: субоктава даёт тепло, вибрато — живость
    "soft": dict(harm=[(0.5, 0.18), (1, 1.0), (2, 0.06)],
                 attack=0.030, decay=2.6, tail=0.45, vib=0.004, peak=0.62),
    # бархатный: почти чистый тон, тяжёлая субоктава, медленный вход
    # и длинный хвост — самый неназойливый из трёх
    "velvet": dict(harm=[(0.5, 0.32), (1, 1.0), (2, 0.025)],
                   attack=0.055, decay=1.7, tail=0.60, vib=0.002, peak=0.50),

    # --- щипковые (Карплус-Стронг): струна, а не синтез ---
    # арфа: длинная мягкая струна, тёплый щипок
    "harp":    dict(engine="pluck", loss=0.9975, damp=0.52, pick=4,
                    tail=0.38, peak=0.58),
    # калимба: короче звенит, щипок ярче
    "kalimba": dict(engine="pluck", loss=0.9955, damp=0.42, pick=2,
                    tail=0.30, peak=0.60),

    # --- молоточковые: неравные обертоны, каждый гаснет по-своему ---
    # маримба: деревянно, обертон на дуодециму, быстрый спад
    "marimba": dict(engine="mallet", attack=0.004, tail=0.32, peak=0.58,
                    partials=[(1.0, 1.0, 3.4), (3.94, 0.34, 8.0), (9.2, 0.10, 14.0)]),
    # музыкальная шкатулка: стеклянный обертон, долгое послезвучие
    "box":     dict(engine="mallet", attack=0.003, tail=0.42, peak=0.55,
                    partials=[(1.0, 1.0, 2.6), (2.0, 0.30, 4.5), (5.4, 0.16, 9.0)]),

    # --- рояль: струна с жёсткостью + вторая, чуть расстроенная ---
    "piano":   dict(engine="piano", attack=0.004, tail=0.55, peak=0.60,
                    partials=8, stiff=0.00042, bright=1.25,
                    detune=0.0007, decay=2.0, spread=0.42),
    # тот же рояль, но снятый с педали: гаснет быстрее, хвост короче
    "grand":   dict(engine="piano", attack=0.004, tail=0.40, peak=0.60,
                    partials=8, stiff=0.00042, bright=1.30,
                    detune=0.0007, decay=3.1, spread=0.45),
}

VIB_HZ = 5.5
RELEASE = 0.03  # общий фейд в конце буфера, чтобы не обрывалось

# имя -> (тембр, [(частоты звучащие вместе, длительность до следующей ноты)])
VARIANTS = {
    # --- короткие рояльные аккорды: один удар, разная гармония ---
    "done-j-major": ("grand", [([C5, E5, G5], 0.40)]),
    "done-k-maj7":  ("grand", [([C5, E5, G5, B5], 0.40)]),
    "done-l-add9":  ("grand", [([C5, E5, G5, D6], 0.40)]),
    "done-m-open":  ("grand", [([C4, G4, C5], 0.42)]),
    "done-n-roll":  ("grand", [([C5], 0.03), ([E5], 0.03), ([G5], 0.40)]),
    "done-o-six":   ("grand", [([C5, E5, G5, A5], 0.40)]),
    # --- рояльные фразы ---
    "done-g-piano":   ("piano", [([C4, G4], 0.17, 0.60), ([E5], 0.10, 0.70),
                                 ([G5], 0.10, 0.75), ([C6, E6], 0.50, 1.0)]),
    "done-h-cadence": ("piano", [([G4, D5, B5], 0.22, 0.75),
                                 ([C4, E5, C6], 0.55, 1.0)]),
    "done-i-ripple":  ("piano", [([C6], 0.08, 0.85), ([G5], 0.08, 0.60),
                                 ([E5], 0.08, 0.65), ([C5, G5], 0.52, 1.0)]),
    # --- инструментальные фразы: каждая со своим ритмом и динамикой ---
    # (ноты, длительность, громкость) — громкость лепит фразировку
    "done-a-tala":  ("kalimba", [([G4], 0.10, 0.55), ([C5], 0.44, 1.0)]),
    "done-b-harp":  ("harp",    [([C5], 0.06, 0.45), ([E5], 0.06, 0.55),
                                 ([G5], 0.06, 0.70), ([C6], 0.09, 0.85),
                                 ([E6], 0.40, 1.0)]),
    "done-c-box":   ("box",     [([E6], 0.11, 0.80), ([D6], 0.09, 0.55),
                                 ([E6], 0.11, 0.85), ([G6], 0.42, 1.0)]),
    "done-d-skip":  ("marimba", [([C5], 0.10, 0.90), ([G5], 0.07, 0.55),
                                 ([E5], 0.10, 0.75), ([C6], 0.40, 1.0)]),
    "done-e-waltz": ("harp",    [([G4], 0.17, 1.0), ([C5], 0.11, 0.55),
                                 ([E5], 0.11, 0.60), ([G5], 0.40, 0.85)]),
    "done-f-bloom": ("harp",    [([C4, G4], 0.18, 0.70), ([E5], 0.10, 0.60),
                                 ([G5], 0.45, 1.0)]),
    # --- бархатные, октавой ниже: для сигнала «закончил, жду ответа» ---
    "done-9-velvet":  ("velvet", [([C4, E4, G4], 0.70)]),
    "done-10-breath": ("velvet", [([E4], 0.16), ([G4], 0.50)]),
    "done-11-glow":   ("velvet", [([C4], 0.14), ([E4], 0.14), ([G4], 0.46)]),
    "done-12-hush":   ("velvet", [([A4], 0.15), ([F4], 0.50)]),
    "done-13-halo":   ("velvet", [([G4, C5], 0.65)]),
    "done-14-nod":    ("velvet", [([E4], 0.13), ([C5], 0.44)]),
    # --- мягкие, «трям-па-ра-лям» ---
    "done-5-tryam":   ("soft", [([E5], 0.15), ([G5], 0.11), ([A5], 0.11), ([C6], 0.42)]),
    "done-6-purr":    ("soft", [([C5], 0.13), ([E5], 0.13), ([G5], 0.13), ([C6], 0.40)]),
    "done-7-lull":    ("soft", [([G5], 0.14), ([E5], 0.12), ([D5], 0.12), ([C5], 0.45)]),
    "done-8-warm":    ("soft", [([C5, E5, G5], 0.55)]),
    "ask-5-mew":      ("soft", [([E5], 0.12), ([G5], 0.30)]),
    "ask-6-hm":       ("soft", [([G5], 0.10), ([A5], 0.10), ([D6], 0.30)]),
    "ask-7-tap":      ("soft", [([C5], 0.10), ([E5], 0.26)]),
    # --- звонкие, первый заход ---
    "done-1-arp":     ("bright", [([C6], 0.09), ([E6], 0.09), ([G6], 0.28)]),
    "done-2-bell":    ("bright", [([C6, E6, G6], 0.50)]),
    "done-3-fifth":   ("bright", [([C6], 0.13), ([G6], 0.30)]),
    "done-4-resolve": ("bright", [([G5], 0.13), ([C6], 0.32)]),
    "ask-1-third":    ("bright", [([E6], 0.08), ([G6], 0.18)]),
    "ask-2-sixth":    ("bright", [([C6], 0.09), ([A6], 0.20)]),
    "ask-3-double":   ("bright", [([G6], 0.07), ([G6], 0.16)]),
    "ask-4-rise":     ("bright", [([G6], 0.08), ([B6], 0.18)]),
}


def unpack(segment):
    """(ноты, длительность[, громкость]) -> тройка."""
    freqs, dur = segment[0], segment[1]
    return freqs, dur, segment[2] if len(segment) > 2 else 1.0


def pluck(freqs, dur, gain, tb, buf, offset):
    """Карплус-Стронг: шумовой щипок, гуляющий по кольцевой линии задержки.

    Кольцо длиной SR/f задаёт высоту, усреднение соседей съедает верхние
    обертоны — так струна тускнеет со временем, как настоящая."""
    n = int((dur + tb["tail"]) * SR)
    fade = int(0.004 * SR)  # микро-атака: без неё щелчок на старте
    for f in freqs:
        size = max(2, int(SR / f))
        rng = random.Random(int(f * 100))
        ring = [rng.uniform(-1.0, 1.0) for _ in range(size)]
        for _ in range(tb["pick"]):  # мягче щипок — меньше «песка» в атаке
            ring = [(ring[i] + ring[i - 1]) * 0.5 for i in range(size)]
        idx = 0
        for i in range(n):
            if offset + i >= len(buf):
                break
            sample = ring[idx]
            nxt = ring[(idx + 1) % size]
            ring[idx] = tb["loss"] * (tb["damp"] * sample + (1.0 - tb["damp"]) * nxt)
            env = gain if i >= fade else gain * i / fade
            buf[offset + i] += env * sample / len(freqs)
            idx = (idx + 1) % size


def mallet(freqs, dur, gain, tb, buf, offset):
    """Молоточек: неравные обертоны, каждый со своей скоростью затухания."""
    n = int((dur + tb["tail"]) * SR)
    for f in freqs:
        for mult, amp, decay in tb["partials"]:
            for i in range(n):
                if offset + i >= len(buf):
                    break
                t = i / SR
                env = math.exp(-decay * t)
                if t < tb["attack"]:
                    env *= t / tb["attack"]
                buf[offset + i] += (gain * amp * env
                                    * math.sin(2 * math.pi * f * mult * t) / len(freqs))


def piano(freqs, dur, gain, tb, buf, offset):
    """Струна рояля: жёсткость растягивает обертоны вверх (f_n = n*f*sqrt(1+B*n^2)),
    верхние гаснут быстрее нижних, а вторая расстроенная струна даёт биение."""
    n = int((dur + tb["tail"]) * SR)
    for f in freqs:
        for string, weight in ((1.0, 1.0), (1.0 + tb["detune"], 0.85)):
            for k in range(1, tb["partials"] + 1):
                amp = weight / k ** tb["bright"]
                decay = tb["decay"] * (1.0 + tb["spread"] * (k - 1))
                fk = k * f * string * math.sqrt(1.0 + tb["stiff"] * k * k)
                if fk > SR / 2:
                    break
                step = 2 * math.pi * fk / SR
                for i in range(n):
                    if offset + i >= len(buf):
                        break
                    t = i / SR
                    env = math.exp(-decay * t)
                    if env < 2e-4:          # обертон уже неслышен — дальше не считаем
                        break
                    if t < tb["attack"]:
                        env *= t / tb["attack"]
                    buf[offset + i] += gain * amp * env * math.sin(step * i) / len(freqs)


def voice(freqs, dur, tb, buf, offset, gain=1.0):
    """Подмешивает ноту (или аккорд) в буфер начиная с offset."""
    engine = tb.get("engine")
    if engine == "pluck":
        return pluck(freqs, dur, gain, tb, buf, offset)
    if engine == "mallet":
        return mallet(freqs, dur, gain, tb, buf, offset)
    if engine == "piano":
        return piano(freqs, dur, gain, tb, buf, offset)
    n = int((dur + tb["tail"]) * SR)
    decay = tb["decay"] / (dur + tb["tail"])
    for i in range(n):
        if offset + i >= len(buf):
            break
        t = i / SR
        env = math.exp(-decay * t)
        if t < tb["attack"]:
            env *= t / tb["attack"]
        bend = 1.0 + tb["vib"] * math.sin(2 * math.pi * VIB_HZ * t)
        s = 0.0
        for f in freqs:
            for mult, amp in tb["harm"]:
                s += amp * math.sin(2 * math.pi * f * mult * bend * t)
        buf[offset + i] += gain * env * s / len(freqs)


def render(timbre, segments):
    """Сегменты -> список float-сэмплов, нормализованный по пику."""
    tb = TIMBRES[timbre]
    total = sum(unpack(seg)[1] for seg in segments) + tb["tail"]
    buf = [0.0] * int(total * SR)

    offset = 0
    for segment in segments:
        freqs, dur, gain = unpack(segment)
        voice(freqs, dur, tb, buf, offset, gain)
        offset += int(dur * SR)

    rel = int(RELEASE * SR)
    for i in range(min(rel, len(buf))):
        buf[len(buf) - 1 - i] *= i / rel

    peak = max((abs(s) for s in buf), default=0.0)
    if peak > 0:
        buf = [s * tb["peak"] / peak for s in buf]
    return buf


def write_wav(path, buf):
    frames = struct.pack("<%dh" % len(buf), *(int(s * 32767) for s in buf))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(frames)


def gen():
    os.makedirs(DIR, exist_ok=True)
    for name, (timbre, segments) in VARIANTS.items():
        write_wav(os.path.join(DIR, name + ".wav"), render(timbre, segments))
        print("  " + name + ".wav")
    print("готово: %d файлов в %s" % (len(VARIANTS), DIR))


def preview(prefix=""):
    for name in [n for n in VARIANTS if n.startswith(prefix)]:
        path = os.path.join(DIR, name + ".wav")
        if not os.path.exists(path):
            sys.exit("нет %s — сначала: cue.py gen" % path)
        print("> " + name, flush=True)
        subprocess.run(["afplay", path], check=False)
        time.sleep(0.7)


def pick(names):
    for name in names:
        if name not in VARIANTS:
            sys.exit("неизвестный вариант: %s\nдоступны: %s" % (name, ", ".join(VARIANTS)))
        kind = name.split("-")[0]
        link = os.path.join(DIR, kind + ".wav")
        if os.path.islink(link) or os.path.exists(link):
            os.remove(link)
        os.symlink(name + ".wav", link)
        print("%s.wav -> %s.wav" % (kind, name))


def selftest():
    import tempfile

    for timbre in TIMBRES:
        buf = render(timbre, [([C5], 0.12), ([E5, G5], 0.25)])
        assert buf, "пустой буфер"
        assert all(-1.0 <= s <= 1.0 for s in buf), "сэмплы вне диапазона"
        assert abs(max(abs(s) for s in buf) - TIMBRES[timbre]["peak"]) < 1e-6, "нормализация сломана"
        assert abs(buf[0]) < 1e-9, "атака не сглажена — будет щелчок"
        assert abs(buf[-1]) < 1e-9, "релиз не сглажен — будет щелчок"

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        write_wav(f.name, buf)
        with wave.open(f.name, "rb") as w:
            assert w.getnchannels() == 1
            assert w.getsampwidth() == 2
            assert w.getframerate() == SR
            assert w.getnframes() == len(buf)

    for name, (timbre, segments) in VARIANTS.items():
        assert name.split("-")[0] in ("done", "ask"), name
        assert timbre in TIMBRES, name
        length = sum(unpack(seg)[1] for seg in segments) + TIMBRES[timbre]["tail"]
        assert 0.2 < length < 1.6, "%s длится %.2f с" % (name, length)

    print("selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "gen"
    if cmd == "--selftest":
        selftest()
    elif cmd == "gen":
        gen()
    elif cmd == "preview":
        preview(args[1] if len(args) > 1 else "")
    elif cmd == "pick":
        pick(args[1:])
    else:
        sys.exit(__doc__)
