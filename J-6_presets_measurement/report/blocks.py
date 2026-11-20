"""The intermediate tables of README.md, sections 4.6 and 4.8.

  python3 report/blocks.py results results/synthetic > blocks.md
"""
import csv, sys, statistics as st
R = sys.argv[1]
def rd(n): return list(csv.DictReader(open(f"{R}/{n}.csv")))
def fmt(x, nd=0, dash="-"):
    if x in (None, ""): return dash
    try: v = float(x)
    except ValueError: return x
    s = f"{v:.{nd}f}"
    return "0" if s in ("-0", "-0.0") and nd == 0 else s
out = []
TRACK = {"vibrato": "pitch", "filter LFO": "brightness", "PWM": "even share", "stepped brightness": "brightness steps"}
def tn(x): return TRACK.get(x, x)
def table(head, rows):
    out.append("| " + " | ".join(head) + " |"); out.append("|" + "---|" * len(head))
    for r in rows: out.append("| " + " | ".join(r) + " |")
    out.append("")
out.append("### FILTER sweep (6-8, RESONANCE 255)")
table(["FILTER", "level, A2 (dBFS)", "ringing peak, A2 (Hz)", "level, A4 (dBFS)", "ringing peak, A4 (Hz)"],
      [[r["FILTER"], fmt(r["level_A2_dbfs"], 1), fmt(r["peak_A2_hz"]), fmt(r["level_A4_dbfs"], 1), fmt(r["peak_A4_hz"])] for r in rd("sweep_filter")])
out.append("### RESONANCE sweep (2-7, FILTER 69), gains against RESONANCE 0")
table(["RESONANCE", "fundamental, A2 (dB)", "peak, A2 (dB)", "at (Hz)", "fundamental, A4 (dB)", "peak, A4 (dB)", "at (Hz)"],
      [[r["RESONANCE"], fmt(r["fundamental_gain_A2_db"], 1), fmt(r["peak_gain_A2_db"], 1), fmt(r["peak_A2_hz"]), fmt(r["fundamental_gain_A4_db"], 1), fmt(r["peak_gain_A4_db"], 1), fmt(r["peak_A4_hz"])] for r in rd("sweep_resonance")])
out.append("### ATTACK sweep (2-7)")
table(["ATTACK", "to -20 dB (ms)", "to -10 dB (ms)", "to -3 dB (ms)", "to peak (ms)", "sustain (dB)", "release to -20 dB (ms)"],
      [[r["ATTACK"], fmt(r["rise_to_-20dB_ms"]), fmt(r["rise_to_-10dB_ms"]), fmt(r["rise_to_-3dB_ms"]), fmt(r["rise_to_peak_ms"]), fmt(r["sustain_db"], 1), fmt(r["release_-20dB_ms"])] for r in rd("sweep_attack")])
out.append("### ENV sweep (1-3)")
table(["ENV", "decay to -20 dB (ms)", "to -40 dB (ms)", "sustain (dB)", "release to -20 dB (ms)", "to -40 dB (ms)", "staccato release to -20 dB (ms)", "brightness at 0.05 / 1 / 5 s (Hz)"],
      [[r["ENV"], fmt(r["decay_to_-20dB_ms"]), fmt(r["decay_to_-40dB_ms"]), fmt(r["sustain_db"], 1), fmt(r["release_-20dB_ms"]), fmt(r["release_-40dB_ms"]), fmt(r["staccato_release_-20dB_ms"]),
        f"{fmt(r['centroid_0.05s_hz'])} / {fmt(r['centroid_1s_hz'])} / {fmt(r['centroid_5s_hz'])}"] for r in rd("sweep_env")])
out.append("### Long releases (1-3)")
table(["ENV", "level at note-off (dBFS)", "-20 dB (s)", "-40 dB (s)", "-60 dB (s)", "decay (dB/s)"],
      [[r["ENV"], fmt(r["level_at_off_dbfs"], 1), fmt(r["release_-20dB_s"], 2), fmt(r["release_-40dB_s"], 2), fmt(r["release_-60dB_s"], 2), fmt(r["decay_db_per_s"], 2)] for r in rd("longtail")])
v = rd("velocity")
out.append("### Velocity (A3, one note per second)")
sounds = sorted({r["sound"] for r in v})
table(["velocity"] + [f"{s} level (dB)" for s in sounds],
      [[vel] + [fmt(next(r["level_db_re_127"] for r in v if r["sound"] == s and r["velocity"] == vel), 1) for s in sounds] for vel in [r["velocity"] for r in v if r["sound"] == sounds[0]]])
