#!/usr/bin/env python3
"""Measure the J-6's sounds from the takes recorded by j6capture.py.

  python3 j6analyze.py CAPTURES_DIR -o measurements.csv [--sounds 1-1,4-4]

CAPTURES_DIR holds one folder per pass: default (each sound as selected),
open (filter fully open, resonance 0), env000 and env255 ([ENVELOPE] at its
extremes). Each take is aligned on its own audio: the first note's onset is
found by fitting the stimulus's note pattern to the take's onset curve,
because the recorder's start-up time varies by tens of milliseconds.

Checked against the reference spreadsheet: chorus agrees on 64 of 64 sounds,
glide on 60 of 60 measurable, vibrato on 56 of 64, filter LFO on 53 of 64,
LFO delay (yes / no) on 34 of 37 with an LFO measured. Known limits: octave and sub-oscillator are ambiguous for mixed waveforms;
sounds whose note decays within 1.5 s get no modulation measurement;
detections on a harmonic of the chorus LFO are flagged in lfo_flags.

Measurements, per sound:
  default pass  amplitude envelope of the 6 s A2 note (attack to -3 dB of the
                smoothed peak, decay, sustain, release), staccato release,
                filter envelope (brightness at onset against later), keyboard
                tracking (brightness relative to pitch, A2 against A4), glide,
                velocity (level and brightness, 40 against 127)
  open pass     oscillator: octave of the oscillator against the played note,
                sub-oscillator (components one octave down following a
                square wave's 1/3, 1/5 law), harmonic profile, noise share,
                all on the brightest frame of the A4 note
  modulation    on the pass where the long note lasts longest: pitch
                (vibrato), brightness (filter LFO) and 2nd/1st harmonic ratio
                (PWM), both channels; a modulation counts if it moves both
                channels in phase and is not within 0.35 Hz of the chorus rate,
                half it or twice it (the analysis resolves about 0.2 Hz);
                each rate is matched to a note value at the pattern tempo, since
                the J-6's LFOs follow it; slowest detectable rate 0.3 Hz;
                chorus I or II from the stereo difference signal
  env passes    sustain and release with [ENVELOPE] at 0 and 255

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
A2, A4 = 110.0, 440.0
# Modulation of the stereo difference/sum energy ratio measured on sounds the
# reference spreadsheet marks chorus I and II. The chorus's own sweep shows in
# per-channel measurements at these rates and at half of them.
CHORUS_MOD = {"I": 1.09, "II": 1.76}
PASSES = ("default", "open", "env000", "env255")


def label(i: int) -> str:
    return f"{i // 8 + 1}-{i % 8 + 1}"


def db(p):
    return 10 * np.log10(np.asarray(p) + EPS)


def r(x, nd=1):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, nd)


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
        best, best_tau = -1.0, pre
        for tau in np.arange(pre - 0.25, pre + 0.4, 0.002):
            s = 0.0
            for on in ons:
                a = int((tau + on - 0.004) * sr / hop)
                b = int((tau + on + 0.012) * sr / hop)
                if 0 <= a < b <= len(rise):
                    s += rise[a:b].max()
            if s > best:
                best, best_tau = s, tau
        if floor <= -99:   # digital silence before the note: the first non-zero sample is exact
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
        a = max(int((self.t0 + start) * self.sr / self.hop), 0)
        b = int((self.t0 + end) * self.sr / self.hop)
        return float(db(self.pow[a:b].mean())) if b > a else -240.0

    def curve(self, start: float, end: float, smooth: float = 0.0):
        a = max(int((self.t0 + start) * self.sr / self.hop), 0)
        b = int((self.t0 + end) * self.sr / self.hop)
        p = self.pow[a:b]
        if smooth > 0:
            k = max(int(smooth * self.sr / self.hop), 1)
            p = np.convolve(p, np.ones(k) / k, mode="same")
        t = (np.arange(a, a + len(p)) * self.hop / self.sr) - self.t0
        return t, db(p)


def spectrum(sig, sr, nfft=1 << 17):
    if len(sig) < 256 or not np.any(sig):
        return None, None
    w = np.hanning(len(sig))
    mag = np.abs(np.fft.rfft(sig * w, nfft)) / (w.sum() / 2)
    return np.fft.rfftfreq(nfft, 1 / sr), mag


def grid(freqs, mag, base, kmax, rel=0.006):
    """Peak magnitude near each multiple of base, without overlapping windows."""
    out = np.zeros(kmax)
    for k in range(1, kmax + 1):
        f = base * k
        w = min(max(f * rel, 2.0), 0.4 * base)
        sel = (freqs > f - w) & (freqs < f + w)
        out[k - 1] = mag[sel].max() if sel.any() else 0.0
    return out


def centroid(sig, sr):
    freqs, mag = spectrum(sig, sr, 1 << 14)
    if freqs is None:
        return float("nan")
    sel = (freqs > 20) & (freqs < 16000)
    p = mag[sel] ** 2
    return float((freqs[sel] * p).sum() / p.sum()) if p.sum() > 0 else float("nan")


def oscillator(take: Take) -> dict:
    """Oscillator make-up from the A4 note of the open-filter pass."""
    ev = take.events["key_A4"]
    sr = take.sr
    n, hop = int(0.1 * sr), int(0.025 * sr)
    sig = take.seg(ev["on"] + 0.05, ev["off"] - 0.02, "stereo")
    if len(sig) < n:
        return {}
    # Average the harmonic levels over the whole note, per channel, following
    # the pitch frame by frame: this evens out the chorus's comb sweep, PWM
    # and vibrato instead of picking one moment of them.
    nfft = 1 << 16
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    w = np.hanning(n)
    cgrid = np.arange(-150, 151, 1.0)
    acc, count, noise = np.zeros(24), 0, []
    for i in range(0, len(sig) - n, hop):
        for ch in (0, 1):
            fr = sig[i:i + n, ch]
            if np.sqrt(np.mean(fr ** 2)) < 1e-5:
                continue
            mag = np.abs(np.fft.rfft(fr * w, nfft))
            score = sum(np.interp(A4 * k * 2 ** (cgrid / 1200), freqs, mag) for k in range(1, 5))
            base = 220.0 * 2 ** (cgrid[int(np.argmax(score))] / 1200)
            acc += grid(freqs, mag, base, 24, rel=0.02) ** 2
            count += 1
            sel = (freqs > 150) & (freqs < 8000)
            half = base / 2
            dist = np.abs(((freqs[sel] / half) + 0.5) % 1 - 0.5) * half
            pw = mag[sel] ** 2
            harm = dist < np.maximum(0.015 * freqs[sel], 22.0)   # 100 ms Hann main lobe: +-20 Hz
            noise.append(pw[~harm].sum() / max(pw[harm].sum(), EPS))
    if count == 0:
        return {}
    g = np.sqrt(acc / count)
    lv = 20 * np.log10(g / g.max() + 1e-12)        # dB re strongest, k x 220 Hz (pitch-following)
    present = lv > -25
    k_low = next((k for k in (1, 2, 4) if present[k - 1]), 2)

    def c(m):   # level of the m-th multiple of the lowest component
        k = m * k_low
        return lv[k - 1] if k <= len(lv) else -120.0

    d3, d5 = c(3) - c(1), c(5) - c(1)
    square_law = abs(d3 + 9.5) < 4.5 and (c(5) < -45 or abs(d5 + 14) < 5)
    saw_like = abs(c(2) - c(1) + 6) < 2 and abs(c(4) - c(1) + 12) < 3
    out = {}
    # sub interpretation only when the oscillator is within 12 dB of the sub;
    # otherwise it is one waveform with faint even harmonics (e.g. a square)
    if square_law and c(2) - c(1) > -12 and not saw_like:
        dco = 2 * k_low * 220.0                       # lowest component is a sub-oscillator
        out["sub_db"] = r(c(1) - c(2))
        kd = 2 * k_low
    else:
        dco = k_low * 220.0
        kd = k_low
        half = kd // 2
        out["sub_db"] = r(lv[half - 1] - lv[kd - 1]) if half >= 1 and lv[half - 1] > -45 else None
    out["osc_octave"] = int(round(math.log2(dco / A4)))
    h = [lv[kd * m - 1] if kd * m <= len(lv) else -120.0 for m in range(1, 9)]
    for m in range(2, 9):
        out[f"h{m}_db"] = r(h[m - 1] - h[0])
    rel = [h[m] - h[0] for m in range(1, 8)]
    even = [rel[1 - 1], rel[3 - 1], rel[5 - 1]]                  # h2, h4, h6
    if max(even) < -25 and abs(rel[2 - 1] + 9.5) < 5:
        wave = "square"
    elif abs(rel[0] + 6) < 3 and abs(rel[1] + 9.5) < 4 and abs(rel[2] + 12) < 5:
        wave = "saw"
    elif h[0] < max(h):
        wave = "pulse/mix (h1 not strongest)"
    else:
        ratio = 10 ** (rel[0] / 20)
        duty = math.acos(min(ratio, 1.0)) / math.pi if ratio <= 1 else None
        if duty and duty >= 0.45:
            wave = "square"                           # within measurement accuracy
        else:
            wave = f"pulse ~{duty:.2f}" if duty and duty > 0.05 else "pulse/mix"
    out["wave"] = wave
    out["noise_db"] = r(10 * math.log10(np.median(noise) + 1e-20)) if noise else None
    f2, m2 = spectrum(take.seg(0.15, 0.65), sr)
    if f2 is not None:
        # low cut: fundamental against 2nd harmonic, A2 against A4
        g2 = grid(f2, m2, dco / 4, 2)
        if g2.min() > 0:
            out["lowcut_db"] = r((h[0] - h[1]) - 20 * math.log10(g2[0] / g2[1]))
    return out


def track(take: Take, start: float, end: float, f1: float, frame=0.08, hop=0.01):
    """Per-frame pitch (cents re f1), brightness (log2 centroid) and the
    even harmonics' share of the first 8 harmonics' energy (0-1, moved by
    PWM), each averaged over the two channels."""
    sr = take.sr
    sig = take.seg(start, end, "stereo")
    n, h = int(frame * sr), int(hop * sr)
    if len(sig) < n * 4:
        return None
    nfft = 1 << 15
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    grid_c = np.arange(-120, 121, 1.0)
    w = np.hanning(n)
    rows = []
    for i in range(0, len(sig) - n, h):
        per = []
        for ch in (0, 1):
            fr = sig[i:i + n, ch]
            if np.sqrt(np.mean(fr ** 2)) < 1e-5:
                per.append((np.nan, np.nan, np.nan))
                continue
            mag = np.abs(np.fft.rfft(fr * w, nfft))
            score = sum(np.interp(f1 * k * 2 ** (grid_c / 1200), freqs, mag) for k in range(1, 5))
            cc = grid_c[int(np.argmax(score))]
            ff = f1 * 2 ** (cc / 1200)
            p = mag ** 2
            sel = (freqs > 20) & (freqs < 16000)
            cen = (freqs[sel] * p[sel]).sum() / max(p[sel].sum(), EPS)
            hk = np.interp(ff * np.arange(1, 9), freqs, mag) ** 2
            per.append((cc, math.log2(max(cen, 1e-9)), hk[1::2].sum() / max(hk.sum(), EPS)))
        rows.append(np.array(per, dtype=float))
    return np.array(rows, dtype=float)          # frames x channel x (pitch, brightness, even share)


def _clean(s):
    s = np.asarray(s, float)
    idx = np.arange(len(s))
    ok = ~np.isnan(s)
    if ok.sum() < 100:
        return None
    s = np.interp(idx, idx[ok], s[ok])
    return s - np.polyval(np.polyfit(idx, s, 2), idx)


def band(s, rate, hop=0.01, width=0.3):
    """Component of a cleaned series within rate +- width Hz."""
    spec = np.fft.rfft(s)
    f = np.fft.rfftfreq(len(s), hop)
    spec[np.abs(f - rate) > width] = 0
    return np.fft.irfft(spec, len(s))


def lfo(per, col, exclude=(), hop=0.01, fmin=0.3, fmax=18.0):
    """The most prominent modulation that moves both channels in phase (a
    chorus sweeps them in opposite phase). Returns rate, prominence, swing
    (p95-p5 of the band-limited mean of both channels), the series, and
    whether the rate sits at the edge of an excluded band: then it is
    usually the flank of a modulation inside the band, whose true rate is
    there (a 3.33 Hz LFO reads 3.17 Hz next to the chorus II band at
    3.52 +- 0.35 Hz)."""
    left, right = _clean(per[:, 0, col]), _clean(per[:, 1, col])
    if left is None or right is None:
        return None
    mean = (left + right) / 2
    nfft = 1 << 15
    spec = np.abs(np.fft.rfft(mean * np.hanning(len(mean)), nfft))
    f = np.fft.rfftfreq(nfft, hop)
    sel = np.flatnonzero((f > fmin) & (f < fmax))
    base = max(np.median(spec[sel]), 1e-12)
    order = sel[np.argsort(spec[sel])[::-1]]
    tried = []
    for i in order[:200]:
        rate = f[i]
        if (any(abs(rate - t) < 0.2 for t in tried) or any(abs(rate - e) < 0.35 for e in exclude)
                or rate > fmax - 0.5):           # a peak at the search limit is an edge effect
            continue
        tried.append(rate)
        prom = spec[i] / base
        if prom < 8 or len(tried) > 6:
            break
        bl, br = band(left, rate, hop), band(right, rate, hop)
        if np.std(bl) == 0 or np.std(br) == 0:
            continue
        if np.corrcoef(bl, br)[0, 1] > 0.5:
            bm = band(mean, rate, hop)
            edge = any(abs(abs(rate - e) - 0.35) < 0.015 for e in exclude)
            return float(rate), float(prom), float(np.percentile(bm, 95) - np.percentile(bm, 5)), mean, edge
    return None


def modulation_delay(series, rate, hop=0.01, t0=0.0):
    """LFO delay: time at which the modulation's depth envelope (Hilbert
    magnitude of the series band-limited to rate +- rate/2) reaches half its
    value later in the note (median over 50-85 % of the series). The
    series is zero-padded before the FFT filter, so the end of the note cannot
    wrap around into its start. Under one LFO cycle a delay cannot be told
    apart from the filter's own rise, so it is reported as 0. A strong onset
    transient in the series (a filter envelope's sweep, a pitch blip) fills
    the band at the start and hides a delay. t0 is the time of the series'
    first frame after the note-on."""
    from scipy.signal import hilbert
    s = np.asarray(series, float)
    if not rate or rate != rate or len(s) < 200:
        return float("nan")
    n = len(s)
    padded = np.concatenate([s, np.zeros(n)])
    env = np.abs(hilbert(band(padded, rate, hop, width=max(rate / 2, 0.3))))[:n]
    final = np.median(env[n // 2: int(n * 0.85)])
    if final <= 0:
        return float("nan")
    idx = np.flatnonzero(env >= 0.5 * final)
    if not len(idx):
        return float("nan")
    t = idx[0] * hop
    return t + t0 if t > 1.0 / rate else 0.0


def envelope(take: Take, gate: float, tail: float) -> dict:
    """Amplitude envelope of the long note."""
    t, lv = take.curve(0, gate + tail)
    ts, ls = take.curve(0, gate + tail, smooth=0.05)
    in_gate = t < gate
    peak = float(ls[in_gate].max())
    ipk = int(np.argmax(ls[in_gate]))
    out = {"peak_dbfs": r(float(lv[in_gate].max())), "floor_dbfs": r(take.floor_db)}
    hit = np.flatnonzero(ls[in_gate] >= peak - 3)
    out["attack_ms"] = r(1000 * max(ts[hit[0]], 0.0), 0)
    sus = take.level(gate - 0.5, gate - 0.05) - peak
    out["sustain_db"] = r(sus) if sus > -60 else None
    last = np.flatnonzero(in_gate)[-1] + 1
    after, ta = ls[ipk:last], ts[ipk:last]
    out["decay_ms"] = None
    if -60 < sus < -3:
        k = np.flatnonzero(after <= peak + sus + 3)
        out["decay_ms"] = r(1000 * (ta[k[0]] - ts[ipk]), 0) if len(k) else None
    for drop in (20, 40):
        k = np.flatnonzero(after <= peak - drop)
        out[f"decay_to_-{drop}dB_ms"] = r(1000 * (ta[k[0]] - ts[ipk]), 0) if len(k) else None
    off_level = take.level(gate - 0.08, gate - 0.01)
    rel = t >= gate
    tr, lr = t[rel] - gate, lv[rel]
    limit = take.floor_db + 10 if take.floor_db > -99 else -100
    for drop in (20, 40):
        target = off_level - drop
        k = np.flatnonzero(lr <= target)
        ok = off_level > -90 and target > limit
        out[f"release_-{drop}dB_ms"] = r(1000 * tr[k[0]], 0) if (ok and len(k)) else None
    return out


def glide(take: Take, target: float, tol: float = 40.0):
    """Settle time of the E3 note: from the moment it dominates until its pitch
    class stays within 40 cents of the target. Counted only if the pitch passes
    through intermediate values for at least 10 ms; 0 means it jumped. Each
    voice glides from the last pitch it played, so the starting pitch varies;
    octave errors do not count, and the pitch track is median-filtered."""
    ev = take.events["glide_to_E3"]
    sig = take.seg(ev["on"], ev["on"] + 1.2)
    sr = take.sr
    n, h = int(0.04 * sr), int(0.005 * sr)
    if len(sig) < 2 * n:
        return None
    nfft = 1 << 15
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    cand = np.arange(80.0, 900.0, 0.5)
    w = np.hanning(n)
    starts = list(range(0, len(sig) - n, h))
    rms = np.array([np.sqrt(np.mean(sig[i:i + n] ** 2)) for i in starts])
    peak = rms.max()
    loud = np.flatnonzero(rms >= peak * 10 ** (-10 / 20))
    if not len(loud):
        return None
    first = loud[0]                       # E3 dominates from here, after its attack
    quiet = np.flatnonzero((rms < peak * 10 ** (-20 / 20)) & (np.arange(len(rms)) > first))
    stop = quiet[0] if len(quiet) else len(starts)
    dist, from_a = [], []
    for k in range(first, stop):
        mag = np.abs(np.fft.rfft(sig[starts[k]:starts[k] + n] * w, nfft))
        f = cand[int(np.argmax(sum(np.interp(cand * m, freqs, mag) for m in range(1, 4))))]
        dist.append(abs(((1200 * math.log2(f / target)) + 600) % 1200 - 600))
        from_a.append(abs(((1200 * math.log2(f / A2)) + 600) % 1200 - 600))
    if len(dist) < 10:
        return None
    med = lambda x: np.array([np.median(x[max(0, i - 1):i + 2]) for i in range(len(x))])
    dist, from_a = med(np.array(dist)), med(np.array(from_a))
    between = (dist > tol + 20) & (from_a > tol + 20)
    run, moved = 0, False
    for b in between:
        run = run + 1 if b else 0
        if run >= 2:
            moved = True
            break
    off = np.flatnonzero(dist >= tol)
    settle = 0 if not len(off) else off[-1] + 1
    if settle >= len(dist) - 5:
        return None                       # never settled within the note
    return r(1000 * settle * h / sr, 0) if moved else 0.0


def chorus(take: Take, start: float, end: float) -> dict:
    seg = take.seg(start, end, "stereo")
    if len(seg) < take.sr:
        return {}
    side = (seg[:, 0] - seg[:, 1]) / 2
    if np.max(np.abs(side)) == 0:
        return {"chorus": "Off"}
    mid = seg.mean(axis=1)
    hop = int(0.01 * take.sr)
    n = len(mid) // hop
    pm = (mid[:n * hop] ** 2).reshape(n, hop).mean(1)
    ps = (side[:n * hop] ** 2).reshape(n, hop).mean(1)
    ok = pm > 1e-12
    out = {"chorus_lr_corr": r(float(np.corrcoef(seg[:, 0], seg[:, 1])[0, 1]), 3)}
    if ok.sum() < 150:
        out["chorus"] = "on"
        return out
    s = db(ps[ok]) - db(pm[ok])
    x = np.arange(len(s))
    s = s - np.polyval(np.polyfit(x, s, 2), x)
    nfft = 1 << 15
    spec = np.abs(np.fft.rfft(s * np.hanning(len(s)), nfft))
    f = np.fft.rfftfreq(nfft, 0.01)
    base = np.median(spec[(f > 0.3) & (f < 6)])
    score = {k: spec[np.abs(f - v) < 0.05].max() / max(base, 1e-12) for k, v in CHORUS_MOD.items()}
    name = max(score, key=score.get)
    out["chorus"] = name if score[name] > 4 else "on"
    out["chorus_score"] = r(score[name])
    return out


def audible_until(take: Take, gate: float, below=40):
    """Seconds after onset until the long note falls `below` dB under its peak."""
    t, lv = take.curve(0, gate, smooth=0.05)
    peak = lv.max()
    floor = max(peak - below, take.floor_db + 10)
    low = np.flatnonzero((lv < floor) & (t > t[np.argmax(lv)]))
    return float(t[low[0]]) if len(low) else gate


# Note values in beats, for LFO rates that follow the pattern tempo.
NOTE_VALUES = [(4, "1/1"), (3, "1/2."), (2, "1/2"), (1.5, "1/4."), (4 / 3, "1/2T"), (1, "1/4"),
               (0.75, "1/8."), (2 / 3, "1/4T"), (0.5, "1/8"), (0.375, "1/16."), (1 / 3, "1/8T"),
               (0.25, "1/16"), (0.1875, "1/32."), (1 / 6, "1/16T"), (0.125, "1/32")]


def note_value(rate: float, bpm: float):
    """Nearest note value whose repetition rate at bpm matches rate within 5 %
    (or 0.12 Hz, the analysis resolution for slow rates)."""
    best = min(NOTE_VALUES, key=lambda nv: abs(math.log(rate / (bpm / 60 / nv[0]))))
    exact = bpm / 60 / best[0]
    return best[1] if abs(rate - exact) <= max(0.05 * exact, 0.12) else None


def single_note(take: Take) -> bool:
    """True when the A2 note's energy sits on one harmonic series, false for a
    chord. The series' actual fundamental is found first (detuned sounds), then
    energy within 0.8 % of its half-frequency grid (which holds a sub-oscillator
    too) is compared with the total, 40 Hz - 2 kHz."""
    freqs, mag = spectrum(take.seg(0.05, 0.45), take.sr, 1 << 18)
    if freqs is None:
        return False
    cand = np.arange(103.0, 117.5, 0.05)
    score = sum(np.interp(cand * k / 2, freqs, mag) for k in range(1, 33))
    half = cand[int(np.argmax(score))] / 2
    sel = (freqs > 40) & (freqs < 2000)
    f, p = freqs[sel], mag[sel] ** 2
    near = np.abs(((f / half) + 0.5) % 1 - 0.5) * half < np.maximum(0.008 * f, 3.0)
    return p[near].sum() / max(p.sum(), EPS) > 0.7


def analyse_sound(takes: dict, idx: int) -> dict:
    row = {"sound": label(idx)}
    d, o = takes.get("default"), takes.get("open")
    osc = oscillator(o) if o else {}
    # Amplitude envelope from the open-filter pass: same amplitude envelope as
    # the preset, and its patterns carry each sound's own ATTACK.
    amp = o or d
    if amp:
        prm = amp.meta.get("prm", {})
        row.update({"ATTACK": prm.get("ATTACK"), "amp_pass": amp.meta["pass"], "onset": amp.onset_method})
        row.update({f"amp_{k}": v for k, v in envelope(amp, 6.0, 3.0).items()})
        st = amp.events["staccato_A2"]
        row["staccato_release_-20dB_ms"] = None
        t, lv = amp.curve(st["off"], st["off"] + 2.3)
        k = np.flatnonzero(lv <= amp.level(st["off"] - 0.03, st["off"]) - 20)
        if len(k):
            row["staccato_release_-20dB_ms"] = r(1000 * (t[k[0]] - st["off"]), 0)
    if d:
        prm = d.meta.get("prm", {})
        row.update({"FILTER": prm.get("FILTER"), "RESONANCE": prm.get("RESONANCE"),
                    "default_pass_ATTACK": prm.get("ATTACK")})
        v40, v127 = d.events["velocity_40"], d.events["velocity_127"]
        row["velocity_40_to_127_db"] = r(d.level(v127["on"], v127["on"] + 0.5)
                                         - d.level(v40["on"], v40["on"] + 0.5))
        c40 = centroid(d.seg(v40["on"] + 0.02, v40["on"] + 0.5), d.sr)
        c127 = centroid(d.seg(v127["on"] + 0.02, v127["on"] + 0.5), d.sr)
        row["velocity_brightness_oct"] = r(math.log2(c127 / c40), 2) if c40 > 0 and c127 > 0 else None
        until = audible_until(d, 6.0)
        late = min(1.0, max(until - 0.3, 0.1))
        ce, cl = centroid(d.seg(0.02, 0.08), d.sr), centroid(d.seg(late, late + 0.2), d.sr)
        row["filter_env_oct"] = r(math.log2(ce / cl), 2) if ce > 0 and cl > 0 else None
        a4 = d.events["key_A4"]
        c2 = centroid(d.seg(0.15, 0.45), d.sr)
        c4 = centroid(d.seg(a4["on"] + 0.15, a4["on"] + 0.45), d.sr)
        row["key_tracking"] = r(1 + math.log2((c4 / 4) / c2) / 2, 2) if c2 > 0 and c4 > 0 else None
    row.update(osc)
    # Modulations. Vibrato and PWM on the open-filter pass, where all
    # harmonics are present; filter LFO on the default pass, where the cutoff
    # sits where the preset has it (at full cutoff an LFO sweep is inaudible).
    tracks = {}
    for name in ("open", "default", "env255"):
        tk = takes.get(name)
        # env255 sustains the plucks; used only when the others are too short,
        # and only if it was recorded with single notes (not in chord mode)
        if name == "env255" and (tracks or not tk or not single_note(tk)):
            continue
        if tk:
            ln = audible_until(tk, 6.0)
            if ln > 1.5:
                f1 = A2 * 2 ** osc.get("osc_octave", 0)
                tr = track(tk, 0.1, min(ln, 5.95), f1)
                if tr is not None and len(tr) > 100:
                    tracks[name] = (tk, ln, tr)
    if tracks:
        tk, ln, _ = tracks.get("open") or tracks.get("default") or tracks.get("env255")
        row["mod_pass"] = tk.meta["pass"]
        ch = chorus(tk, 0.3, min(ln, 5.95))
        row.update(ch)
        # The chorus's sweep shows in these tracks at its rate, half and twice it.
        rates = [CHORUS_MOD[ch["chorus"]]] if ch.get("chorus") in CHORUS_MOD else (
            list(CHORUS_MOD.values()) if ch.get("chorus") == "on" else [])
        exclude = [v * m for v in rates for m in (0.5, 1, 2)]
        thresholds = {"vibrato": 6.0, "filter_lfo": 0.1, "pwm": 0.05}
        found = {}
        for col, name, prefer in ((0, "vibrato", ("open", "default", "env255")),
                                  (1, "filter_lfo", ("default", "open", "env255")),
                                  (2, "pwm", ("open", "default", "env255"))):
            pas = next((q for q in prefer if q in tracks), None)
            if pas:
                res = lfo(tracks[pas][2], col, exclude)
                if res and res[2] > thresholds[name]:
                    found[name] = res + (pas,)
        # One LFO moving several things shows in several tracks at one rate;
        # a pulse's PWM or a pitch change also shifts the brightness track.
        for weaker, stronger in (("filter_lfo", "pwm"), ("filter_lfo", "vibrato"), ("vibrato", "pwm")):
            if weaker in found and stronger in found and abs(found[weaker][0] - found[stronger][0]) < 0.1:
                small = {"filter_lfo": 0.5, "vibrato": 25.0}[weaker]
                if found[weaker][2] < small:
                    del found[weaker]
        src = tracks.get("default") or tracks.get("open") or tracks.get("env255")
        bl, br = _clean(src[2][:, 0, 1]), _clean(src[2][:, 1, 1])
        if bl is not None and br is not None:
            mb = (bl + br) / 2
            row["brightness_wobble_oct"] = r(float(np.percentile(mb, 95) - np.percentile(mb, 5)), 2)
        # The chorus LFO (half the measured chorus rate) is free-running and has
        # a whole harmonic series; the J-6's LFOs follow the pattern tempo. A
        # detection on a chorus harmonic that matches no note value is dropped as
        # the chorus; one that matches a note value is kept and flagged.
        bpm = float(tk.meta.get("prm", {}).get("TEMPO", 10000)) / 100
        row["tempo_bpm"] = bpm
        flags = []
        for name in list(found):
            rate = found[name][0]
            for v in rates:
                k = round(rate / (v / 2))
                if k >= 1 and abs(rate - k * v / 2) < 0.15:
                    if note_value(rate, bpm) is None:
                        del found[name]
                    else:
                        flags.append(f"{name} also on chorus harmonic {k}")
                    break
        for name in found:
            if found[name][4]:
                flags.append(f"{name} rate at the edge of a band excluded around the chorus: "
                             "the true rate is probably inside it")
        row["lfo_flags"] = "; ".join(flags) or None
        for name in ("vibrato", "filter_lfo", "pwm"):
            res = found.get(name)
            row[f"{name}_note"] = note_value(res[0], bpm) if res else None
            row[f"{name}_hz"] = r(res[0], 2) if res else None
            row[f"{name}_swing"] = r(res[2], 2) if res else None
            # the track starts 0.1 s after the note-on, and its frames are 0.08 s long
            row[f"{name}_delay_s"] = r(modulation_delay(res[3], res[0], t0=0.14), 2) if res else None
    else:
        row["lfo_flags"] = "note too short to measure modulation"
    if amp:
        # vibrato widens the pitch band a settled note stays in
        sw = row.get("vibrato_swing")
        row["glide_ms"] = glide(amp, A2 * 2 ** (7 / 12), max(40.0, sw / 2 + 15) if sw else 40.0)
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
        for name in PASSES:   # the experiment folders are for j6experiments.py
            js = root / name / f"{name}_P{idx + 1:02d}_{label(idx)}.json"
            if js.exists():
                takes[name] = Take(js)
        if takes:
            rows.append(analyse_sound(takes, idx))
            print(f"{label(idx)} analysed", file=sys.stderr)
    fields = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.output}: {len(rows)} sounds")


if __name__ == "__main__":
    main()
