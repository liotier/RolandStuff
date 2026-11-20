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
verylong   as longnote, 90 s notes: modulations down to 0.056 Hz
longnote2  as longnote, sounds at several FILTER settings: a filter LFO hidden
           by an open filter, a filter movement told from the source's noise
longnote   one 20 s A2 note: every modulation's exact rate, whether it is a
           note value or a harmonic of the chorus LFO, and, for a sound
           recorded at two tempos, whether it follows the tempo
keysync2   as keysync, eight notes, sounds at 60, 70 and 100 BPM
chord      four notes entering at 0, 0.25, 0.51 and 1.05 s: whether the
           voices share one LFO phase or each starts its own at its note-on

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


def averaged_peak_rate(ds, exclude=(), hop=0.01, fmin=0.5, fmax=20.0, guard=0.35):
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
        sel &= np.abs(f - e) >= guard
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


# Note values for reporting a measured rate, the triplet whole note included
# (two slow LFOs run at 0.624 Hz, 2 2/3 beats at 100 BPM)
REPORT_VALUES = sorted(A.NOTE_VALUES + [(8 / 3, "1/1T"), (6, "1/1."), (8, "2/1"), (16, "4/1"), (32, "8/1"),
                                        (1 / 16, "1/64"), (1 / 32, "1/128")], reverse=True)


def nearest_value(rate: float, bpm: float):
    beats, name = min(REPORT_VALUES, key=lambda nv: abs(math.log(rate * nv[0] * 60 / bpm)))
    return name, 100 * (rate * beats * 60 / bpm - 1)


def note_phases(series, f):
    """Per-note amplitude, phase against the note-on and against the take."""
    out = []
    for e, tau, sv in series:
        sel = tau >= FIT_FROM
        amp, theta = phase_fit(tau[sel], sv[sel], f)
        out.append((e, amp, theta, theta + 2 * np.pi * f * e["on"]))
    return out


def free_rate(series, f_med: float, bpm: float):
    """Rate at which the notes' phases against the take agree best, weighted
    by amplitude: first among the note values within 0.45 Hz of the per-note
    estimate (which sits up to 0.35 Hz off when the true rate lies in a band
    excluded around the chorus's harmonics), then, if none agrees, within
    0.06 Hz of it. The search stays narrow because the onsets, about 4.6 s
    apart, make rates 0.22 Hz apart look alike."""
    def score(f):
        ph = note_phases(series, f)
        return (abs(np.mean([a * np.exp(1j * big) for _, a, _, big in ph])),
                concentration([big for _, _, _, big in ph]))
    grid = [bpm / 60 / b for b, _ in REPORT_VALUES if abs(bpm / 60 / b - f_med) <= 0.45]
    if grid:
        f = max(grid, key=lambda g: score(g)[0])
        if score(f)[1] >= 0.9:
            return f
    return max(np.arange(f_med - 0.06, f_med + 0.0601, 0.002), key=lambda g: score(g)[0])


def known_rates(longnote_rows, lab: str, bpm: float) -> list[tuple[str, float]]:
    """Modulations the long note found on this sound at this tempo, chorus
    harmonics left out, plus those found at another tempo that follow the
    tempo (their rate scaled), each rate set to its note value when within
    0.5 % or 0.01 Hz (the long note's precision)."""
    out = []
    for row in longnote_rows or []:
        if row["sound"] != lab or not row.get("rate_hz") or row["chorus_harmonic"]:
            continue
        if row["measurement"] not in ("vibrato", "filter LFO", "PWM", "audio-rate component"):
            continue
        if row["tempo_bpm"] == bpm:
            f = row["rate_hz"]
        elif row.get(f"at_{bpm:g}_bpm") == "follows the tempo":
            f = row["rate_hz"] * bpm / row["tempo_bpm"]
        else:
            continue
        name, _ = nearest_value(f, bpm)
        exact = bpm / 60 / dict((nm, bt) for bt, nm in REPORT_VALUES)[name]
        if abs(f - exact) < max(0.005 * exact, 0.01):
            f = exact
        if all(abs(f - g) > 0.02 or k != row["measurement"] for k, g in out):
            out.append((row["measurement"], f))
    return out


def audio_phases(tk: A.Take, notes, f: float):
    """Phase of the component at f on each note (a DFT from 0.5 s after the
    note-on), against the note-on and against the take."""
    rel, big = [], []
    for e in notes:
        a, b = e["on"] + 0.5, e["off"] - 0.05
        x = tk.seg(a, b)
        t = a + np.arange(len(x)) / tk.sr
        z = np.sum(x * np.exp(-2j * np.pi * f * t))
        big.append(float(np.angle(z)))
        rel.append(float(np.angle(z) + 2 * np.pi * f * e["on"]))
    return rel, big


