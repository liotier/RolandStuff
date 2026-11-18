#!/usr/bin/env python3
"""Measure the J-6's sounds from the takes recorded by j6capture.py.

WORK IN PROGRESS, not validated. Known problems: the oscillator-frequency
estimate (dco_frequency) counts harmonics twice and reports octave -1, which
also corrupts the harmonic profile, noise share and pitch tracking; the
modulation tracks mistake the chorus's comb sweeps for LFO; the chorus
classifier is confused by an LFO. Envelope, release, velocity and chorus-off
measurements agree with the reference spreadsheet so far.

  python3 j6analyze.py CAPTURES_DIR -o measurements.csv [--sounds 1-1,4-4]

CAPTURES_DIR holds one folder per pass (default, open, env000, env255). Each
take is aligned on its own audio: the first note's onset is found by fitting
the stimulus's note pattern to the take's onset curve, because the recorder's
start-up time varies by tens of milliseconds.

Needs numpy, scipy and soundfile (Debian: python3-numpy python3-scipy
python3-soundfile).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

EPS = 1e-24
NOTE_A2 = 110.0
CHORUS_RATES = {"I": 1.09, "II": 1.76}   # side/mid modulation measured on chorus I and II sounds


def label(i: int) -> str:
    return f"{i // 8 + 1}-{i % 8 + 1}"


def db(p):
    return 10 * np.log10(np.asarray(p) + EPS)


class Take:
    def __init__(self, json_path: Path):
        self.meta = json.loads(json_path.read_text())
        audio = json_path.with_suffix(".flac")
        if not audio.exists():
            audio = json_path.with_suffix(".wav")
        self.x, self.sr = sf.read(audio, always_2d=True)
        self.events = {e["name"]: e for e in self.meta["events"]}
        self.hop = int(0.005 * self.sr)
        p = (self.x ** 2).mean(axis=1)
        n = len(p) // self.hop
        self.pow = p[: n * self.hop].reshape(n, self.hop).mean(axis=1)   # 5 ms power frames
        self.t0, self.floor_db, self.onset_method = self._onset()

    def _onset(self):
        sr, hop = self.sr, self.hop
        pre = self.meta["recording"]["midi_started_after_arecord_start_s"]
        lvl = np.maximum(db(self.pow), -100.0)
        floor = float(np.percentile(lvl[int(0.05 * sr / hop): int((pre - 0.1) * sr / hop)], 95))
        rise = np.zeros_like(lvl)
        rise[2:] = np.maximum(lvl[2:] - lvl[:-2], 0)                     # rise over 10 ms
        ons = [e["on"] for e in self.meta["events"]]
        best, best_tau = -1.0, None
        for tau in np.arange(pre - 0.25, pre + 0.4, 0.002):
            s = 0.0
            for on in ons:
                a = int((tau + on - 0.004) * sr / hop)
                b = int((tau + on + 0.012) * sr / hop)
                if 0 <= a < b <= len(rise):
                    s += rise[a:b].max()
            if s > best:
                best, best_tau = s, tau
        # Digital silence before the note: the first non-zero sample is exact.
        if floor <= -99:
            nz = np.flatnonzero(np.abs(self.x).max(axis=1) > 3e-5)
            if len(nz) and abs(nz[0] / sr - best_tau) < 0.03:
                return nz[0] / sr, floor, "first-sample"
        return best_tau, floor, "pattern-fit"

    def seg(self, start: float, end: float, channels: str = "mono"):
        a = max(0, int((self.t0 + start) * self.sr))
        b = min(len(self.x), int((self.t0 + end) * self.sr))
        s = self.x[a:b]
        return s.mean(axis=1) if channels == "mono" else s

    def level(self, start: float, end: float) -> float:
        a, b = int((self.t0 + start) * self.sr / self.hop), int((self.t0 + end) * self.sr / self.hop)
        return float(db(self.pow[max(a, 0):max(b, a + 1)].mean())) if b > a else -240.0

    def curve(self, start: float, end: float):
        a, b = int((self.t0 + start) * self.sr / self.hop), int((self.t0 + end) * self.sr / self.hop)
        a = max(a, 0)
        t = start + (np.arange(a, b) - int((self.t0 + start) * self.sr / self.hop)) * self.hop / self.sr
        return t, db(self.pow[a:b])


def spectrum(sig, sr, nfft=1 << 17):
    if len(sig) < 256:
        return None, None
    w = np.hanning(len(sig))
    mag = np.abs(np.fft.rfft(sig * w, nfft)) / (w.sum() / 2)
    return np.fft.rfftfreq(nfft, 1 / sr), mag


def amp_at(freqs, mag, f, rel=0.015):
    sel = (freqs > f * (1 - rel)) & (freqs < f * (1 + rel))
    return float(mag[sel].max()) if sel.any() else 0.0


def dco_frequency(freqs, mag):
    """Largest of A1, A2, A3, A4 whose harmonic grid holds at least half of the
    spectral peak energy: the oscillator frequency, not the sub-oscillator's."""
    total = sum(amp_at(freqs, mag, 27.5 * k) ** 2 for k in range(1, 400) if 27.5 * k < 12000)
    best = None
    for f in (55.0, 110.0, 220.0, 440.0):
        e = sum(amp_at(freqs, mag, f * k) ** 2 for k in range(1, 200) if f * k < 12000)
        if total > 0 and e >= 0.5 * total:
            best = f
    return best


