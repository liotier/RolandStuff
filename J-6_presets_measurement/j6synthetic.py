#!/usr/bin/env python3
"""Synthetic takes with known answers, to check j6experiments.py.

  python3 j6synthetic.py synthetic
  python3 j6experiments.py synthetic -o synthetic_results

Writes one folder per experiment into OUT, in the format j6capture.py
records (stereo FLAC at 44.1 kHz plus a JSON sidecar), each built so that the
analysis has one right answer:

keysync    1-1 vibrato 5 Hz restarting with each note; 1-2 vibrato 4.444 Hz
           running freely; 1-3 a sample and hold at 4.444 Hz running freely
           (near the step detector's threshold: see keysync()); 1-4 no LFO
filters    3-5 a saw through a resonant lowpass (Q 8) whose cutoff is
           1000 Hz x 2^((FILTER - 120) / 14.4) x (note / 110 Hz)^0.5:
           keyboard tracking 0.50, 1 kHz at A2 for FILTER 120
longtail   1-3 releases of 4 dB/s (ENV 238) and 2 dB/s (ENV 255)
longnote   1-1 a vibrato on a dotted sixteenth, following the tempo (4.444 Hz
           at 100 BPM, 2.667 Hz at 60); 1-2 a filter LFO fixed at 6.81 Hz
keysync2   1-3 a free-running vibrato at 60 BPM (2 Hz, an eighth triplet)
chord      1-4 one 5 Hz filter LFO shared by the four voices; 1-5 a 4.444 Hz
           filter LFO per voice, restarting with each note
verylong   1-6 a filter LFO on four whole notes, following the tempo
           (0.104 Hz at 100 BPM, 0.0625 Hz at 60)
longnote2  1-7 a noisy source with a random filter movement; 1-8 the same
           source without; each at FILTER 120 and 255 (open)
keysync3   5-8 and 5-6: a filter envelope spike at each note-on and a
           0.556 Hz filter LFO, running freely (5-8) or restarting (5-6)

Needs numpy, scipy, soundfile, and j6capture.py beside it (for the stimuli).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import j6capture as C  # noqa: E402

SR, PRE = 44100, 0.8


def label(i: int) -> str:
    return f"{i // 8 + 1}-{i % 8 + 1}"


def save(out: Path, folder: str, n: int, sound: int, stim: str, left, right=None, bpm=100, **knobs) -> None:
    """One take: PRE s of silence, the signal, 1 s of silence; sidecar as j6capture writes it."""
    d = out / folder
    d.mkdir(parents=True, exist_ok=True)
    base = f"{folder}_P{n:02d}_{label(sound)}"
    z, tail = np.zeros(int(PRE * SR)), np.zeros(SR)
    right = left if right is None else right
    sf.write(d / f"{base}.flac", np.column_stack([np.concatenate([z, left, tail]), np.concatenate([z, right, tail])]),
             SR, subtype="PCM_24")
    events = [{"name": nm, "note": note, "velocity": 100, "on": on, "off": round(on + g, 4)}
              for nm, note, _, on, g in C.STIMULI[stim]]
    prm = {"SOUND": str(sound), "TEMPO": str(int(round(bpm * 100))), "FILTER": "128", "RESONANCE": "0",
           "ENV": "128", "ATTACK": "0"}
    prm.update({k: str(v) for k, v in knobs.items()})
    meta = {"pass": folder, "stimulus": stim, "prm": prm, "events": events,
            "recording": {"midi_started_after_arecord_start_s": PRE, "rate": SR}}
    (d / f"{base}.json").write_text(json.dumps(meta))


def take_time(stim: str):
    end = max(on + g for _, _, _, on, g in C.STIMULI[stim]) + C.TAIL[stim]
    return np.arange(int(end * SR)) / SR


def gate(t, on, off, release=0.03):
    """Linear 5 ms attack, held, exponential release (cut after 0.3 s)."""
    e = np.where((t >= on) & (t < off), 1.0, 0.0)
    a = (t >= on) & (t < on + 0.005)
    e[a] = (t[a] - on) / 0.005
    r = (t >= off) & (t < off + 0.3)
    e[r] = np.exp(-(t[r] - off) / release)
    return e


def voice(t, f0, cents=0.0, bright=3000.0, k_max=25):
    """A saw-like tone (1/k harmonics) with pitch in cents and a Gaussian
    lowpass at 'bright' Hz, both possibly arrays over t."""
    cents = np.broadcast_to(cents, t.shape)
    phase = 2 * np.pi * np.cumsum(f0 * 2 ** (cents / 1200)) / SR
    return sum((1 / k) * np.exp(-(k * f0 / np.asarray(bright)) ** 2) * np.sin(k * phase) for k in range(1, k_max + 1))


def keysync(out: Path) -> None:
    # The sample and hold's random values: across seeds 3, 7 and 11 the step
    # detector's averaged peak stands 4.55, 3.90 and 4.48 times the median,
    # against its threshold of 4 (the real 8-7: 2.7 at 100 BPM, 4.9 at 150).
    # Seed 3 is used so that the phase test is exercised.
    rng = np.random.default_rng(3)
    t = take_time("retrig")
    for n, (sound, mode, rate) in enumerate([(0, "restart", 5.0), (1, "free", 100 / 60 / 0.375),
                                             (2, "sh", 100 / 60 / 0.375), (3, "none", 0.0)], 1):
        x = np.zeros_like(t)
        for _, _, _, on, g in C.STIMULI["retrig"]:
            e = gate(t, on, on + g)
            sel = e > 0
            tt = t[sel]
            if mode == "restart":
                depth = np.clip((tt - on - 0.3) / 0.4, 0, 1)
                y = voice(tt, 110.0, 40 * depth * np.sin(2 * np.pi * rate * (tt - on) + 0.7))
            elif mode == "free":
                y = voice(tt, 110.0, 40 * np.sin(2 * np.pi * rate * tt + 1.3))
            elif mode == "sh":
                step = np.floor(tt * rate + 0.37).astype(int)
                values = rng.uniform(1, 12, step.max() - step.min() + 2)
                y = voice(tt, 110.0, 0.0, 110.0 * values[step - step.min()], k_max=29)
            else:
                y = voice(tt, 110.0)
            x[sel] += 0.1 * e[sel] * y
        save(out, "keysync", n, sound, "retrig", x)


def filters(out: Path) -> None:
    def biquad_lowpass(x, fc, q):
        w0 = 2 * np.pi * min(fc, 0.45 * SR) / SR
        alpha, c = np.sin(w0) / (2 * q), np.cos(w0)
        b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
        a = np.array([1 + alpha, -2 * c, 1 - alpha])
        return lfilter(b / a[0], a / a[0], x)
    t = take_time("filter")
    for n, v in enumerate([255] + list(range(17, 239, 17)), 1):
        x = np.zeros_like(t)
        for _, note, _, on, g in C.STIMULI["filter"]:
            f0 = 440 * 2 ** ((note - 69) / 12)
            e = gate(t, on, on + g)
            sel = e > 0
            y = 0.05 * voice(t[sel], f0, 0.0, 1e9, k_max=int(15000 // f0))
            if v != 255:
                y = biquad_lowpass(y, 1000 * 2 ** ((v - 120) / 14.4) * (f0 / 110) ** 0.5, 8.0) / 3
            x[sel] += e[sel] * y
        save(out, "filters", n, 20, "filter", x, FILTER=v, RESONANCE=0 if v == 255 else 255)


def longtail(out: Path) -> None:
    t = take_time("longtail")
    for n, (env, db_per_s) in enumerate([(238, 4.0), (255, 2.0)], 61):
        y = 0.2 * voice(t, 110.0, 0.0, 1e9, k_max=20) * np.where(t < 6.0, 1.0, 10 ** (-db_per_s * (t - 6.0) / 20))
        save(out, "longtail", n, 2, "longtail", y, ENV=env)


def longnote(out: Path) -> None:
    t = take_time("longnote")
    for n, (sound, bpm, mode) in enumerate([(0, 100, "synced"), (0, 60, "synced"), (1, 100, "fixed"), (1, 60, "fixed")], 1):
        e = gate(t, 0.0, 20.0)
        sel = e > 0
        tt = t[sel]
        if mode == "synced":
            y = voice(tt, 110.0, 30 * np.sin(2 * np.pi * bpm / 60 / 0.375 * tt))
        else:
            y = voice(tt, 110.0, 0.0, 1500 * 2 ** (0.4 * np.sin(2 * np.pi * 6.81 * tt)))
        x = np.zeros_like(t)
        x[sel] = 0.1 * e[sel] * y
        save(out, "longnote", n, sound, "longnote", x, bpm=bpm)


def keysync2(out: Path) -> None:
    t = take_time("retrig8")
    x = np.zeros_like(t)
    for _, _, _, on, g in C.STIMULI["retrig8"]:
        e = gate(t, on, on + g)
        sel = e > 0
        x[sel] += 0.1 * e[sel] * voice(t[sel], 110.0, 30 * np.sin(2 * np.pi * 2.0 * t[sel] + 0.4))
    save(out, "keysync2", 1, 2, "retrig8", x, bpm=60)


def chord(out: Path) -> None:
    t = take_time("chord")
    for n, (sound, mode, f) in enumerate([(3, "shared", 5.0), (4, "per voice", 100 / 60 / 0.375)], 1):
        x = np.zeros_like(t)
        for _, note, _, on, g in C.STIMULI["chord"]:
            f0 = 440 * 2 ** ((note - 69) / 12)
            e = gate(t, on, on + g)
            sel = e > 0
            tt = t[sel]
            lfo = np.sin(2 * np.pi * f * (tt if mode == "shared" else tt - on))
            x[sel] += 0.05 * e[sel] * voice(tt, f0, 0.0, 400 * 2 ** (0.6 * lfo))
        save(out, "chord", n, sound, "chord", x)


def verylong(out: Path) -> None:
    t = take_time("verylong")[: int(90.0 * SR)]
    for n, bpm in ((1, 100), (2, 60)):
        y = 0.1 * voice(t, 110.0, 0.0, 900 * 2 ** (0.7 * np.sin(2 * np.pi * bpm / 60 / 16 * t)), k_max=39)
        save(out, "verylong", n, 5, "verylong", y, bpm=bpm)


def longnote2(out: Path, rng) -> None:
    t = np.arange(int(20.0 * SR)) / SR
    for n, (sound, moving, filt) in enumerate([(6, True, 120), (6, True, 255), (7, False, 120), (7, False, 255)], 3):
        noise = rng.standard_normal(len(t)) * 0.3
        steps = np.repeat(rng.uniform(-1, 1, int(20.0 * 12) + 1), SR // 12)[: len(t)]
        steps = np.convolve(steps, np.ones(400) / 400, "same")
        cutoff = (600 * 2 ** (steps if moving else 0 * steps)) if filt < 255 else np.full(len(t), 8000.0)
        tone = voice(t, 110.0, 0.0, cutoff, k_max=39)
        coeff = np.exp(-2 * np.pi * np.minimum(cutoff, 8000) / SR)    # one-pole lowpass on the noise
        filtered, acc = np.zeros(len(t)), 0.0
        for i in range(len(t)):
            acc = coeff[i] * acc + (1 - coeff[i]) * noise[i]
            filtered[i] = acc
        # the noise differs a little between channels, as a chorus makes it
        save(out, "longnote2", n, sound, "longnote", 0.1 * (tone + filtered), 0.1 * (tone + np.roll(filtered, 37)),
             FILTER=filt)


def keysync3(out: Path) -> None:
    t = take_time("retrig8long")
    f = 100 / 60 / 3        # a dotted half at 100 BPM
    for n, (sound, mode) in enumerate([(39, "free"), (37, "restart")], 1):
        x = np.zeros_like(t)
        for _, _, _, on, g in C.STIMULI["retrig8long"]:
            sel = (t >= on) & (t < on + g)
            tt = t[sel] - on
            lt = t[sel] if mode == "free" else tt
            dips = -0.3 * np.clip(np.cos(2 * np.pi * f * lt + 0.5), 0.6, 1) + 0.18
            octaves = 0.9 * np.exp(-tt / 0.2) + 0.35 * np.sin(2 * np.pi * f * lt + 0.5) + dips
            env = np.minimum(tt / 0.005, 1) * (0.6 + 0.4 * np.exp(-tt / 0.3))
            x[sel] += 0.1 * env * voice(t[sel], 110.0, 0.0, 700 * 2 ** octaves, k_max=29)
        save(out, "keysync3", n, sound, "retrig8long", x)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="folder to create the synthetic experiment folders in")
    args = ap.parse_args()
    out = Path(args.out)
    rng = np.random.default_rng(7)
    for name, fn in (("keysync", lambda: keysync(out)), ("filters", lambda: filters(out)),
                     ("longtail", lambda: longtail(out)), ("longnote", lambda: longnote(out)),
                     ("keysync2", lambda: keysync2(out)), ("chord", lambda: chord(out)),
                     ("verylong", lambda: verylong(out)), ("longnote2", lambda: longnote2(out, rng)),
                     ("keysync3", lambda: keysync3(out))):
        fn()
        print(f"wrote {out / name}")


if __name__ == "__main__":
    main()