table(["sound", "exponent n (level ~ velocity^n)", "largest residual (dB)", "brightness trend 0-127 (oct)", "brightness scatter (oct)"],
      [[s, fmt(r["level_exponent"], 2), fmt(r["level_residual_max_db"], 2), fmt(r["brightness_slope_oct"], 2), fmt(r["brightness_scatter_oct"], 2)] for s in sounds for r in [next(r for r in v if r["sound"] == s)]])
p = rd("poly")
for s in sorted({r["sound"] for r in p})[:1]:
    out.append(f"### Polyphony ({s}): level of each note's fundamental, dB against the loudest")
    notes = list(dict.fromkeys(r["note"] for r in p if r["sound"] == s))
    wins = list(dict.fromkeys((r["from_s"], r["to_s"]) for r in p if r["sound"] == s))
    table(["window (s)"] + [f"{n}" for n in notes],
          [[f"{a}-{b}"] + [fmt(next(r["level_db"] for r in p if r["sound"] == s and r["note"] == n and r["from_s"] == a), 0, ".") for n in notes] for a, b in wins])
t = rd("tempo")
rows = []
for r in t:
    for k, name in (("vibrato", "pitch"), ("filter_lfo", "brightness"), ("pwm", "even share")):
        a, b = r[f"{k}_hz_default"], r[f"{k}_hz_tempo150"]
        if a and b:
            rows.append([r["sound"], name, fmt(a, 2), r[f"{k}_note_default"] or "?", fmt(b, 2), r[f"{k}_note_tempo150"] or "?", f"{float(b) / float(a):.3f}",
                         f"{fmt(r[f'{k}_delay_s_default'], 2)} / {fmt(r[f'{k}_delay_s_tempo150'], 2)}"])
out.append("### Tempo: LFOs found at 100 and 150 BPM")
table(["sound", "track", "100 BPM (Hz)", "note", "150 BPM (Hz)", "note", "ratio", "delay at 100 / 150 BPM (s)"], rows)
fs = rd("filters_summary"); fc = rd("filters_curve")
out.append("### FILTER per sound (resonant peak brought to A2)")
vals = sorted({int(r["FILTER"]) for r in fc})
table(["FILTER"] + [r["sound"] for r in fs],
      [[str(v)] + [fmt(next((c["peak_at_A2_hz"] for c in fc if c["sound"] == r["sound"] and int(c["FILTER"]) == v), ""), 0, "") for r in fs] for v in vals])
table(["sound", "keyboard tracking (octave per octave)", "spread", "FILTER values used", "FILTER for 1 kHz at A2"],
      [[r["sound"], fmt(r["key_tracking"], 2), fmt(r["key_tracking_spread"], 2), r["filter_values_for_tracking"], fmt(r["FILTER_for_1kHz_at_A2"], 0, "below 17")] for r in fs])
ln = rd("longnote")
out.append("### Closing pass: each modulation looked for at the other tempo")
rows = []
for r in ln:
    for k in ("at_60_bpm", "at_70_bpm", "at_100_bpm"):
        if r.get(k):
            rows.append([r["sound"], tn(r["measurement"]), f"{fmt(r['rate_hz'], 3)} Hz at {fmt(r['tempo_bpm'])} BPM", k.split("_")[1] + " BPM", r[k]])
table(["sound", "measured on", "found", "looked for at", "verdict"], rows)
out.append("### Chord test (four notes held together)")
table(["sound", "measured on", "rate (Hz)", "phase agreement against the clock", "against each note-on", "verdict"],
      [[r["sound"], r.get("measurement") or "-", fmt(r.get("rate_hz"), 3), fmt(r.get("concentration_re_clock"), 2), fmt(r.get("concentration_re_note_on"), 2), r["verdict"]] for r in rd("chord")])
out.append("### Final pass: 8-2")
table(["take", "measured on", "rate (Hz)", "note", "swing", "height (x median)"],
      [[f"{fmt(r['tempo_bpm'])} BPM, FILTER {r['FILTER']}", tn(r["measurement"]), fmt(r["rate_hz"], 3), r["nearest_note_value"], fmt(r["swing"], 3), fmt(r["prominence"], 0)] for r in rd("verylong") + rd("longnote2") if r["sound"] == "8-2" and not r["chorus_harmonic"] and r["measurement"]])
