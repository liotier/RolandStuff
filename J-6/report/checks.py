#!/usr/bin/env python3
"""The ad hoc checks quoted in README.md, beyond the CSV files in results/.

  python3 report/checks.py [CAPTURES]

Without CAPTURES, only the computations that need no recording run:
  - how often random phases reach a given concentration (section 4.5.9)
  - the average spectrum of a pulse whose width sweeps (section 4.5.6)
  - the apparent vibrato of a pulse-width modulation (section 4.5.15)
With CAPTURES (the folder holding open/, default/ and env255/):
  - the exact LFO rates of the plucks on the env255 takes, measured without
    the band excluded around the chorus (2-1, 1-6, 2-4, 1-4)
  - weak pitch ripples on 4-5 and 4-6, below the 6-cent detection threshold

Run it from the J-6 folder (it imports j6analyze.py).
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def phase_odds():
    rng = np.random.default_rng(1)
    for n in (7, 8):
        th = rng.uniform(0, 2 * np.pi, (2_000_000, n))
        r = np.abs(np.exp(1j * th).mean(axis=1))
        print(f"{n} random phases: median concentration {np.median(r):.2f}, "
              f"P(>= 0.8) {np.mean(r >= 0.8):.4f}, P(>= 0.9) {np.mean(r >= 0.9):.5f}")


def swept_pulse():
    saw = -20 * np.log10(np.arange(1, 9))
    for lo, hi in ((0.05, 0.5), (0.1, 0.5), (0.2, 0.5)):
        d = np.linspace(lo, hi, 20001)
        p = np.array([np.mean(np.sin(np.pi * k * d) ** 2) / k ** 2 for k in range(1, 9)])
        rel = 10 * np.log10(p / p[0])
        print(f"width swept {lo:.2f}-{hi:.2f}: harmonics 2-5 at {np.round(rel[1:5], 1)} dB "
              f"(saw {np.round(saw[1:5], 1)}), largest deviation up to the 8th {np.max(np.abs(rel - saw)):.1f} dB")


def pwm_vibrato(f0=110.0, rate=4.444, swing=0.2):
    """A pulse with one fixed edge: harmonic k's phase is -pi k d, so a moving
    width d shifts every harmonic by the ratio -d'(t) / (2 f0)."""
    peak = 2 * math.pi * rate * swing / (2 * f0)
    print(f"width +-{swing} at {rate} Hz on {f0} Hz: apparent vibrato "
          f"{1200 * math.log2(1 + peak) - 1200 * math.log2(1 - peak):.0f} cents peak to peak")


def take(cap, pas, lab):
    import j6analyze as A
    i = (int(lab[0]) - 1) * 8 + int(lab[2]) - 1
    return A.Take(cap / pas / f"{pas}_P{i + 1:02d}_{A.label(i)}.json")


def pluck_rates(cap):
    import j6analyze as A
    for lab, octave in (("2-1", 0), ("1-6", 1), ("2-4", 1), ("1-4", 0)):
        tk = take(cap, "env255", lab)
        end = min(A.audible_until(tk, 6.0), 5.95)
        tr = A.track(tk, 0.1, end, A.A2 * 2 ** octave)
        for col, name in ((1, "brightness"), (2, "even share"), (0, "pitch")):
            left, right = A._clean(tr[:, 0, col]), A._clean(tr[:, 1, col])
            if left is None or right is None:
                continue
            m = (left + right) / 2
            spec = np.abs(np.fft.rfft(m * np.hanning(len(m)), 1 << 16))
            f = np.fft.rfftfreq(1 << 16, 0.01)
            sel = np.flatnonzero((f > 0.25) & (f < 12))
            k = sel[np.argmax(spec[sel])]
            y0, y1, y2 = np.log(spec[k - 1:k + 2])
            fr = f[k] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (f[1] - f[0])
            print(f"{lab} {name:10s}: {fr:.3f} Hz, {spec[k] / np.median(spec[sel]):.0f} x median, "
                  f"note value at 100 BPM {A.note_value(fr, 100)}")


def weak_vibrato(cap):
    import csv
    import j6analyze as A
    octave = {r["sound"]: int(r["osc_octave"]) for r in csv.DictReader(open("results/measurements.csv"))}
    for lab in ("4-5", "4-6"):
        for pas in ("open", "default"):
            tk = take(cap, pas, lab)
            end = min(A.audible_until(tk, 6.0), 5.95)
            tr = A.track(tk, 0.1, end, A.A2 * 2 ** octave[lab])
            left, right = A._clean(tr[:, 0, 0]), A._clean(tr[:, 1, 0])
            mean = (left + right) / 2
            late = mean[len(mean) // 3:]                       # past any delay
            spec = np.abs(np.fft.rfft(late * np.hanning(len(late)), 1 << 15))
            f = np.fft.rfftfreq(1 << 15, 0.01)
            sel = np.flatnonzero((f > 0.3) & (f < 18))
            base = np.median(spec[sel])
            used, out = [], []
            for i in sel[np.argsort(spec[sel])[::-1]]:
                if any(abs(f[i] - u) < 0.4 for u in used):
                    continue
                used.append(f[i])
                corr = np.corrcoef(A.band(left, f[i]), A.band(right, f[i]))[0, 1]
                bm = A.band(mean, f[i])
                out.append(f"{f[i]:.2f} Hz x{spec[i] / base:.1f} L/R {corr:+.2f} "
                           f"{np.percentile(bm, 95) - np.percentile(bm, 5):.1f} cents")
                if len(out) == 3:
                    break
            print(f"{lab} {pas:7s}: " + " | ".join(out))


if __name__ == "__main__":
    phase_odds()
    swept_pulse()
    pwm_vibrato()
    if len(sys.argv) > 1:
        cap = Path(sys.argv[1])
        pluck_rates(cap)
        weak_vibrato(cap)