def keysync(root: Path, out: Path, folder: str = "keysync", known=None) -> None:
    """Seven A2 notes per sound. Each modulation (pitch, brightness, even-
    harmonic share; the stepped brightness of a sample and hold when none is
    periodic) is found on most notes at one rate, then its phase is measured
    on each note from 1 s after the note-on, with a sinusoid at a fixed rate.
    If the LFO restarts with each note, the phases against the note-on agree;
    if it runs freely, the phases against the take agree. Agreement is the
    concentration of the seven phases (1 = equal, about 0.4 = scattered).
    The note onsets are spread so that one hypothesis predicts scattered
    phases where the other predicts equal ones (onset concentration at most
    0.46 for every note value at 100 BPM). The phases against the note-on
    are measured at the per-note rate (insensitive to small errors), those
    against the take at the rate the coherence scan finds."""
    rows, summary = [], []
    for tk in takes(root / folder):
        lab = sound_of(tk)
        bpm = float(tk.meta["prm"].get("TEMPO", 10000)) / 100
        notes = sorted(tk.events.values(), key=lambda e: e["on"])
        tracks = [A.track(tk, e["on"] + 0.1, e["off"] - 0.05, A.A2) for e in notes]
        ch, exclude = chorus_exclusion(root, tk, notes)
        chorus_lfo = ([A.CHORUS_MOD[ch] / 2] if ch in A.CHORUS_MOD else
                      [v / 2 for v in A.CHORUS_MOD.values()] if ch == "on" else [])
        # (minimum swings as in j6analyze.py: smaller ones include the frame
        # analysis's own ripple, 10 Hz for A2 at 10 ms frames)
        cand = {}
        # with the long notes' rates, the phases are measured at those rates
        # (the per-note detection misses slow LFOs next to the chorus)
        rates = known_rates(known, lab, bpm)
        if rates:
            verdicts = []
            for kind, f in rates:
                if kind == "audio-rate component":
                    rel, big = audio_phases(tk, notes, f)
                else:
                    col = {"vibrato": 0, "filter LFO": 1, "PWM": 2}[kind]
                    series = []
                    for e, tr in zip(notes, tracks):
                        sv = A._clean((tr[:, 0, col] + tr[:, 1, col]) / 2) if tr is not None else None
                        if sv is not None:
                            series.append((e, 0.14 + 0.01 * np.arange(len(sv)), sv))
                    ph = note_phases(series, f)
                    rel, big = [th for _, _, th, _ in ph], [b for _, _, _, b in ph]
                for e, th, b in zip(notes, rel, big):
                    rows.append({"sound": lab, "tempo_bpm": bpm, "measurement": kind, "rate_hz": r(f, 3),
                                 "note": e["name"], "onset_s": e["on"],
                                 "phase_re_note_on_deg": r(math.degrees(th) % 360, 0),
                                 "phase_re_take_deg": r(math.degrees(b) % 360, 0)})
                r_note, r_take = concentration(rel), concentration(big)
                verdict = ("restarts with each note" if r_note >= 0.8 and r_note - r_take >= 0.3 else
                           "free-running" if r_take >= 0.9 and r_take - r_note >= 0.3 else "unclear")
                name, dev = nearest_value(f, bpm)
                summary.append({"sound": lab, "tempo_bpm": bpm, "chorus": ch, "measurement": kind,
                                "rate_hz": r(f, 3), "nearest_note_value": name, "deviation_pct": r(dev, 1),
                                "concentration_re_note_on": r(r_note, 2), "concentration_re_take": r(r_take, 2),
                                "verdict": verdict, "rate_from": "long note"})
                verdicts.append(f"{kind} {f:.3f} Hz ({name}): {r_note:.2f} against the note-on, "
                                f"{r_take:.2f} against the take -> {verdict}")
            print(f"  {lab} at {bpm:g} BPM, rates from the long note: " + "; ".join(verdicts))
            continue
        for col, kind, least in ((0, "vibrato", 6.0), (1, "filter LFO", 0.1), (2, "PWM", 0.05)):
            found = [res for res in (A.lfo(tr, col, exclude) if tr is not None else None for tr in tracks)
                     if res and res[2] > least]
            rate = consistent_rate([res[0] for res in found], len(notes))
            if rate:
                series = []
                for e, tr in zip(notes, tracks):
                    sv = A._clean((tr[:, 0, col] + tr[:, 1, col]) / 2) if tr is not None else None
                    if sv is not None:
                        series.append((e, 0.14 + 0.01 * np.arange(len(sv)), sv))
                cand[kind] = (rate, float(np.median([res[1] for res in found])), series)
        if not cand:
            per = [jumps(tk, e["on"] + 0.1, e["off"] - 0.05) for e in notes]
            per = [(e, t, d) for e, (t, d) in zip(notes, per) if d is not None]
            if len(per) > len(notes) // 2:
                rate, prom = averaged_peak_rate([d for _, _, d in per], exclude, fmax=9.5)
                if prom >= 4 and A.note_value(rate, bpm):
                    cand["stepped brightness"] = (rate, prom, [(e, t - e["on"], d - d.mean()) for e, t, d in per])
        if not cand:
            print(f"  {lab} at {bpm:g} BPM: no LFO found on the notes")
            summary.append({"sound": lab, "tempo_bpm": bpm, "chorus": ch, "verdict": "no LFO found"})
            continue
        verdicts = []
        for kind, (f_med, prom, series) in sorted(cand.items(), key=lambda kv: -kv[1][1]):
            # a free-running harmonic of the chorus LFO is the chorus, not an LFO
            k = [n for c in chorus_lfo for n in range(2, 13) if abs(f_med - n * c) < 0.03]
            if k and kind != "stepped brightness":
                verdicts.append(f"{kind} {f_med:.2f} Hz: harmonic {k[0]} of the chorus LFO, skipped")
                continue
            ph = note_phases(series, f_med)
            r_note = concentration([th for _, _, th, _ in ph])
            if r_note >= 0.8 and r_note - concentration([big for _, _, _, big in ph]) >= 0.3:
                verdict, f = "restarts with each note", f_med
            else:
                f = free_rate(series, f_med, bpm)
                ph = note_phases(series, f)
                if concentration([big for _, _, _, big in ph]) >= 0.9 and \
                        concentration([big for _, _, _, big in ph]) - concentration([th for _, _, th, _ in ph]) >= 0.3:
                    verdict = "free-running"
                else:
                    verdict, f = "unclear", f_med
            ph = note_phases(series, f)
            r_note = concentration([th for _, _, th, _ in ph])
            r_take = concentration([big for _, _, _, big in ph])
            name, dev = nearest_value(f, bpm)
            for e, amp, theta, big in ph:
                rows.append({"sound": lab, "measurement": kind, "rate_hz": r(f, 3), "note": e["name"],
                             "onset_s": e["on"], "amplitude": r(amp, 4),
                             "phase_re_note_on_deg": r(math.degrees(theta) % 360, 0),
                             "phase_re_take_deg": r(math.degrees(big) % 360, 0)})
            summary.append({"sound": lab, "tempo_bpm": bpm, "chorus": ch, "measurement": kind,
                            "rate_hz": r(f, 3), "nearest_note_value": name, "deviation_pct": r(dev, 1),
                            "concentration_re_note_on": r(r_note, 2), "concentration_re_take": r(r_take, 2),
                            "verdict": verdict})
            verdicts.append(f"{kind} {f:.3f} Hz ({name} {dev:+.1f} %): {r_note:.2f} against the note-on, "
                            f"{r_take:.2f} against the take -> {verdict}")
        print(f"  {lab}: " + "; ".join(verdicts))
    write(out / f"{folder}_notes.csv", rows)
    write(out / f"{folder}.csv", summary)
    counts = {}
    for lab in dict.fromkeys(row["sound"] for row in summary):
        vs = {row["verdict"] for row in summary if row["sound"] == lab}
        v = (vs.pop() if len(vs) == 1 else
             "restarts with each note" if "restarts with each note" in vs else
             "free-running" if "free-running" in vs else "unclear")
        counts[v] = counts.get(v, 0) + 1
    print("  per sound: " + ", ".join(f"{v}: {n}" for v, n in sorted(counts.items())))