out.append("### Final pass: brightness jitter and harmonic fluctuation")
j = rd("longnote2_jitter") + rd("verylong_jitter")
table(["sound", "BPM", "FILTER / RES", "brightness jitter 5-45 Hz, both channels (oct)", "between channels (oct)", "harmonic fluctuation 1-45 Hz (oct rms)"],
      [[r["sound"], fmt(r["tempo_bpm"]), f"{r['FILTER']} / {r['RESONANCE']}", fmt(r["together_5_45_oct"], 3), fmt(r["apart_5_45_oct"], 3), fmt(r.get("harmonic_fluctuation_oct"), 2)] for r in j])
out.append("### Finalfinal pass (eight 8 s notes)")
table(["sound", "BPM", "measured on", "rate (Hz)", "against the note-on", "against the clock", "verdict"],
      [[r["sound"], fmt(r["tempo_bpm"]), tn(r["measurement"]), fmt(r["rate_hz"], 3), fmt(r["concentration_re_note_on"], 2), fmt(r["concentration_re_take"], 2), r["verdict"]] for r in rd("keysync3")])
dd = rd("destinations")
out.append("### Destinations: swing at the LFO rate, filter at the sound's setting / fully open")
def cell(r, pas, k, nd):
    return fmt(r.get(f"{pas}_{k}"), nd, "")
rows = []
for r in dd:
    if r.get("default_pitch_cents") not in (None, ""):
        rows.append([r["sound"], fmt(r["rate_hz"], 3), f"{cell(r, 'default', 'pitch_cents', 1)} / {cell(r, 'open', 'pitch_cents', 1)}",
                     f"{cell(r, 'default', 'brightness_oct', 2)} / {cell(r, 'open', 'brightness_oct', 2)}", f"{cell(r, 'default', 'even_share', 2)} / {cell(r, 'open', 'even_share', 2)}"])
    else:
        rows.append([r["sound"] + " (ENV 255)", fmt(r["rate_hz"], 3), cell(r, "env255", "pitch_cents", 1), cell(r, "env255", "brightness_oct", 2), cell(r, "env255", "even_share", 2)])
table(["sound", "rate (Hz)", "pitch (cents)", "brightness (oct)", "even share"], rows)

out.append("### LFO phase: seven or eight A2 notes per sound")
rows = []
for name, label in (("keysync", "keysync (7 notes of 3.5 s)"), ("keysync2", "keysync2 (8 notes of 3.5 s)"), ("keysync3", "keysync3 (8 notes of 8 s)")):
    data = rd(name)
    DEC = ("free-running", "restarts with each note")
    groups = {}
    for r in data:
        bpm = r.get("tempo_bpm") or ("100" if name != "keysync" or r["sound"] != "8-7" else "150")
        groups.setdefault((r["sound"], bpm), []).append(r)
    for (snd, bpm), rs in groups.items():
        dec = [r for r in rs if r["verdict"] in DEC]
        shown = [dec[0]] if dec else [rs[0]]
        shown += [r for r in dec[1:] if r["verdict"] != dec[0]["verdict"]][:1]
        for r in shown:
            rows.append((snd, name, [snd, name, fmt(bpm), tn(r.get("measurement")) or "-", fmt(r.get("rate_hz"), 3), r.get("nearest_note_value") or "-",
                         fmt(r.get("concentration_re_note_on"), 2), fmt(r.get("concentration_re_take"), 2), r["verdict"]]))
rows.sort(key=lambda x: (x[0], ("keysync", "keysync2", "keysync3").index(x[1])))
table(["sound", "pass", "BPM", "measured on", "rate (Hz)", "note", "against the note-on", "against the clock", "verdict"], [r for _, _, r in rows])
# ---- chorus modes
ch = rd("chorus")
out.append("### Chorus modes")
def hgt(r, k): return fmt(r.get(f"height_{k}"), 1)
table(["sound", "main analysis", "height at 0.543 Hz (I)", "at 0.880 Hz (II)", "at 7.57 Hz (fast)", "verdict"],
      [[r["sound"], r["main_analysis"], hgt(r, "I"), hgt(r, "II"), hgt(r, "fast"), r["verdict"]]
       for r in ch if r["main_analysis"] not in ("I", "II", "Off") or r["verdict"] != r["main_analysis"]])
known = [r for r in ch if r["main_analysis"] in ("I", "II")]
ratios = []
for r in known:
    h = sorted((float(r[f"height_{k}"]) for k in ("I", "II", "fast")), reverse=True)
    ratios.append(h[0] / h[1])