def centroid(sig, sr):
    freqs, mag = spectrum(sig, sr, 1 << 14)
    if freqs is None:
        return float("nan")
    sel = (freqs > 20) & (freqs < 16000)
    p = mag[sel] ** 2
    return float((freqs[sel] * p).sum() / p.sum()) if p.sum() > 0 else float("nan")


def track(take: Take, start: float, end: float, f_ref: float, frame=0.08, hop=0.01):
    """Per-frame pitch (cents re f_ref), brightness (log2 centroid) and
    2nd/1st harmonic ratio (dB), on the left channel."""
    sr = take.sr
    sig = take.seg(start, end, "stereo")
    if len(sig) < int(frame * sr) * 4:
        return None
    sig = sig[:, 0]
    n, h = int(frame * sr), int(hop * sr)
    nfft = 1 << 15
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    cents_grid = np.arange(-150, 151, 2.0)
    out = []
    w = np.hanning(n)
    for i in range(0, len(sig) - n, h):
        fr = sig[i:i + n]
        if np.sqrt(np.mean(fr ** 2)) < 1e-5:
            out.append((np.nan, np.nan, np.nan))
            continue
        mag = np.abs(np.fft.rfft(fr * w, nfft))
        score = np.zeros_like(cents_grid)
        for k in range(1, 5):
            fk = f_ref * k * 2 ** (cents_grid / 1200)
            score += np.interp(fk, freqs, mag)
        c = cents_grid[int(np.argmax(score))]
        f1 = f_ref * 2 ** (c / 1200)
        p = mag ** 2
        sel = (freqs > 20) & (freqs < 16000)
        cen = (freqs[sel] * p[sel]).sum() / max(p[sel].sum(), EPS)
        h1, h2 = np.interp(f1, freqs, mag), np.interp(2 * f1, freqs, mag)
        out.append((c, math.log2(max(cen, 1e-9)), 20 * math.log10((h2 + 1e-12) / (h1 + 1e-12))))
    return np.array(out)


def modulation(series, hop=0.01, fmin=0.15, fmax=15.0):
    """Dominant modulation frequency and p95-p5 swing of a detrended series."""
    s = np.asarray(series, float)
    s = s[~np.isnan(s)]
    if len(s) < 100:
        return float("nan"), float("nan")
    x = np.arange(len(s))
    s = s - np.polyval(np.polyfit(x, s, 2), x)
    nfft = 1 << 15
    spec = np.abs(np.fft.rfft(s * np.hanning(len(s)), nfft))
    f = np.fft.rfftfreq(nfft, hop)
    sel = (f > fmin) & (f < fmax)
    return float(f[sel][np.argmax(spec[sel])]), float(np.percentile(s, 95) - np.percentile(s, 5))