# ---------------------------------------------------------------- filters
def resonant_peak(tk: A.Take, ref: A.Take, a: float, b: float, f0: float):
    """Gain of each harmonic against the reference take (FILTER 255,
    RESONANCE 0), within 50 dB of the reference's strongest harmonic and below
    12 kHz. The resonant peak is the largest gain, if it stands 6 dB above
    the median gain of the harmonics below it and is not the first or last
    one, and stand 12 dB above the median gain of the harmonics beyond 1.5
    times its frequency (a lowpass resonance attenuates what lies above it;
    a bump with nothing falling off above it is a difference between the
    takes). Its frequency is refined by a parabola through the gains (dB) of
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
    # a lowpass resonance attenuates what lies well above it; a bump with
    # nothing falling off above it is a difference between the takes
    above = valid[(valid + 1) >= 1.5 * (j + 1)]
    if not len(above) or gain - np.median(g[above]) < 12:
        return None, gain
    x = np.log2(f0 * np.array([j, j + 1, j + 2]))
    c2, c1, _ = np.polyfit(x, g[j - 1:j + 2], 2)
    xv = -c1 / (2 * c2) if c2 < 0 else x[1]
    return float(2 ** min(max(xv, x[0]), x[2])), gain


# Below the 6th harmonic the harmonics sample a sharp peak too coarsely
# (errors of 100-500 cents on synthetic data, under 60 above it); near the
# 12 kHz analysis limit the peak's upper side is not seen.
MIN_HARMONIC, MAX_FIT_HZ = 6, 10000


def filters(root: Path, out: Path) -> None:
    """FILTER 17-238 at RESONANCE 255 on four sounds, each note A1 to A4
    measured from 0.8 s after its note-on (past the filter envelope's sweep)
    against the sound's FILTER 255 / RESONANCE 0 reference. Per sound:
    keyboard tracking, the median over FILTER values of the slope of
    log2(peak) against log2(note) among well-resolved peaks (6th harmonic
    or above, below 10 kHz) of notes at least an octave apart; then the
    curve: at each FILTER value, the peak brought to A2 by that tracking
    (median over notes), and the steps per octave between neighbouring
    values. filters.csv keeps every peak; filters_curve.csv the curve."""
    groups: dict[str, dict] = {}
    for tk in takes(root / "filters"):
        prm = tk.meta["prm"]
        g = groups.setdefault(sound_of(tk), {"ref": None, "sweep": []})
        if int(prm["FILTER"]) == 255 and int(prm["RESONANCE"]) == 0:
            g["ref"] = tk
        else:
            g["sweep"].append((int(prm["FILTER"]), tk))
    rows, curve, summary = [], [], []
    for lab, g in groups.items():
        if g["ref"] is None:
            print(f"  {lab}: no reference take (FILTER 255, RESONANCE 0), skipped")
            continue
        good: dict[int, list] = {}
        for v, tk in sorted(g["sweep"], key=lambda x: x[0]):
            for e in sorted(tk.events.values(), key=lambda e: e["on"]):
                f0 = 440 * 2 ** ((e["note"] - 69) / 12)
                a, b = e["on"] + 0.8, e["off"] - 0.05
                pk, gain = resonant_peak(tk, g["ref"], a, b, f0)
                rows.append({"sound": lab, "FILTER": v, "note": e["name"].split("_")[-1], "note_hz": r(f0, 2),
                             "level_dbfs": r(tk.level(a, b)), "peak_hz": r(pk, 0),
                             "peak_harmonic": r(pk / f0, 1) if pk else None, "peak_gain_db": r(gain),
                             "strongest_hz": r(strongest(tk, a, b), 0)})
                if pk and pk / f0 >= MIN_HARMONIC and pk < MAX_FIT_HZ:
                    good.setdefault(v, []).append((f0, pk))
        slopes = []
        for v, pts in good.items():
            if len(pts) >= 2 and max(p[0] for p in pts) / min(p[0] for p in pts) >= 2:
                k, _ = np.polyfit([math.log2(p[0]) for p in pts], [math.log2(p[1]) for p in pts], 1)
                slopes.append(k)
        if not slopes:
            print(f"  {lab}: too few resolved peaks")
            continue
        kt = float(np.median(slopes))
        pts = sorted((v, float(np.median([pk * (110 / f0) ** kt for f0, pk in ps]))) for v, ps in good.items())
        steps, mine = [], [{"sound": lab, "FILTER": pts[0][0], "peak_at_A2_hz": r(pts[0][1], 0)}]
        for (v1, h1), (v2, h2) in zip(pts, pts[1:]):
            spo = (v2 - v1) / math.log2(h2 / h1) if h2 > h1 else None
            if spo:
                steps.append(spo)
            mine.append({"sound": lab, "FILTER": v2, "peak_at_A2_hz": r(h2, 0),
                         "steps_per_octave_from_previous": r(spo, 1)})
        curve += mine
        at1k = None
        for (v1, h1), (v2, h2) in zip(pts, pts[1:]):
            if h1 <= 1000 <= h2 and h2 > h1:
                at1k = v1 + (v2 - v1) * math.log2(1000 / h1) / math.log2(h2 / h1)
        summary.append({"sound": lab, "key_tracking": r(kt, 2), "key_tracking_spread": r(float(np.std(slopes)), 2),
                        "filter_values_for_tracking": len(slopes),
                        "FILTER_range": f"{pts[0][0]}-{pts[-1][0]}",
                        "peak_at_A2_hz_range": f"{pts[0][1]:.0f}-{pts[-1][1]:.0f}",
                        "FILTER_for_1kHz_at_A2": r(at1k, 0), "steps_per_octave_median": r(float(np.median(steps)), 1) if steps else None})
        print(f"  {lab}: keyboard tracking {kt:.2f} (spread {np.std(slopes):.2f}, {len(slopes)} FILTER values); "
              f"peak at A2 {pts[0][1]:.0f} Hz at FILTER {pts[0][0]} to {pts[-1][1]:.0f} Hz at {pts[-1][0]}; "
              f"1 kHz at A2 for FILTER {at1k:.0f}" if at1k is not None else
              f"  {lab}: keyboard tracking {kt:.2f} (spread {np.std(slopes):.2f}, {len(slopes)} FILTER values); "
              f"peak at A2 {pts[0][1]:.0f} Hz at FILTER {pts[0][0]} to {pts[-1][1]:.0f} Hz at {pts[-1][0]}")
        print("     peak at A2 (Hz) by FILTER: " + ", ".join(f"{row['FILTER']}:{row['peak_at_A2_hz']:.0f}" for row in mine))
    write(out / "filters.csv", rows)
    write(out / "filters_curve.csv", curve)
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
        limit = tk.floor_db + 10 if tk.floor_db > -99 else -150   # digital silence: no floor
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


# ---------------------------------------------------------------- longnote
def chorus_lfo_rates(ch: str) -> list[float]:
    """The chorus LFO: half the rate at which its stereo difference pulses."""
    return ([A.CHORUS_MOD[ch] / 2] if ch in A.CHORUS_MOD else
            [v / 2 for v in A.CHORUS_MOD.values()] if ch == "on" else [])


def measured_chorus_lfo(tk: A.Take, start: float, end: float, ch: str) -> list[float]:
    """The chorus LFO's rate measured on the take: the peak of the stereo
    difference/sum ratio's modulation within 0.1 Hz of the nominal rate,
    refined by a parabola, halved (the ratio pulses twice per LFO cycle).
    Falls back to the nominal rates."""
    seg = tk.seg(start, end, "stereo")
    side, mid = (seg[:, 0] - seg[:, 1]) / 2, seg.mean(axis=1)
    if not np.any(side):
        return []
    hop = int(0.01 * tk.sr)
    n = len(mid) // hop
    pm = (mid[:n * hop] ** 2).reshape(n, hop).mean(1)
    ps = (side[:n * hop] ** 2).reshape(n, hop).mean(1)
    ok = pm > 1e-12
    if ok.sum() < 300:
        return chorus_lfo_rates(ch)
    x = A.db(ps[ok]) - A.db(pm[ok])
    x = x - np.polyval(np.polyfit(np.arange(len(x)), x, 2), np.arange(len(x)))
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)), 1 << 17))
    f = np.fft.rfftfreq(1 << 17, 0.01)
    out = []
    names = [ch] if ch in A.CHORUS_MOD else list(A.CHORUS_MOD) if ch == "on" else []
    for name in names:
        sel = np.flatnonzero(np.abs(f - A.CHORUS_MOD[name]) < 0.1)
        i = sel[np.argmax(spec[sel])]
        y0, y1, y2 = np.log(spec[i - 1: i + 2])
        fr = f[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (f[1] - f[0])
        out.append(float(fr) / 2)
    return out


def describe_rate(f: float, bpm: float, chorus_lfo) -> tuple[str, float, str]:
    """Nearest note value, and the chorus LFO harmonic it falls on, if any
    (within 0.015 Hz plus 0.002 Hz per harmonic, the measured rate's
    uncertainty times the harmonic number)."""
    name, dev = nearest_value(f, bpm)
    harm = [f"{n} x {c:.4f}" for c in chorus_lfo for n in range(1, 25) if abs(f - n * c) < 0.015 + 0.002 * n]
    return name, dev, (harm[0] if harm else "")


def mod_series(tk: A.Take, end: float):
    """Pitch, brightness and even-share series of the long note, each as
    (left, right, mean), cleaned; None where a channel is silent."""
    tr = A.track(tk, 0.1, end, A.A2)
    out = {}
    for col, kind in ((0, "vibrato"), (1, "filter LFO"), (2, "PWM")):
        left, right = A._clean(tr[:, 0, col]), A._clean(tr[:, 1, col])
        out[kind] = None if left is None or right is None else (left, right, (left + right) / 2)
    return out


def band_rms(x, lo, hi, hop=0.01) -> float:
    """RMS of x within lo-hi Hz (Parseval on the windowless spectrum)."""
    spec = np.fft.rfft(x - np.mean(x))
    f = np.fft.rfftfreq(len(x), hop)
    sel = (f >= lo) & (f < hi)
    return float(np.sqrt(2 * np.sum(np.abs(spec[sel]) ** 2)) / len(x))


def peak_height(series, f, hop=0.01):
    """Height of the spectral peak within 0.03 Hz of f against the median
    0.15-18 Hz, and its rate."""
    spec = np.abs(np.fft.rfft(series * np.hanning(len(series)), 1 << 16))
    fr = np.fft.rfftfreq(1 << 16, hop)
    base = max(np.median(spec[(fr > 0.15) & (fr < 18)]), 1e-12)
    sel = np.flatnonzero(np.abs(fr - f) <= 0.03)
    i = sel[np.argmax(spec[sel])]
    return float(spec[i] / base), float(fr[i])


def audio_components(tk: A.Take, start: float, end: float, f0: float):
    """Components of the sound below its fundamental, 15 Hz to 0.95 f0,
    within 10 dB of its strongest component and more than 0.5 Hz from a
    sub-oscillator (f0 / 2, f0 / 4 and their multiples): an audio-rate
    modulation, as on a ring-modulated sound. Vibrato sidebands stay far
    below 10 dB. Frequencies refined by a parabola."""
    from scipy.signal import find_peaks
    f, m = A.spectrum(tk.seg(start, min(end, start + 40)), tk.sr, 1 << 21)
    sel = (f > 15) & (f < 4000)
    f, m = f[sel], m[sel]
    db = 20 * np.log10(m / m.max() + 1e-12)
    pk, _ = find_peaks(db, height=-10, distance=max(int(1.0 / (f[1] - f[0])), 1))
    out = []
    for i in pk:
        if f[i] < 0.95 * f0 and abs(f[i] - f0 / 4 * round(f[i] / (f0 / 4))) > 0.5:
            y0, y1, y2 = np.log(m[i - 1: i + 2])
            out.append((float(f[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (f[1] - f[0])), float(db[i])))
    return out


def longnote(root: Path, out: Path, folder: str = "longnote") -> list[dict]:
    """One long A2 note per take (20 s; 90 s in verylong). On the pitch,
    brightness and even-harmonic tracks, every spectral peak from five
    cycles per note (0.25 Hz on 20 s, 0.056 Hz on 90 s) to 18 Hz that
    stands 8 times above the
    median and moves both channels in phase, with its swing (a weaker one
    only above a tenth of the strongest and 0.25 Hz from it, clear of the
    window's sidelobes); each is named by its nearest note value at the
    take's tempo and checked against the harmonics of the chorus LFO,
    measured on the same note (within 0.015 Hz plus 0.002 Hz per harmonic:
    the chorus, not an LFO). The 20 s note resolves about 0.05 Hz, so the
    band excluded around the chorus lines shrinks to 0.1 Hz. Stepped
    (sample-and-hold) brightness is checked when nothing periodic is found,
    and audio-rate components below the note are listed (for those, the
    prominence column holds their level in dB against the strongest
    component).
    For a sound recorded at two tempos (same FILTER and RESONANCE), each
    modulation found at one tempo
    is looked for in the other take at the rate scaled by the tempo ratio
    and at the same rate: the taller peak (8 times the median at least, and
    twice the other) says whether it follows the tempo or is fixed; a
    candidate rate on a harmonic of that take's chorus LFO counts for
    nothing (the peak found within 0.02 Hz of one).

    Each take also gets its brightness jitter, 0.5-5 and 5-45 Hz, split
    into what moves both channels together (a modulation of the sound) and
    what differs between them (the chorus acting on noise, estimation
    noise): comparing takes of one sound at different FILTER settings tells
    a filter movement, which vanishes with the filter open, from the noise
    of the source, which stays (written to FOLDER_jitter.csv)."""
    rows, takes_by, jit = [], {}, []
    for tk in takes(root / folder):
        lab = sound_of(tk)
        bpm = float(tk.meta["prm"].get("TEMPO", 10000)) / 100
        knobs = (int(tk.meta["prm"].get("FILTER", -1)), int(tk.meta["prm"].get("RESONANCE", -1)))
        tag = f"{lab} at {bpm:g} BPM, FILTER {knobs[0]} RESONANCE {knobs[1]}"
        e = tk.events["long_A2"]
        end = min(A.audible_until(tk, e["off"]), e["off"] - 0.05)
        if end < 4:
            print(f"  {tag}: the note lasts {end:.1f} s, too short")
            continue
        ch = A.chorus(tk, 0.3, end).get("chorus", "on")
        clfo = measured_chorus_lfo(tk, 0.3, end, ch)
        series = mod_series(tk, end)
        takes_by[(lab, bpm, knobs)] = (tk, end, series, clfo)
        fmin = max(0.05, 5 / end)
        if series["filter LFO"] is not None:
            left, right, _ = series["filter LFO"]
            row = {"sound": lab, "tempo_bpm": bpm, "FILTER": knobs[0], "RESONANCE": knobs[1]}
            for lo, hi in ((0.5, 5), (5, 45)):
                c, d = band_rms((left + right) / 2, lo, hi), band_rms((left - right) / 2, lo, hi)
                row[f"together_{lo:g}_{hi:g}_oct"], row[f"apart_{lo:g}_{hi:g}_oct"] = r(c, 4), r(d, 4)
            jit.append(row)
        found = []
        for kind, least in (("vibrato", 6.0), ("filter LFO", 0.1), ("PWM", 0.05)):
            if series[kind] is None:
                continue
            left, right, mean = series[kind]
            spec = np.abs(np.fft.rfft(mean * np.hanning(len(mean)), 1 << 16))
            f = np.fft.rfftfreq(1 << 16, 0.01)
            sel = np.flatnonzero((f > fmin) & (f < 18))   # 5 cycles per note at least
            base = max(np.median(spec[sel]), 1e-12)
            peaks = [i for i in sel[1:-1] if spec[i] >= spec[i - 1] and spec[i] >= spec[i + 1] and spec[i] / base >= 8]
            peaks = sorted(peaks, key=lambda i: -spec[i])
            kept = []
            for i in peaks:
                # the window's sidelobes stand 31 dB below a peak and 0.1-0.2 Hz from it
                if any(abs(f[i] - f[j]) < 0.25 for j in kept) or (kept and spec[i] < 0.1 * spec[kept[0]]):
                    continue
                bl, br = A.band(left, f[i]), A.band(right, f[i])
                if np.std(bl) == 0 or np.std(br) == 0 or np.corrcoef(bl, br)[0, 1] <= 0.5:
                    continue
                bm = A.band(mean, f[i])
                swing = float(np.percentile(bm, 95) - np.percentile(bm, 5))
                if swing <= least:
                    continue
                kept.append(i)
                y0, y1, y2 = np.log(spec[i - 1: i + 2])
                fr = f[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * (f[1] - f[0])
                found.append((kind, fr, spec[i] / base, swing))
                if len(kept) == 3:
                    break
        if not any(not describe_rate(fr, bpm, clfo)[2] for _, fr, _, _ in found):
            t, d = jumps(tk, 0.2, end)
            if d is not None:
                # threshold set above the 7-10.5 that chorus leakage and a slow
                # filter LFO reach on the closing pass's sounds, none of which
                # has a sample and hold
                rate, prom = averaged_peak_rate([d], [n * c for c in clfo for n in range(1, 25)], fmax=9.5, guard=0.05)
                if prom >= 12 and A.note_value(rate, bpm):
                    found.append(("stepped brightness", rate, prom, None))
        for fr, level in audio_components(tk, 2.0, end, A.A2):
            found.append(("audio-rate component", fr, level, None))
        if not found:
            rows.append({"sound": lab, "tempo_bpm": bpm, "FILTER": knobs[0], "RESONANCE": knobs[1],
                         "chorus": ch, "measurement": None})
            print(f"  {tag} (chorus {ch}): no modulation")
            continue
        parts = []
        for kind, fr, prom, swing in found:
            name, dev, harm = describe_rate(fr, bpm, clfo)
            if kind == "audio-rate component":
                harm = ""
            rows.append({"sound": lab, "tempo_bpm": bpm, "FILTER": knobs[0], "RESONANCE": knobs[1], "chorus": ch,
                         "chorus_lfo_hz": "/".join(f"{c:.4f}" for c in clfo), "measurement": kind,
                         "rate_hz": r(fr, 3), "prominence": r(prom, 1), "swing": r(swing, 3),
                         "nearest_note_value": name, "deviation_pct": r(dev, 1), "chorus_harmonic": harm})
            parts.append(f"{kind} {fr:.3f} Hz ({name} {dev:+.1f} %{', chorus ' + harm if harm else ''})")
        print(f"  {tag} (chorus {ch}, LFO {'/'.join(f'{c:.3f}' for c in clfo)} Hz): " + "; ".join(parts))
    # each modulation looked for at the other tempo
    for row in rows:
        if not row.get("rate_hz") or row["chorus_harmonic"] or row["measurement"] in ("stepped brightness",):
            continue
        lab, bpm, knobs = row["sound"], row["tempo_bpm"], (row["FILTER"], row["RESONANCE"])
        for (lab2, bpm2, knobs2), (tk2, end2, series2, clfo2) in takes_by.items():
            if lab2 != lab or bpm2 == bpm or knobs2 != knobs:
                continue
            synced, fixed = row["rate_hz"] * bpm2 / bpm, row["rate_hz"]
            if row["measurement"] == "audio-rate component":
                comps = audio_components(tk2, 2.0, end2, A.A2)
                hs = [any(abs(c - g) < 0.1 for c, _ in comps) for g in (synced, fixed)]
                verdict = ("follows the tempo" if hs[0] and not hs[1] else "fixed rate" if hs[1] and not hs[0]
                           else "unclear")
                detail = f"component at {synced:.3f} Hz: {'yes' if hs[0] else 'no'}, at {fixed:.3f} Hz: {'yes' if hs[1] else 'no'}"
            else:
                if series2.get(row["measurement"]) is None:
                    continue
                m2 = series2[row["measurement"]][2]
                (h_s, f_s), (h_f, f_f) = peak_height(m2, synced), peak_height(m2, fixed)
                # a peak found on a harmonic of the other take's chorus LFO is the chorus
                on_chorus = [any(abs(g - n * c) < 0.02 for c in clfo2 for n in range(1, 25)) for g in (f_s, f_f)]
                h_s, h_f = (0.0 if on_chorus[0] else h_s), (0.0 if on_chorus[1] else h_f)
                verdict = ("follows the tempo" if h_s >= 8 and h_s >= 2 * h_f else
                           "fixed rate" if h_f >= 8 and h_f >= 2 * h_s else "unclear")
                detail = (f"peak {h_s:.0f} at {f_s:.3f} Hz (tempo-scaled{', on a chorus harmonic' if on_chorus[0] else ''}), "
                          f"{h_f:.0f} at {f_f:.3f} Hz (unchanged{', on a chorus harmonic' if on_chorus[1] else ''})")
            row[f"at_{bpm2:g}_bpm"] = verdict
            print(f"  {lab} {row['measurement']} {row['rate_hz']:.3f} Hz at {bpm:g} BPM, looked for at {bpm2:g} BPM: "
                  f"{detail} -> {verdict}")
    for row in jit:
        print(f"  {row['sound']} at {row['tempo_bpm']:g} BPM, FILTER {row['FILTER']} RESONANCE {row['RESONANCE']}: "
              f"brightness jitter 0.5-5 Hz {row['together_0.5_5_oct']:.3f} together / {row['apart_0.5_5_oct']:.3f} apart, "
              f"5-45 Hz {row['together_5_45_oct']:.3f} / {row['apart_5_45_oct']:.3f} octave rms")
    write(out / f"{folder}.csv", rows)
    write(out / f"{folder}_jitter.csv", jit)
    return rows


# ---------------------------------------------------------------- chord
def which_reset(out: Path, lab: str, kind: str, f: float, notes, phases):
    """For a shared vibrato on a sound whose LFO restarts with each note
    (keysync), the note-on that restarted it: the single notes give the
    phase the LFO has against its note-on, which predicts the chord's phase
    if note k restarted it. Frames: keysync phases refer to frame centres,
    chord frames start 0.05 s before theirs."""
    ks = out / "keysync_notes.csv"
    if kind != "pitch" or not ks.exists():
        return None
    th = [math.radians(float(row["phase_re_note_on_deg"])) for row in csv.DictReader(open(ks))
          if row["sound"] == lab and row["measurement"] == "vibrato" and abs(float(row["rate_hz"]) - f) < 0.02]
    if len(th) < 3 or concentration(th) < 0.8:
        return None    # not a restarting LFO, or no single-note data
    mean = float(np.angle(np.mean(np.exp(1j * np.array(th)))))
    shared = float(np.angle(np.mean(np.exp(1j * np.array(phases)))))
    dist = []
    for e in notes:
        pred = mean + 2 * np.pi * f * (e["on"] - 0.05)
        dist.append(abs((math.degrees(shared - pred) + 180) % 360 - 180))
    k = int(np.argmin(dist))
    return (f"the phase is the one note {k + 1} (onset {notes[k]['on']} s) gives on its own, within {dist[k]:.0f} deg "
            f"(others {', '.join(f'{d:.0f}' for i, d in enumerate(dist) if i != k)} deg)")


def chord(root: Path, out: Path) -> None:
    """Four notes (A2, D3, F#3, B3) entering at 0, 0.25, 0.51 and 1.05 s and
    held together. Each note's level is read on its own fundamental and 2nd
    harmonic (no two of the eight coincide), every 10 ms over 100 ms frames,
    from 1 s after the last note entered; a filter LFO or PWM moves those
    levels, a vibrato their frequency (read as the peak's position). The
    common rate is the strongest periodicity of the four series together.
    If the voices share one LFO, the four phases agree against the clock; if
    each voice's LFO starts at its note-on, they agree against each note's
    onset. The onsets are spread so that the two predictions differ
    (concentration at most 0.46 for note values above 1 Hz at 100 BPM). The
    chorus acts on the mix and is common to all voices: a rate that is no
    note value and lies within the window's resolution (1 / 6.9 s) of one of
    its harmonics is inconclusive."""
    rows, summary = [], []
    for tk in takes(root / "chord"):
        lab = sound_of(tk)
        bpm = float(tk.meta["prm"].get("TEMPO", 10000)) / 100
        notes = sorted(tk.events.values(), key=lambda e: e["on"])
        a = notes[-1]["on"] + 1.0
        b = min(e["off"] for e in notes) - 0.1
        n, hop = int(0.1 * tk.sr), 0.01
        ts = np.arange(a, b, hop)
        nfft = 1 << 15
        freqs = np.fft.rfftfreq(nfft, 1 / tk.sr)
        w = np.hanning(n)
        f0s = [440 * 2 ** ((e["note"] - 69) / 12) for e in notes]
        lv = np.zeros((len(ts), len(notes)))
        fq = np.zeros((len(ts), len(notes)))
        for i, t in enumerate(ts):
            seg = tk.seg(t, t + 0.1)
            if len(seg) < n:
                lv[i] = fq[i] = np.nan
                continue
            mag = np.abs(np.fft.rfft(seg[:n] * w, nfft))
            for k, f0 in enumerate(f0s):
                tot, pos = 0.0, 0.0
                for h in (1, 2):
                    sel = np.flatnonzero(np.abs(freqs - h * f0) < 0.02 * h * f0)
                    j = sel[np.argmax(mag[sel])]
                    tot += mag[j] ** 2
                    y0, y1, y2 = np.log(mag[j - 1: j + 2] + 1e-12)
                    dj = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if y0 - 2 * y1 + y2 < 0 else 0.0
                    pos += (freqs[j] + dj * (freqs[1] - freqs[0])) / h / 2
                lv[i, k] = 10 * math.log10(tot + 1e-24)
                fq[i, k] = 1200 * math.log2(pos / f0)
        ch, _ = chorus_exclusion(root, tk, notes)
        # the chorus acts on the mix, so its sweep is common to all voices:
        # every harmonic of its LFO, measured on the chord, is left out
        clfo = measured_chorus_lfo(tk, a, b, ch)
        exclude = [n * c for c in clfo for n in range(1, 25)]
        best = None
        for kind, data in (("level", lv), ("pitch", fq)):
            series = [A._clean(data[:, k]) for k in range(len(notes))]
            if any(sv is None for sv in series):
                continue
            rate, prom = averaged_peak_rate(series, exclude, fmin=0.5, fmax=15, guard=0.05)
            if best is None or prom > best[2]:
                best = (kind, rate, prom, series)
        if best is None or best[2] < 4:
            print(f"  {lab}: no common modulation")
            summary.append({"sound": lab, "verdict": "no common modulation"})
            continue
        kind, rate, prom, series = best
        # all four notes are fitted over the same window, so a small rate
        # error shifts their phases alike; a rate within 1 % of a note value
        # is taken as that value
        f, nv = rate, A.note_value(rate, bpm)
        if nv:
            exact = bpm / 60 / dict((nm, bt) for bt, nm in A.NOTE_VALUES)[nv]
            if abs(rate / exact - 1) < 0.01:
                f = exact
        big, rel = [], []
        for e, sv in zip(notes, series):
            amp, theta = phase_fit(ts, sv, f)
            big.append(theta)
            rel.append(theta - 2 * np.pi * f * e["on"])
            rows.append({"sound": lab, "note": e["name"], "onset_s": e["on"], "measurement": kind,
                         "rate_hz": r(f, 3), "amplitude": r(amp, 4),
                         "phase_re_clock_deg": r(math.degrees(theta) % 360, 0),
                         "phase_re_note_on_deg": r(math.degrees(rel[-1]) % 360, 0)})
        r_clock, r_note = concentration(big), concentration(rel)
        # a rate on a note value is the tempo-synced LFO; another one within
        # the resolution of a chorus harmonic may be the chorus
        near = [] if f != rate else [f"{n} x {c:.3f}" for c in clfo for n in range(1, 25) if abs(f - n * c) < 1 / (b - a)]
        if near:
            verdict = f"inconclusive: chorus harmonic {near[0]} Hz within the resolution"
        elif r_clock >= 0.9 and r_clock - r_note >= 0.3:
            verdict = "voices share one LFO phase"
        elif r_note >= 0.9 and r_note - r_clock >= 0.3:
            verdict = "each voice's LFO starts at its note-on"
        else:
            verdict = "unclear"
        reset = which_reset(out, lab, kind, f, notes, big) if verdict == "voices share one LFO phase" else None
        if reset:
            verdict += f"; {reset}"
        summary.append({"sound": lab, "measurement": kind, "rate_hz": r(f, 3), "prominence": r(prom, 1),
                        "concentration_re_clock": r(r_clock, 2), "concentration_re_note_on": r(r_note, 2),
                        "verdict": verdict})
        print(f"  {lab}: {kind} at {f:.3f} Hz: phases agree {r_clock:.2f} against the clock, "
              f"{r_note:.2f} against each note-on -> {verdict}")
    write(out / "chord_notes.csv", rows)
    write(out / "chord.csv", summary)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captures", help="folder holding default/ and the experiment folders")
    ap.add_argument("-o", "--output", default="results", help="folder for the CSV files (default results)")
    args = ap.parse_args()
    root, out = Path(args.captures), Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    found = False
    known = []   # the long notes' modulations, for keysync2

    def run_longnote(a, b):
        known.extend(longnote(a, b))

    for name, fn in (("tempo150", tempo), ("velocity", velocity), ("poly", poly), ("sweep", sweep),
                     ("keysync", keysync), ("filters", filters), ("longtail", longtail),
                     ("longnote", run_longnote), ("keysync2", lambda a, b: keysync(a, b, "keysync2", known)),
                     ("chord", chord), ("verylong", lambda a, b: longnote(a, b, "verylong")),
                     ("longnote2", lambda a, b: longnote(a, b, "longnote2"))):
        if (root / name).is_dir():
            found = True
            print(f"== {name}")
            fn(root, out)
    if not found:
        sys.exit(f"no experiment folder (tempo150, velocity, poly, sweep, keysync, filters, "
                 f"longtail, longnote, keysync2, chord, verylong, longnote2) in {root}")


if __name__ == "__main__":
    main()