agree = sum(r["verdict"] == r["main_analysis"] for r in known)
offs = [r for r in ch if r["main_analysis"] == "Off"]
out.append(f"On the {len(known)} sounds the main analysis had named I or II, the test agrees on {agree}, the winning "
           f"height standing {min(ratios):.1f} to {max(ratios):.1f} times above the next (median {st.median(ratios):.1f}); "
           f"the {len(offs)} sounds it found off are exact mono on every take ({sum(r['verdict'] == 'Off' for r in offs)} of {len(offs)}).")
out.append("")

# ---- [ENVELOPE]
ev = rd("envelope")
def val(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def rel_txt(r, env):
    v = val(r[f"release_ms_env{env}"])
    if v is not None:
        return f"{v / 1000:.1f} s" if v >= 1000 else f"{v:.0f} ms"
    return "over 3 s" if str(env) in r["release_over_3s_at_env"].split() else "-"
def cell(r, env):
    s_, dec = val(r[f"sustain_db_env{env}"]), val(r[f"decay_ms_env{env}"])
    if s_ is None:
        return f"no sustain; -20 dB in {dec / 1000:.1f} s" if dec and dec >= 1000 else (f"no sustain; -20 dB in {dec:.0f} ms" if dec else "no sustain")
    v = round(s_)
    txt = f"{0 if v == 0 else v} dB"
    if dec and s_ <= -20:
        txt += f" after a {dec / 1000:.1f} s decay" if dec >= 1000 else f" after a {dec:.0f} ms decay"
    return f"{txt}; release {rel_txt(r, env)}"
def ms(x):
    return "-" if x is None else (f"{x / 1000:.1f} s" if x >= 1000 else f"{x:.0f} ms")
GROUPS = [("pluck", "Pluck"), ("decaying", "Decaying tone"), ("gated", "Gated"), ("tail", "With a tail")]
def sus_med(mine, e):
    """Median sustain, a note without sustain counting as the lowest."""
    v = sorted((val(r[f"sustain_db_env{e}"]) if val(r[f"sustain_db_env{e}"]) is not None else -999) for r in mine)
    m_ = st.median(v)
    return "none" if m_ <= -999 else f"{m_:.0f} dB"
def rel_med(mine, e):
    """Median release over the members that sustain at e (3 s and more as such);
    '-' when fewer than half of them sustain."""
    v = []
    for r in mine:
        if val(r[f"sustain_db_env{e}"]) is None:
            continue
        x = val(r[f"release_ms_env{e}"])
        v.append(x if x is not None else (3001 if str(e) in r["release_over_3s_at_env"].split() else None))
    v = [x for x in v if x is not None]
    if len(v) * 2 < len(mine):
        return "-"
    m_ = st.median(v)
    return "over 3 s" if m_ > 3000 else ms(m_)
def dec_med(mine, e):
    return ms(st.median([val(r[f"decay_ms_env{e}"]) for r in mine if val(r[f"decay_ms_env{e}"]) is not None]))
def members(key):
    return [r for r in ev if r["group"] == key]
P, D, G, T = (members(k) for k in ("pluck", "decaying", "gated", "tail"))
gated_short = [r["sound"] for r in G if val(r["release_ms_env255"]) is not None and val(r["release_ms_env255"]) < 50]
tail_over = sum(1 for r in T if "255" in r["release_over_3s_at_env"].split())
WHAT = {
 "pluck": f"No sustain up to the middle of the knob, which sets how fast the note dies away (to -20 dB in a median "
          f"{dec_med(P, 0)} at 0, {dec_med(P, 128)} at 128). Past the middle a sustain appears, which reaches nearly full level at 255.",
 "decaying": f"A faint sustain up to the middle, raised to about -10 dB at the top; the decay and the release lengthen "
             f"with the knob.",
 "gated": f"Sustained at every setting, but up to the middle of the knob the release stays under 50 ms, as if gated; "
          f"towards the top a release appears ({' and '.join(gated_short)} stay gated even at 255).",
 "tail": f"Sustained at every setting, with a release tail already at the middle of the knob; at 255 the release "
         f"lasts over 3 s on {tail_over} of the {len(T)}.",
}
out.append("### ENVELOPE groups")
rows = []
for key, name in GROUPS:
    mine = members(key)
    rows.append([name, WHAT[key], ", ".join(r["sound"] for r in mine) + f" ({len(mine)})",
                 " / ".join(sus_med(mine, e) for e in (0, 128, 255)), " / ".join(rel_med(mine, e) for e in (0, 128, 255))])
table(["group", "what [ENVELOPE] does", "sounds", "median sustain at ENV 0 / 128 / 255", "median release at ENV 0 / 128 / 255"], rows)
out.append("### ENVELOPE per sound")
gname = dict(GROUPS)
table(["sound", "group", "ENV 0", "ENV 128 (default)", "ENV 255"],
      [[r["sound"], gname[r["group"]], cell(r, 0), cell(r, 128), cell(r, 255)] for r in ev])

if len(sys.argv) > 2:
    S = sys.argv[2]
    def sd(n): return list(csv.DictReader(open(f"{S}/{n}.csv")))
    out.append("### Synthetic validation")
    exp = {("keysync", "1-1"): "restarts (5 Hz vibrato)", ("keysync", "1-2"): "free-running (4.444 Hz vibrato)",
           ("keysync", "1-3"): "free-running (4.444 Hz sample and hold)", ("keysync", "1-4"): "no LFO",
           ("keysync2", "1-3"): "free-running (2 Hz vibrato at 60 BPM)",
           ("keysync3", "5-8"): "free-running (0.556 Hz, envelope spike)", ("keysync3", "5-6"): "restarts (0.556 Hz, envelope spike)"}
    rows = []
    for n in ("keysync", "keysync2", "keysync3"):
        for r in sd(n):
            rows.append([n, r["sound"], exp[(n, r["sound"])], tn(r.get("measurement")) or "-", fmt(r.get("rate_hz"), 3),
                         fmt(r.get("concentration_re_note_on"), 2), fmt(r.get("concentration_re_take"), 2), r["verdict"]])
    for r in sd("chord"):
        rows.append(["chord", r["sound"], {"1-4": "one LFO shared by the voices (5 Hz)", "1-5": "one LFO per voice, restarting (4.444 Hz)"}[r["sound"]],
                     r["measurement"], fmt(r["rate_hz"], 3), fmt(r["concentration_re_note_on"], 2), fmt(r["concentration_re_clock"], 2), r["verdict"]])
    table(["experiment", "sound", "built as", "measured on", "rate (Hz)", "against the note-on", "against the clock", "verdict"], rows)
    rows = []
    for n in ("longnote", "verylong"):
        for r in sd(n):
            v = r.get("at_60_bpm") or r.get("at_100_bpm")
            rows.append([n, r["sound"], {"1-1": "vibrato on a 1/16., follows the tempo", "1-2": "filter LFO fixed at 6.81 Hz", "1-6": "filter LFO on 4/1, follows the tempo"}[r["sound"]],
                         fmt(r["tempo_bpm"]), tn(r["measurement"]), fmt(r["rate_hz"], 3), v or "-"])
    table(["experiment", "sound", "built as", "BPM", "measured on", "rate (Hz)", "at the other tempo"], rows)
    f = sd("filters_summary")[0]
    out.append(f"Filters, 3-5 (built with keyboard tracking 0.50, 1 kHz at A2 for FILTER 120 and 14.4 steps per octave): measured tracking {fmt(f['key_tracking'], 2)}, 1 kHz at A2 for FILTER {fmt(f['FILTER_for_1kHz_at_A2'])}, {fmt(f['steps_per_octave_median'], 1)} steps per octave.")
    out.append("")
    table(["longtail (1-3)", "built as", "-20 dB (s)", "-40 dB (s)", "-60 dB (s)", "decay (dB/s)"],
          [[f"ENV {r['ENV']}", {"238": "4 dB/s", "255": "2 dB/s"}[r["ENV"]], fmt(r["release_-20dB_s"], 2), fmt(r["release_-40dB_s"], 2), fmt(r["release_-60dB_s"], 2), fmt(r["decay_db_per_s"], 2)] for r in sd("longtail")])
    table(["longnote2", "built as", "FILTER", "brightness jitter 0.5-5 Hz, together / apart (oct)", "harmonic fluctuation (oct rms)"],
          [[r["sound"], {"1-7": "noisy source, random filter movement", "1-8": "noisy source, static filter"}[r["sound"]], r["FILTER"],
            f"{fmt(r['together_0.5_5_oct'], 3)} / {fmt(r['apart_0.5_5_oct'], 3)}", fmt(r["harmonic_fluctuation_oct"], 3)] for r in sd("longnote2_jitter")])

print("\n".join(out))