def modulation_delay(series, rate, hop=0.01):
    """Time at which the modulation's running swing reaches half its final value."""
    s = np.asarray(series, float)
    if not rate or rate != rate or len(s) < 200:
        return float("nan")
    win = max(int(1.5 / rate / hop), 10)
    sw = np.array([np.nanpercentile(s[i:i + win], 95) - np.nanpercentile(s[i:i + win], 5)
                   if np.sum(~np.isnan(s[i:i + win])) > win // 2 else np.nan
                   for i in range(0, len(s) - win)])
    if np.all(np.isnan(sw)):
        return float("nan")
    final = np.nanmedian(sw[-max(len(sw) // 4, 1):])
    idx = np.flatnonzero(sw >= 0.5 * final)
    return float(idx[0] * hop + win * hop / 2) if len(idx) else float("nan")


def envelope(take: Take, gate: float, tail: float):
    """Amplitude envelope of the long note: attack, decay, sustain, release."""
    t, lv = take.curve(0, gate + tail)
    gate_sel = t < gate
    peak = float(lv[gate_sel].max())
    ipk = int(np.argmax(lv[gate_sel]))
    out = {"peak_dbfs": round(peak, 1), "floor_dbfs": round(take.floor_db, 1)}
    above = np.flatnonzero(lv[gate_sel] >= peak - 1)
    out["attack_ms"] = round(1000 * t[above[0]], 1)
    sus = take.level(gate - 0.5, gate - 0.05) - peak
    out["sustain_db"] = round(sus, 1) if sus > -60 else None
    after = lv[ipk:np.flatnonzero(gate_sel)[-1] + 1]
    ta = t[ipk:np.flatnonzero(gate_sel)[-1] + 1]
    if sus > -60 and sus < -3:
        hit = np.flatnonzero(after <= peak + sus + 3)
        out["decay_ms"] = round(1000 * (ta[hit[0]] - t[ipk]), 0) if len(hit) else None
    else:
        out["decay_ms"] = None
    for drop in (20, 40):
        hit = np.flatnonzero(after <= peak - drop)
        out[f"decay_to_-{drop}dB_ms"] = round(1000 * (ta[hit[0]] - t[ipk]), 0) if len(hit) else None
    # release after the note-off, measured only down to the contamination floor + 10 dB
    off_level = take.level(gate - 0.08, gate - 0.01)
    rel_sel = t >= gate
    tr, lr = t[rel_sel] - gate, lv[rel_sel]
    limit = take.floor_db + 10 if take.floor_db > -99 else -100
    for drop in (20, 40):
        target = off_level - drop
        hit = np.flatnonzero(lr <= target)
        ok = off_level > -90 and target > limit
        out[f"release_-{drop}dB_ms"] = round(1000 * tr[hit[0]], 0) if (ok and len(hit)) else None
    return out


def glide_time(take: Take, f_from: float, f_to: float):
    """Time for the dominant partial to pass halfway (in cents) from f_from to f_to."""
    ev = take.events["glide_to_E3"]
    sig = take.seg(ev["on"], ev["on"] + 0.6)
    sr = take.sr
    n, h = int(0.04 * sr), int(0.002 * sr)
    freqs = np.fft.rfftfreq(1 << 15, 1 / sr)
    band = (freqs > f_from * 0.97) & (freqs < f_to * 1.03)
    mid = math.sqrt(f_from * f_to)
    w = np.hanning(n)
    for i in range(0, len(sig) - n, h):
        mag = np.abs(np.fft.rfft(sig[i:i + n] * w, 1 << 15))
        f = freqs[band][np.argmax(mag[band])]
        if f >= mid:
            return round(1000 * (i + n / 2) / sr, 0)
    return None


def chorus(take: Take, start: float, end: float):
    seg = take.seg(start, end, "stereo")
    if len(seg) < take.sr:
        return {}
    side = (seg[:, 0] - seg[:, 1]) / 2
    mid = seg.mean(axis=1)
    if np.max(np.abs(side)) == 0:
        return {"chorus": "Off", "chorus_lr_corr": 1.0}
    corr = float(np.corrcoef(seg[:, 0], seg[:, 1])[0, 1])
    hop = int(0.01 * take.sr)
    n = len(mid) // hop
    pm = (mid[:n * hop] ** 2).reshape(n, hop).mean(1)
    ps = (side[:n * hop] ** 2).reshape(n, hop).mean(1)
    ok = pm > 1e-12
    out = {"chorus_lr_corr": round(corr, 3)}
    if ok.sum() > 150:
        rate, swing = modulation(db(ps[ok]) - db(pm[ok]), fmin=0.3, fmax=6)
        out["chorus_mod_hz"] = round(rate, 2)
        name = min(CHORUS_RATES, key=lambda k: abs(CHORUS_RATES[k] - rate))
        out["chorus"] = name if abs(CHORUS_RATES[name] - rate) < 0.2 else "?"
    else:
        out["chorus"] = "on"
    return out


def audible_until(take: Take, gate: float, below=40):
    """Seconds after onset until the long note falls `below` dB under its peak."""
    t, lv = take.curve(0, gate)
    peak = lv.max()
    floor = max(peak - below, take.floor_db + 10)
    low = np.flatnonzero((lv < floor) & (t > t[np.argmax(lv)]))
    return float(t[low[0]]) if len(low) else gate


def analyse_sound(takes: dict, idx: int) -> dict:
    row = {"sound": label(idx)}
    d, o = takes.get("default"), takes.get("open")
    if d:
        row["onset_method"] = d.onset_method
        prm = d.meta.get("prm", {})
        row.update({"FILTER": prm.get("FILTER"), "RESONANCE": prm.get("RESONANCE"),
                    "ATTACK": prm.get("ATTACK")})
        row.update({f"default_{k}": v for k, v in envelope(d, 6.0, 3.0).items()})
        st = d.events["staccato_A2"]
        st_level = d.level(st["on"], st["on"] + 0.15)
        row["staccato_peak_rel_db"] = round(st_level - row["default_peak_dbfs"], 1)
        t, lv = d.curve(st["off"], st["off"] + 2.3)
        hit = np.flatnonzero(lv <= d.level(st["off"] - 0.03, st["off"]) - 20)
        row["staccato_release_-20dB_ms"] = round(1000 * t[hit[0]] - 1000 * st["off"], 0) if len(hit) else None
        # velocity: level and brightness, A3 at 40 and 127
        v40, v127 = d.events["velocity_40"], d.events["velocity_127"]
        row["velocity_40_to_127_db"] = round(d.level(v127["on"], v127["on"] + 0.5)
                                             - d.level(v40["on"], v40["on"] + 0.5), 1)
        c40 = centroid(d.seg(v40["on"] + 0.02, v40["on"] + 0.5), d.sr)
        c127 = centroid(d.seg(v127["on"] + 0.02, v127["on"] + 0.5), d.sr)
        row["velocity_brightness_oct"] = round(math.log2(c127 / c40), 2) if c40 == c40 and c127 == c127 else None
        # filter envelope: brightness early vs later in the long note
        until = audible_until(d, 6.0)
        late_a = min(1.0, max(until - 0.3, 0.1))
        ce = centroid(d.seg(0.02, 0.08), d.sr)
        cl = centroid(d.seg(late_a, late_a + 0.2), d.sr)
        row["filter_env_oct"] = round(math.log2(ce / cl), 2) if ce == ce and cl == cl and cl > 0 else None
        # keyboard tracking: brightness relative to pitch, A2 versus A4, same envelope phase
        a4 = d.events["key_A4"]
        c2 = centroid(d.seg(0.15, 0.45), d.sr)
        c4 = centroid(d.seg(a4["on"] + 0.15, a4["on"] + 0.45), d.sr)
        row["key_tracking"] = round(1 + math.log2((c4 / 4) / c2) / 2, 2) if c2 == c2 and c4 == c4 and c2 > 0 else None
        row["glide_halfway_ms"] = glide_time(d, NOTE_A2, NOTE_A2 * 2 ** (7 / 12))
    if o:
        freqs, mag = spectrum(o.seg(0.15, 0.65), o.sr)
        if freqs is not None and mag.max() > 0:
            f = dco_frequency(freqs, mag)
            if f:
                row["octave"] = int(round(math.log2(f / NOTE_A2)))
                a1 = amp_at(freqs, mag, f)
                row["sub_db"] = round(20 * math.log10((amp_at(freqs, mag, f / 2) + 1e-12) / (a1 + 1e-12)), 1)
                hs = [amp_at(freqs, mag, f * k) for k in range(1, 11)]
                for k in range(2, 11):
                    row[f"h{k}_db"] = round(20 * math.log10((hs[k - 1] + 1e-12) / (a1 + 1e-12)), 1)
                even = sum(h ** 2 for h in hs[1::2])
                odd = sum(h ** 2 for h in hs[0::2])
                row["even_odd_db"] = round(10 * math.log10((even + 1e-20) / (odd + 1e-20)), 1)
                # inharmonic (noise) share: energy away from the f/2 grid, 100 Hz - 10 kHz
                sel = (freqs > 100) & (freqs < 10000)
                grid = np.abs(((freqs[sel] / (f / 2)) + 0.5) % 1 - 0.5) * (f / 2)
                harm = grid < np.maximum(0.03 * freqs[sel], 4)
                p = mag[sel] ** 2
                row["noise_db"] = round(10 * math.log10((p[~harm].sum() + 1e-20) / (p[harm].sum() + 1e-20)), 1)
                # high-pass indicator: fundamental versus 2nd harmonic, A2 against A4
                a4 = o.events["key_A4"]
                f4, m4 = spectrum(o.seg(a4["on"] + 0.15, a4["on"] + 0.65), o.sr)
                if f4 is not None:
                    r4 = 20 * math.log10((amp_at(f4, m4, 4 * f) + 1e-12) / (amp_at(f4, m4, 8 * f) + 1e-12))
                    r2 = 20 * math.log10((a1 + 1e-12) / (hs[1] + 1e-12))
                    row["lowcut_db"] = round(r4 - r2, 1)
    # modulations: on the pass whose long note stays audible the longest
    best, best_len = None, 0.0
    for name in ("open", "default", "env255"):
        tk = takes.get(name)
        if tk:
            ln = audible_until(tk, 6.0)
            if ln > best_len + 0.5:
                best, best_len = tk, ln
    if best and best_len > 1.5:
        row["mod_pass"] = best.meta["pass"]
        f_ref = NOTE_A2 * 2 ** row.get("octave", 0)
        tr = track(best, 0.1, min(best_len, 5.95), f_ref)
        if tr is not None:
            for col, name, unit_scale in ((0, "lfo_pitch", 1), (1, "lfo_filter", 1), (2, "pwm", 1)):
                rate, swing = modulation(tr[:, col])
                row[f"{name}_hz"] = round(rate, 2)
                row[f"{name}_swing"] = round(swing, 2)
                row[f"{name}_delay_s"] = round(modulation_delay(tr[:, col], rate), 2)
        row.update(chorus(best, 0.3, min(best_len, 5.95)))
    # envelope control at its extremes
    for name in ("env000", "env255"):
        tk = takes.get(name)
        if tk:
            env = envelope(tk, 6.0, 3.0)
            for k in ("sustain_db", "decay_to_-20dB_ms", "release_-20dB_ms", "floor_dbfs"):
                row[f"{name}_{k}"] = env.get(k)
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captures", help="folder holding default/, open/, env000/, env255/")
    ap.add_argument("-o", "--output", required=True, help="CSV file to write")
    ap.add_argument("--sounds", help="comma-separated labels, default all 64")
    args = ap.parse_args()
    root = Path(args.captures)
    wanted = None
    if args.sounds:
        wanted = {(int(s[0]) - 1) * 8 + int(s[2]) - 1 for s in args.sounds.split(",")}
    rows = []
    for idx in range(64):
        if wanted is not None and idx not in wanted:
            continue
        takes = {}
        for pass_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            js = pass_dir / f"{pass_dir.name}_P{idx + 1:02d}_{label(idx)}.json"
            if js.exists():
                takes[pass_dir.name] = Take(js)
        if not takes:
            continue
        rows.append(analyse_sound(takes, idx))
        print(f"{label(idx)} analysed", file=sys.stderr)
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.output}: {len(rows)} sounds")


if __name__ == "__main__":
    main()
