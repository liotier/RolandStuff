#!/usr/bin/env python3
"""Analyse the experiment passes recorded by j6passes.sh: tempo150, velocity,
poly, sweep, keysync, filters and longtail.

  python3 j6experiments.py captures -o results

Run it from the experiment folder. CAPTURES holds the experiment folders
below; tempo150 also needs default/ (the reference at 100 BPM). Each
experiment found writes its CSV files into the output folder and prints a
summary.

tempo      every sound at 150 BPM against the default pass: LFO rates, the
           note values they match, their onset delays, and measurements that
           should not depend on tempo (attack, sustain, release, glide); on
           sounds without a periodic LFO, the rate of stepped (sample-and-
           hold) brightness changes, reported when it follows the tempo
velocity   A3 at 16 velocities, one per second: level and brightness (spectral
           centroid) of each note against velocity 127, the exponent n of
           level ~ velocity^n, and the brightness trend across velocities
           (on sounds with chorus or an LFO the notes catch the modulation at
           different phases, which shows as scatter, not as a trend)
poly       six notes entering 0.5 s apart, all held to 4 s: level of each
           note's fundamental in 0.4 s windows, which shows how many voices
           sound and which notes are dropped
sweep      the built-in plan of j6prm.py: FILTER on 6-8 at resonance 255 (the
           frequency of the resonant peak, A2 and A4), RESONANCE on 2-7 (gain at
           each harmonic against resonance 0), ATTACK on 2-7 (rise times) and
           ENV on 1-3 (decay, sustain, release, brightness over time)
keysync    seven A2 notes per sound with an LFO: whether the LFO's phase
           restarts with each note or runs freely (8-7's sample and hold at
           150 BPM, where its steps stand out from its chorus)
filters    FILTER 17-238 at RESONANCE 255 on 6-8, 2-7, 4-6 and 4-4, notes A1
           to A4: each sound's cutoff offset, steps per octave and keyboard
           tracking, from the resonant peak against a FILTER 255 reference
longtail   1-3 at ENV 221, 238 and 255: releases of many seconds

Needs j6analyze.py and j6prm.py beside it, numpy, scipy and soundfile.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import j6analyze as A  # noqa: E402
from j6prm import sweep_plan  # noqa: E402

r = A.r
NOTE_NAMES = {48: "C3", 52: "E3", 55: "G3", 59: "B3", 62: "D4", 65: "F4"}


def write(path: Path, rows: list[dict]) -> None:
    fields = []
    for row in rows:
        fields += [k for k in row if k not in fields]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


def takes(folder: Path) -> list[A.Take]:
    return [A.Take(js) for js in sorted(folder.glob(f"{folder.name}_P*.json"))]


def sound_of(tk: A.Take) -> str:
    return A.label(int(tk.meta["prm"]["SOUND"]))


def log_slope(x, y):
    """Slope and intercept of log2(y) against x."""
    k, c = np.polyfit(np.asarray(x, float), np.log2(np.asarray(y, float)), 1)
    return k, c


# ---------------------------------------------------------------- tempo
def jumps(tk: A.Take, a: float, b: float, hop: float = 0.01):
    """Size of the frame-to-frame jumps of the spectral centroid (log2, 40 ms
    frames, hop apart) between a and b, and the time of each jump."""
    ts = np.arange(a, b - 0.04, hop)
    c = np.array([A.centroid(tk.seg(t, t + 0.04), tk.sr) for t in ts])
    ok = np.isfinite(c) & (c > 0)
    if len(c) < 50 or ok.mean() < 0.8:
        return None, None
    c = np.interp(np.arange(len(c)), np.flatnonzero(ok), np.log2(c[ok]))
    return ts[1:] + 0.02, np.abs(np.diff(c))


def peak_rate(d, hop=0.01, fmin=0.5, fmax=20.0) -> float:
    spec = np.abs(np.fft.rfft((d - d.mean()) * np.hanning(len(d)), 1 << 14))
    f = np.fft.rfftfreq(1 << 14, hop)
    sel = (f > fmin) & (f < fmax)
    return float(f[sel][np.argmax(spec[sel])])


def averaged_peak_rate(ds, exclude=(), hop=0.01, fmin=0.5, fmax=20.0):
    """Strongest periodicity of several jump series together (their spectra,
    each divided by its median, summed), away from the excluded rates; and its
    height against the median of the sum."""
    f = np.fft.rfftfreq(1 << 14, hop)
    tot = np.zeros(len(f))
    for d in ds:
        spec = np.abs(np.fft.rfft((d - d.mean()) * np.hanning(len(d)), 1 << 14))
        tot += spec / max(np.median(spec), 1e-12)
    sel = (f > fmin) & (f < fmax)
    for e in exclude:
        sel &= np.abs(f - e) >= 0.35
    i = int(np.argmax(np.where(sel, tot, -1)))
    return float(f[i]), float(tot[i] / np.median(tot[sel]))


def step_rate(tk: A.Take) -> float | None:
    """Rate of a stepped (sample-and-hold) brightness modulation: the
    strongest periodicity, 0.5-20 Hz, in the size of the centroid's jumps on
    the long note."""
    end = min(A.audible_until(tk, 6.0), 5.9)
    if end < 1.7:
        return None
    _, d = jumps(tk, 0.2, end)
    return None if d is None else peak_rate(d)


def tempo(root: Path, out: Path) -> None:
    keys = ("amp_attack_ms", "amp_sustain_db", "amp_release_-20dB_ms", "glide_ms",
            "chorus", "filter_env_oct")
    rows, pairs = [], []
    for i in range(64):
        lab = A.label(i)
        a = root / "default" / f"default_P{i + 1:02d}_{lab}.json"
        b = root / "tempo150" / f"tempo150_P{i + 1:02d}_{lab}.json"
        if not (a.exists() and b.exists()):
            continue
        res = {}
        for tag, js in (("default", a), ("tempo150", b)):
            res[tag] = A.analyse_sound({"default": A.Take(js)}, i)
        row = {"sound": lab}
        for tag in res:
            row[f"bpm_{tag}"] = res[tag].get("tempo_bpm")
        for lfo in ("vibrato", "filter_lfo", "pwm"):
            for q in ("hz", "note", "delay_s"):
                for tag in res:
                    row[f"{lfo}_{q}_{tag}"] = res[tag].get(f"{lfo}_{q}")
            x, y = res["default"].get(f"{lfo}_hz"), res["tempo150"].get(f"{lfo}_hz")
            if x and y:
                pairs.append((lab, lfo, x, y, res["default"].get(f"{lfo}_note"),
                               res["tempo150"].get(f"{lfo}_note"),
                               res["default"].get(f"{lfo}_delay_s"),
                               res["tempo150"].get(f"{lfo}_delay_s")))
        for k in keys:
            for tag in res:
                row[f"{k}_{tag}"] = res[tag].get(k)
        # sounds without a periodic LFO: a stepped modulation whose clock
        # follows the tempo shows as a jump rate scaled by the tempo ratio
        if not any(res[tag].get(f"{lfo}_hz") for tag in res for lfo in ("vibrato", "filter_lfo", "pwm")):
            for tag, js in (("default", a), ("tempo150", b)):
                sr_ = step_rate(A.Take(js))
                row[f"step_hz_{tag}"] = r(sr_, 2)
                row[f"step_note_{tag}"] = A.note_value(sr_, res[tag]["tempo_bpm"]) if sr_ and res[tag].get("tempo_bpm") else None
        rows.append(row)
        print(f"  {lab}", end="", flush=True)
    print()
    write(out / "tempo.csv", rows)
    if not rows:
        return
    expected = rows[0]["bpm_tempo150"] / rows[0]["bpm_default"] if rows[0]["bpm_default"] else 1.5
    ratios = np.array([y / x for _, _, x, y, *_ in pairs])
    near = int(np.sum(np.abs(ratios / expected - 1) < 0.02))
    same_note = sum(1 for p in pairs if p[4] and p[4] == p[5])
    print(f"  LFOs found at both tempos: {len(pairs)}; rate ratio median {np.median(ratios):.3f} "
          f"(tempo ratio {expected:.3f}); within 2 % of the tempo ratio: {near}; "
          f"same note value: {same_note}")
    delays = [(lab, lfo, x, y, d1, d2) for lab, lfo, x, y, n1, n2, d1, d2 in pairs if d1 and d2]
    if delays:
        q = np.median([d2 / d1 for *_, d1, d2 in delays])
        print(f"  LFO delays measured at both tempos: {len(delays)}; ratio median {q:.2f} "
              f"({1 / expected:.2f} if they followed the tempo)")
    for lab, lfo, x, y, d1, d2 in delays:
        print(f"    {lab} {lfo:<10} {x:5.2f} -> {y:5.2f} Hz, delay {d1:.2f} -> {d2:.2f} s")
    for row in rows:
        x, y = row.get("step_hz_default"), row.get("step_hz_tempo150")
        if x and y and abs(y / x / expected - 1) < 0.03 and row["step_note_default"] \
                and row["step_note_default"] == row["step_note_tempo150"]:
            print(f"  {row['sound']}: stepped brightness modulation (sample and hold) at {x:.2f} -> {y:.2f} Hz, "
                  f"note value {row['step_note_default']} at both tempos")


# ---------------------------------------------------------------- velocity
def velocity(root: Path, out: Path) -> None:
    rows = []
    for tk in takes(root / "velocity"):
        lab = sound_of(tk)
        evs = sorted(tk.events.values(), key=lambda e: e["on"])
        v = np.array([e["velocity"] for e in evs], float)
        lv = np.array([tk.level(e["on"] + 0.02, e["on"] + 0.25) for e in evs])
        br = np.array([A.centroid(tk.seg(e["on"] + 0.02, e["on"] + 0.25), tk.sr) for e in evs])
        x = 20 * np.log10(v / 127)
        n, c = np.polyfit(x, lv, 1)
        resid = np.abs(lv - (c + n * x)).max()
        lb = np.log2(br / br[-1])
        slope, c2 = np.polyfit(v / 127, lb, 1)
        scatter = float(np.std(lb - (c2 + slope * v / 127)))
        for e, vv, ll, bb in zip(evs, v, lv, lb):
            rows.append({"sound": lab, "velocity": int(vv), "level_db_re_127": r(ll - lv[-1], 2),
                         "brightness_oct_re_127": r(bb, 3), "level_exponent": r(n, 3),
                         "level_residual_max_db": r(resid, 2), "brightness_slope_oct": r(slope, 3),
                         "brightness_scatter_oct": r(scatter, 3)})
        print(f"  {lab}: level ~ velocity^{n:.2f} (largest residual {resid:.2f} dB, "
              f"{lv[0] - lv[-1]:+.1f} dB from {int(v[0])} to 127); brightness trend {slope:+.2f} octave "
              f"from 0 to 127, scatter {scatter:.2f} octave")
    write(out / "velocity.csv", rows)


# ---------------------------------------------------------------- poly
def poly(root: Path, out: Path) -> None:
    rows = []
    for tk in takes(root / "poly"):
        lab = sound_of(tk)
        notes = sorted(tk.events.values(), key=lambda e: e["on"])
        last_on = notes[-1]["on"]
        end = min(e["off"] for e in notes)
        held = {}
        for t in np.arange(0.25, end, 0.5):
            f, m = A.spectrum(tk.seg(t - 0.2, t + 0.2), tk.sr, 1 << 18)
            p = []
            for e in notes:
                f0 = 440 * 2 ** ((e["note"] - 69) / 12)
                sel = np.abs(f - f0) < f0 * 0.008
                p.append(float(m[sel].max()) ** 2)
            ref = max(p)
            for e, pp in zip(notes, p):
                started = e["on"] <= t - 0.2
                lvl = 10 * math.log10(pp / ref + 1e-12)
                rows.append({"sound": lab, "from_s": r(t - 0.2, 2), "to_s": r(t + 0.2, 2),
                             "note": NOTE_NAMES.get(e["note"], e["note"]), "entered_s": e["on"],
                             "level_db": r(lvl) if started else None})
                if started and t - 0.2 >= last_on:
                    held.setdefault(e["note"], []).append(lvl)
        sounding = [NOTE_NAMES.get(n, n) for n, ls in held.items() if min(ls) > -30]
        dropped = [NOTE_NAMES.get(n, n) for n, ls in held.items() if min(ls) <= -30]
        print(f"  {lab}: after the last note enters, {len(sounding)} notes sound "
              f"({' '.join(sounding)}), dropped: {' '.join(dropped) or 'none'}")
    write(out / "poly.csv", rows)


# ---------------------------------------------------------------- sweeps
def strongest(tk: A.Take, a: float, b: float) -> float:
    f, m = A.spectrum(tk.seg(a, b), tk.sr, 1 << 18)
    sel = (f > 20) & (f < 16000)
    return float(f[sel][np.argmax(m[sel])])


def sweep_filter(group: list[tuple[int, A.Take]], out: Path) -> None:
    """Resonance 255: the strongest spectral peak is the filter's own ringing,
    so its frequency follows the cutoff. Takes more than 25 dB below the
    loudest one are the filter closed on noise and get no frequency."""
    rows = []
    for v, tk in group:
        a4 = tk.events["key_A4"]
        rows.append({"FILTER": v, "sound": sound_of(tk),
                     "level_A2_dbfs": r(tk.level(0.5, 2.0)), "peak_A2_hz": r(strongest(tk, 0.5, 2.0)),
                     "level_A4_dbfs": r(tk.level(a4["on"] + 0.3, a4["off"] - 0.05)),
                     "peak_A4_hz": r(strongest(tk, a4["on"] + 0.3, a4["off"] - 0.05))})
    for note in ("A2", "A4"):
        top = max(row[f"level_{note}_dbfs"] for row in rows)
        for row in rows:
            if row[f"level_{note}_dbfs"] < top - 25:
                row[f"peak_{note}_hz"] = None
    write(out / "sweep_filter.csv", rows)
    lo = [(row["FILTER"], row["peak_A2_hz"]) for row in rows if row["peak_A2_hz"] and row["peak_A2_hz"] < 2000]
    if len(lo) >= 3:
        k, c = log_slope(*zip(*lo))
        print(f"  FILTER: {1 / k:.1f} steps per octave below 2 kHz; resonant peak at A2 = "
              f"{2 ** c:.2f} Hz x 2^(FILTER/{1 / k:.1f}), from {lo[0][1]:.0f} Hz at {lo[0][0]}")
    both = [math.log2(row["peak_A4_hz"] / row["peak_A2_hz"]) / 2 for row in rows
            if row["peak_A2_hz"] and row["peak_A4_hz"] and row["peak_A4_hz"] < 8000]
    if both:
        print(f"  key tracking (octaves of cutoff per octave of pitch, A2 to A4): "
              f"median {np.median(both):.2f}, range {min(both):.2f}-{max(both):.2f}")
    print(f"  highest peaks: A2 {max(row['peak_A2_hz'] or 0 for row in rows):.0f} Hz, "
          f"A4 {max(row['peak_A4_hz'] or 0 for row in rows):.0f} Hz")


def harmonic_gains(tk, ref, a, b, base, kmax):
    hs = []
    for t in (tk, ref):
        f, m = A.spectrum(t.seg(a, b), t.sr, 1 << 18)
        hs.append(A.grid(f, m, base, kmax, rel=0.03))
    h, h0 = hs
    ok = h0 > h0.max() * 10 ** (-50 / 20)
    g = 20 * np.log10((h + 1e-12) / (h0 + 1e-12))
    k = int(np.argmax(np.where(ok, g, -999)))
    return g[0], g[k], base * (k + 1)


def sweep_resonance(group, out: Path) -> None:
    """Gain at each harmonic against the take at resonance 0: the passband loss
    at the fundamental and the height and place of the resonant peak (to the
    nearest harmonic: 110 Hz steps at A2, 440 Hz at A4)."""
    ref = group[0][1]
    rows = []
    for v, tk in group:
        a4 = tk.events["key_A4"]
        row = {"RESONANCE": v, "sound": sound_of(tk)}
        for note, (a, b, base, kmax) in (("A2", (4.5, 5.9, 110.0, 48)),
                                         ("A4", (a4["on"] + 0.3, a4["off"] - 0.1, 440.0, 12))):
            g0, gp, fp = harmonic_gains(tk, ref, a, b, base, kmax)
            row.update({f"fundamental_gain_{note}_db": r(g0), f"peak_gain_{note}_db": r(gp),
                        f"peak_{note}_hz": r(fp, 0)})
        rows.append(row)
    write(out / "sweep_resonance.csv", rows)
    hi = rows[-1]
    best = max(rows, key=lambda row: row["peak_gain_A2_db"])
    print(f"  RESONANCE: at {hi['RESONANCE']}, fundamental {hi['fundamental_gain_A2_db']:+.1f} dB (A2), "
          f"{hi['fundamental_gain_A4_db']:+.1f} dB (A4); resonant peak {hi['peak_gain_A2_db']:+.1f} dB near "
          f"{hi['peak_A2_hz']:.0f} Hz (A2), {hi['peak_gain_A4_db']:+.1f} dB near {hi['peak_A4_hz']:.0f} Hz (A4); "
          f"largest peak {best['peak_gain_A2_db']:+.1f} dB at RESONANCE {best['RESONANCE']}")


def sweep_attack(group, out: Path) -> None:
    """Rise of the 6 s A2 note (20 ms smoothing): time to 20, 10 and 3 dB below
    its peak, and to the peak."""
    rows = []
    for v, tk in group:
        t, ls = tk.curve(0, 6.0, smooth=0.02)
        pk = ls.max()
        row = {"ATTACK": v, "sound": sound_of(tk)}
        for d in (20, 10, 3, 0):
            row[f"rise_to_-{d}dB_ms" if d else "rise_to_peak_ms"] = r(
                1000 * max(t[np.flatnonzero(ls >= pk - d)[0]], 0.0), 0)
        env = A.envelope(tk, 6.0, 3.0)
        row["sustain_db"] = env["sustain_db"]
        row["release_-20dB_ms"] = env["release_-20dB_ms"]
        rows.append(row)
    write(out / "sweep_attack.csv", rows)
    pts = [(row["ATTACK"], row["rise_to_-3dB_ms"]) for row in rows if row["rise_to_-3dB_ms"] >= 20]
    if len(pts) >= 3:
        k, _ = log_slope(*zip(*pts))
        print(f"  ATTACK: rise to -3 dB from {pts[0][1]:.0f} ms at {pts[0][0]} to {pts[-1][1]:.0f} ms at "
              f"{pts[-1][0]}, doubling every {1 / k:.0f} steps; below {pts[0][0]} it is under 20 ms; "
              f"release -20 dB stays {min(row['release_-20dB_ms'] or 0 for row in rows):.0f}-"
              f"{max(row['release_-20dB_ms'] or 0 for row in rows):.0f} ms")


def sweep_env(group, out: Path) -> None:
    """The 6 s A2 note and a 0.15 s staccato A2: decay, sustain, release, and
    brightness (spectral centroid) at 0.05, 1 and 5 s."""
    rows = []
    for v, tk in group:
        e = A.envelope(tk, 6.0, 7.5)
        st = tk.events["staccato_A2"]
        before = tk.level(st["off"] - 0.03, st["off"])
        t, lv = tk.curve(st["off"], st["off"] + 5.5)
        k = np.flatnonzero(lv <= before - 20)
        audible = before > tk.level(st["on"], st["off"]) - 40
        row = {"ENV": v, "sound": sound_of(tk), "decay_to_-20dB_ms": e["decay_to_-20dB_ms"],
               "decay_to_-40dB_ms": e["decay_to_-40dB_ms"], "sustain_db": e["sustain_db"],
               "release_-20dB_ms": e["release_-20dB_ms"], "release_-40dB_ms": e["release_-40dB_ms"],
               "staccato_release_-20dB_ms": r(1000 * (t[k[0]] - st["off"]), 0) if audible and len(k) else None}
        for a in (0.05, 1.0, 5.0):
            row[f"centroid_{a:g}s_hz"] = r(A.centroid(tk.seg(a, a + 0.1), tk.sr), 0)
        rows.append(row)
    write(out / "sweep_env.csv", rows)
    plucks = [row for row in rows if row["sustain_db"] is None]
    held = [row for row in rows if row["sustain_db"] is not None]
    if plucks:
        print(f"  ENV {plucks[0]['ENV']}-{plucks[-1]['ENV']}: no sustain, decay to -20 dB "
              f"{plucks[0]['decay_to_-20dB_ms']:.0f}-{plucks[-1]['decay_to_-20dB_ms']:.0f} ms")
    if held:
        rel = [row["release_-20dB_ms"] for row in held if row["release_-20dB_ms"]]
        print(f"  ENV {held[0]['ENV']}-{held[-1]['ENV']}: sustain {held[0]['sustain_db']:+.1f} to "
              f"{held[-1]['sustain_db']:+.1f} dB, release to -20 dB {min(rel):.0f}-{max(rel):.0f} ms "
              f"(longer ones exceed the 7.5 s window)")


SWEEPS = {"FILTER": sweep_filter, "RESONANCE": sweep_resonance, "ATTACK": sweep_attack, "ENV": sweep_env}


def sweep(root: Path, out: Path) -> None:
    plan = sweep_plan()
    groups: dict[str, list] = {}
    for n, step in plan.items():
        hits = sorted((root / "sweep").glob(f"sweep_P{n:02d}_*.json"))
        if hits:
            knob = next(k for k in step if k != "sound")
            tk = A.Take(hits[0])
            if int(tk.meta["prm"][knob]) != step[knob]:
                sys.exit(f"{hits[0]}: {knob} is {tk.meta['prm'][knob]}, the sweep plan says {step[knob]}")
            groups.setdefault(knob, []).append((step[knob], tk))
    for knob, group in groups.items():
        SWEEPS[knob](sorted(group, key=lambda g: g[0]), out)

# ---------------------------------------------------------------- keysync
BEATS = {name: beats for beats, name in A.NOTE_VALUES}
FIT_FROM = 1.0   # s after each note-on: past the LFO delays measured (0.9 s at most)


def phase_fit(t, s, f):
    """Amplitude and phase lag theta of s ~ A cos(2 pi f t - theta) + c."""
    m = np.column_stack([np.cos(2 * np.pi * f * t), np.sin(2 * np.pi * f * t), np.ones_like(t)])
    (a, b, _), *_ = np.linalg.lstsq(m, s, rcond=None)
    return math.hypot(a, b), math.atan2(b, a)


def chorus_exclusion(root: Path, tk: A.Take, notes) -> tuple[str, list[float]]:
    """Chorus I, II, on (rate unclear) or Off, and the rates its free-running
    sweep shows at in the measurements: its rate, half and twice it, as in
    j6analyze.py. The chorus is read from the sound's 6 s note in the default
    pass when captures/default holds it (a 3.5 s note often leaves the rate
    unclear), else by a vote over the notes."""
    i = int(tk.meta["prm"]["SOUND"])
    ref = root / "default" / f"default_P{i + 1:02d}_{A.label(i)}.json"
    if ref.exists():
        dt = A.Take(ref)
        ch = A.chorus(dt, 0.3, min(A.audible_until(dt, 6.0), 5.95)).get("chorus", "on")
    else:
        votes = [A.chorus(tk, e["on"] + 0.3, e["off"] - 0.05).get("chorus") for e in notes]
        named = [v for v in votes if v in A.CHORUS_MOD]
        ch = max(set(named), key=named.count) if named else ("on" if "on" in votes else "Off")
    rates = [A.CHORUS_MOD[ch]] if ch in A.CHORUS_MOD else (list(A.CHORUS_MOD.values()) if ch == "on" else [])
    return ch, [v * m for v in rates for m in (0.5, 1, 2)]


def consistent_rate(rates, n):
    """Median of the rates if more than half of n notes lie within 5 % (at
    least 0.12 Hz) of it, else None."""
    if not rates:
        return None
    med = float(np.median(rates))
    close = sum(abs(x - med) <= max(0.05 * med, 0.12) for x in rates)
    return med if close > n // 2 else None


def concentration(angles) -> float:
    return float(abs(np.mean(np.exp(1j * np.asarray(angles)))))


def keysync(root: Path, out: Path) -> None:
    """Seven A2 notes per sound. The LFO is found on each note (pitch,
    brightness or even-harmonic share; the stepped brightness of a sample and
    hold otherwise), its rate set to the exact note value at the pattern
    tempo, and its phase measured on each note from 1 s after the note-on. If
    the LFO restarts with each note, the phase relative to the note-on is the
    same on every note; if it runs freely, the phase relative to the take is.
    The note onsets are spread so that one hypothesis predicts scattered
    phases where the other predicts equal ones (concentration of the onsets'
    phases at most 0.46 for every note value at 100 BPM)."""
    rows, summary = [], []
    for tk in takes(root / "keysync"):
        lab = sound_of(tk)
        bpm = float(tk.meta["prm"].get("TEMPO", 10000)) / 100
        notes = sorted(tk.events.values(), key=lambda e: e["on"])
        tracks = [A.track(tk, e["on"] + 0.1, e["off"] - 0.05, A.A2) for e in notes]
        ch, exclude = chorus_exclusion(root, tk, notes)
        # a detection counts if most notes agree on its rate and it is a note value
        # (minimum swings as in j6analyze.py: smaller ones include the frame
        # analysis's own ripple, 10 Hz for A2 at 10 ms frames)
        cand = {}
        for col, kind, least in ((0, "vibrato", 6.0), (1, "filter LFO", 0.1), (2, "PWM", 0.05)):
            found = [res for res in (A.lfo(tr, col, exclude) if tr is not None else None for tr in tracks)
                     if res and res[2] > least]
            rate = consistent_rate([res[0] for res in found], len(notes))
            nv = A.note_value(rate, bpm) if rate else None
            if nv:
                cand[kind] = (col, rate, float(np.median([res[1] for res in found])),
                              float(np.median([res[2] for res in found])), nv)
        # one LFO moving several things shows in several measurements; a pitch
        # or pulse-width change also shifts the brightness (as in j6analyze.py)
        for weaker, stronger, small in (("filter LFO", "PWM", 0.5), ("filter LFO", "vibrato", 0.5),
                                        ("vibrato", "PWM", 25.0)):
            if weaker in cand and stronger in cand and abs(cand[weaker][1] - cand[stronger][1]) < 0.1 \
                    and cand[weaker][3] < small:
                del cand[weaker]
        series = []
        if cand:
            kind = max(cand, key=lambda k: cand[k][2])
            col, _, _, _, nv = cand[kind]
            for e, tr in zip(notes, tracks):
                sv = A._clean((tr[:, 0, col] + tr[:, 1, col]) / 2) if tr is not None else None
                if sv is not None:
                    series.append((e, 0.14 + 0.01 * np.arange(len(sv)), sv))
        else:
            # a sample and hold: steps in brightness, found on the jump-size
            # spectrum averaged over the notes (on one note the chorus's sweep
            # often outweighs it)
            per = [jumps(tk, e["on"] + 0.1, e["off"] - 0.05) for e in notes]
            per = [(e, t, d) for e, (t, d) in zip(notes, per) if d is not None]
            if len(per) > len(notes) // 2:
                rate, prom = averaged_peak_rate([d for _, _, d in per], exclude)
                nv = A.note_value(rate, bpm)
                if nv and prom >= 4:
                    kind = "stepped brightness"
                    series = [(e, t - e["on"], d - d.mean()) for e, t, d in per]
        if not series:
            print(f"  {lab}: no LFO found on the notes")
            summary.append({"sound": lab, "chorus": ch, "verdict": "no LFO found"})
            continue
        f = bpm / 60 / BEATS[nv]
        rel, ab = [], []
        for e, tau, sv in series:
            sel = tau >= FIT_FROM
            amp, theta = phase_fit(tau[sel], sv[sel], f)
            big = theta + 2 * np.pi * f * e["on"]
            rel.append(theta)
            ab.append(big)
            rows.append({"sound": lab, "measurement": kind, "rate_hz": r(f, 3), "note_value": nv,
                         "note": e["name"], "onset_s": e["on"], "amplitude": r(amp, 4),
                         "phase_re_note_on_deg": r(math.degrees(theta) % 360, 0),
                         "phase_re_take_deg": r(math.degrees(big) % 360, 0)})
        r_rel, r_abs = concentration(rel), concentration(ab)
        r_on = concentration([2 * np.pi * f * e["on"] for e, _, _ in series])
        window = min(len(t) for _, t, _ in series) * 0.01 - FIT_FROM
        if f * window < 1.0:
            verdict = "too slow to tell"
        elif r_rel >= 0.8 and r_rel - r_abs >= 0.3:
            verdict = "restarts with each note"
        elif r_abs >= 0.8 and r_abs - r_rel >= 0.3:
            verdict = "free-running"
        else:
            verdict = "unclear"
        summary.append({"sound": lab, "chorus": ch, "measurement": kind, "rate_hz": r(f, 3), "note_value": nv,
                        "notes": len(series), "concentration_re_note_on": r(r_rel, 2),
                        "concentration_re_take": r(r_abs, 2), "onset_concentration": r(r_on, 2),
                        "verdict": verdict})
        print(f"  {lab}: {kind} {f:.2f} Hz ({nv}): phase concentration {r_rel:.2f} against the note-on, "
              f"{r_abs:.2f} against the take -> {verdict}")
    write(out / "keysync_notes.csv", rows)
    write(out / "keysync.csv", summary)
    counts = {}
    for row in summary:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    print("  " + ", ".join(f"{v}: {n}" for v, n in sorted(counts.items())))


# ---------------------------------------------------------------- filters
def resonant_peak(tk: A.Take, ref: A.Take, a: float, b: float, f0: float):
    """Gain of each harmonic against the reference take (FILTER 255,
    RESONANCE 0), within 50 dB of the reference's strongest harmonic and below
    12 kHz. The resonant peak is the largest gain, if it stands 6 dB above
    the median gain of the harmonics below it and is not the first or last
    one; its frequency is refined by a parabola through the gains (dB) of
    its neighbours against log frequency."""
    kmax = int(12000 // f0)
    hs = []
    for t in (tk, ref):
        f, m = A.spectrum(t.seg(a, b), t.sr, 1 << 18)
        hs.append(A.grid(f, m, f0, kmax, rel=0.03))
    h, h0 = hs
    valid = np.flatnonzero(h0 > h0.max() * 10 ** (-50 / 20))
    g = 20 * np.log10((h + 1e-12) / (h0 + 1e-12))
    j = int(valid[np.argmax(g[valid])])
    gain = float(g[j])
    if j in (valid[0], valid[-1]) or j - 1 not in valid or j + 1 not in valid:
        return None, gain
    if gain - np.median(g[valid[valid < j]]) < 6:
        return None, gain
    x = np.log2(f0 * np.array([j, j + 1, j + 2]))
    c2, c1, _ = np.polyfit(x, g[j - 1:j + 2], 2)
    xv = -c1 / (2 * c2) if c2 < 0 else x[1]
    return float(2 ** min(max(xv, x[0]), x[2])), gain


# Fit limits. Below the 6th harmonic the harmonics sample a sharp peak too
# coarsely (errors of 100-500 cents on synthetic data, under 60 above it).
# On 6-8 the mapping is exponential up to FILTER 170 and flattens above it,
# towards a ceiling near 16 kHz.
MIN_HARMONIC, MAX_FIT_HZ, MAX_FIT_FILTER = 6, 8000, 170


def filters(root: Path, out: Path) -> None:
    """FILTER 17-238 at RESONANCE 255 on four sounds, each note A1 to A4
    measured from 0.8 s after its note-on (past the filter envelope's sweep)
    against the sound's FILTER 255 / RESONANCE 0 reference. Per sound, a fit
    log2(peak) = a + b FILTER + c log2(note / A2) over the well-resolved peaks
    of the exponential region (see the limits above) gives the steps per
    octave (1/b), the keyboard tracking (c, octaves per octave) and the
    FILTER value that puts the peak at 1 kHz on A2: the sound's cutoff
    offset. filters.csv keeps every peak, fitted or not."""
    groups: dict[str, dict] = {}
    for tk in takes(root / "filters"):
        prm = tk.meta["prm"]
        g = groups.setdefault(sound_of(tk), {"ref": None, "sweep": []})
        if int(prm["FILTER"]) == 255 and int(prm["RESONANCE"]) == 0:
            g["ref"] = tk
        else:
            g["sweep"].append((int(prm["FILTER"]), tk))
    rows, summary = [], []
    for lab, g in groups.items():
        if g["ref"] is None:
            print(f"  {lab}: no reference take (FILTER 255, RESONANCE 0), skipped")
            continue
        pts = []
        for v, tk in sorted(g["sweep"], key=lambda x: x[0]):
            for e in sorted(tk.events.values(), key=lambda e: e["on"]):
                f0 = 440 * 2 ** ((e["note"] - 69) / 12)
                a, b = e["on"] + 0.8, e["off"] - 0.05
                pk, gain = resonant_peak(tk, g["ref"], a, b, f0)
                rows.append({"sound": lab, "FILTER": v, "RESONANCE": int(tk.meta["prm"]["RESONANCE"]),
                             "note": e["name"].split("_")[-1], "note_hz": r(f0, 2),
                             "level_dbfs": r(tk.level(a, b)), "peak_hz": r(pk, 0),
                             "peak_harmonic": r(pk / f0, 1) if pk else None, "peak_gain_db": r(gain),
                             "strongest_hz": r(strongest(tk, a, b), 0)})
                if pk and pk / f0 >= MIN_HARMONIC and pk < MAX_FIT_HZ and v <= MAX_FIT_FILTER:
                    pts.append((v, math.log2(f0 / 110), math.log2(pk)))
        if len(pts) < 4 or len({p[1] for p in pts}) < 2:
            print(f"  {lab}: too few resonant peaks for a fit ({len(pts)})")
            continue
        x = np.array(pts)
        m = np.column_stack([np.ones(len(x)), x[:, 0], x[:, 1]])
        (a0, b0, c0), *_ = np.linalg.lstsq(m, x[:, 2], rcond=None)
        res = 1200 * (x[:, 2] - m @ np.array([a0, b0, c0]))
        at1k = (math.log2(1000) - a0) / b0
        summary.append({"sound": lab, "points": len(pts), "steps_per_octave": r(1 / b0, 2),
                        "key_tracking": r(c0, 2), "FILTER_for_1kHz_at_A2": r(at1k, 1),
                        "residual_rms_cents": r(float(np.sqrt(np.mean(res ** 2))), 0)})
        print(f"  {lab}: {1 / b0:.1f} steps per octave, keyboard tracking {c0:.2f}, 1 kHz at A2 for "
              f"FILTER {at1k:.0f} (fit on {len(pts)} peaks, residual {np.sqrt(np.mean(res ** 2)):.0f} cents rms)")
    write(out / "filters.csv", rows)
    write(out / "filters_summary.csv", summary)


# ---------------------------------------------------------------- longtail
def longtail(root: Path, out: Path) -> None:
    """One 6 s A2 note and 30 s of release: time for the release to fall 20,
    40 and 60 dB below the level at note-off (50 ms smoothing), and the decay
    rate between -10 and -40 dB, extrapolated to a 60 dB fall."""
    rows = []
    for tk in takes(root / "longtail"):
        prm = tk.meta["prm"]
        off = tk.events["long_A2"]["off"]
        start = tk.level(off - 0.08, off - 0.01)
        t, lv = tk.curve(off, off + 29.5, smooth=0.05)
        t = t - off
        row = {"sound": sound_of(tk), "ENV": int(prm["ENV"]), "level_at_off_dbfs": r(start)}
        limit = tk.floor_db + 10 if tk.floor_db > -99 else -100
        for drop in (20, 40, 60):
            k = np.flatnonzero(lv <= start - drop)
            row[f"release_-{drop}dB_s"] = r(float(t[k[0]]), 2) if len(k) and start - drop > limit else None
        sel = (lv <= start - 10) & (lv >= start - 40) & (t > 0)
        if sel.sum() > 20:
            slope = np.polyfit(t[sel], lv[sel], 1)[0]
            row["decay_db_per_s"] = r(float(-slope), 2)
            row["release_60dB_extrapolated_s"] = r(float(60 / -slope), 1) if slope < 0 else None
        rows.append(row)
        print(f"  {row['sound']} ENV {row['ENV']}: release to -20 / -40 / -60 dB "
              f"{row['release_-20dB_s']} / {row['release_-40dB_s']} / {row['release_-60dB_s']} s, "
              f"{row.get('decay_db_per_s')} dB/s")
    write(out / "longtail.csv", rows)



def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captures", help="folder holding default/ and the experiment folders")
    ap.add_argument("-o", "--output", default="results", help="folder for the CSV files (default results)")
    args = ap.parse_args()
    root, out = Path(args.captures), Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    found = False
    for name, fn in (("tempo150", tempo), ("velocity", velocity), ("poly", poly), ("sweep", sweep),
                     ("keysync", keysync), ("filters", filters), ("longtail", longtail)):
        if (root / name).is_dir():
            found = True
            print(f"== {name}")
            fn(root, out)
    if not found:
        sys.exit(f"no experiment folder (tempo150, velocity, poly, sweep, keysync, filters, "
                 f"longtail) in {root}")


if __name__ == "__main__":
    main()
