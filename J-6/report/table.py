"""The results table of README.md, section 2.1, from the files in results/.

  python3 report/table.py results > table.md

L holds each sound's LFO verdict as the experiments settled it (keysync,
keysync2, keysync3, longnote, verylong, longnote2, destinations; README
section 4.6); the other columns come from measurements.csv and defaults.csv,
and the names from the comparison workbook.
"""
import csv, sys, math, openpyxl
R = sys.argv[1]
m = {r["sound"]: r for r in csv.DictReader(open(f"{R}/measurements.csv"))}
d = {r["sound"]: r for r in csv.DictReader(open(f"{R}/defaults.csv"))}
t = {r["sound"]: r for r in csv.DictReader(open(f"{R}/tempo.csv"))}
wb = openpyxl.load_workbook(f"{R}/J6_sounds_measured.xlsx", data_only=True)
ws = wb["Comparison"]; hdr = [c.value for c in ws[1]]
comp = {row[0]: dict(zip(hdr, row)) for row in ws.iter_rows(min_row=2, values_only=True)}
# Consolidated LFO verdicts (keysync, keysync2, keysync3, longnote, verylong, longnote2, destinations test)
L = {
 "1-4": ("filter ?", "slow, 0.3-0.6 Hz", None, "n/t", "seen only with ENV 255: a 0.23 octave brightness swing at 0.556 Hz (1/2.); unverified"),
 "1-5": None, "1-6": ("pulse width, pitch", "1/4T", 2.5, "n/t", "measured with ENV 255, where it sustains"),
 "1-7": ("pulse width", "1/4T", 2.5, "free", "spreadsheet: pulse width fixed"),
 "2-1": ("filter, pulse width", "1/8", 3.333, "n/t", "3.330 Hz with ENV 255 (first read at 3.17 Hz, a chorus band edge); Standing: 1/8th notes"),
 "2-4": ("pulse width", "1/8.", 2.222, "n/t", "measured with ENV 255"),
 "2-6": ("filter", "1/4T", 2.5, "free", "a 7.5 Hz pitch ripple is the LFO's 3rd harmonic"),
 "2-7": ("filter", "1/8", 3.333, "free", "its pitch ripple is the filter's pull"),
 "2-8": ("filter", "1/16.", 4.444, "free", ""),
 "3-6": ("filter", "1/4", 1.667, "free", "first suspected to be a chorus harmonic"),
 "3-8": ("pitch", "1/16.", 4.444, "free", ""),
 "4-1": ("pulse width", "1/2T", 1.25, "free", ""),
 "4-2": None, "4-3": ("pulse width", "1/2.", 0.556, "free", ""),
 "4-4": ("pitch, 145 cents", "1/8T", 5.0, "free", ""),
 "4-5": None, "4-6": None,
 "5-1": ("pulse width", "1/4T", 2.5, "free", ""),
 "5-2": ("pitch", "1/16.", 4.444, "free", ""),
 "5-3": ("pulse width", "1/2", 0.833, "free", "first read at 2.59 Hz, a chorus product"),
 "5-4": ("pulse width", "1/8", 3.333, "free", "the spreadsheet lists no LFO"),
 "5-5": None,
 "5-6": ("pulse width, pitch", "1/16.", 4.444, "restarts", "restarts only when no other key is held; the voices share it; the pitch swing may be the PWM's own phase motion"),
 "5-7": ("filter", "1/8T", 5.0, "free", ""),
 "5-8": ("filter or pulse width", "1/2.", 0.556, "free", "first misread as restarting"),
 "6-2": ("pitch", "1/8T", 5.0, "free", ""),
 "6-3": ("audio-rate modulation (filter, per Standing)", "1/128", 53.33, "restarts", "the ring-modulator timbre; it changes with the tempo"),
 "6-4": ("filter", "1/16.", 4.444, "free", ""),
 "6-5": ("filter", "1/8T", 5.0, "free", ""),
 "6-7": ("pitch", "1/8T", 5.0, "free", ""),
 "6-8": ("filter, heard as pitch", "1/8", 3.333, "free", "the filter rings: its LFO sounds as vibrato"),
 "7-1": ("pulse width", "1/8.", 2.222, "free", ""),
 "7-2": ("pitch, pulse width ?", "1/4T", 2.5, "free", "the spreadsheet lists no LFO; a 6-cent vibrato; the even harmonics move at twice its rate"),
 "7-3": ("pitch, pulse width ?", "1/16.", 4.444, "free", "Standing: vibrato, saw without PWM; with the filter open its even harmonics and brightness still swing"),
 "7-4": ("pulse width", "1/8.", 2.222, "free", ""),
 "7-5": ("pitch", "1/32.", 8.889, "free", ""),
 "7-6": ("filter, pitch", "1/4T", 2.5, "free", ""),
 "7-7": ("filter", "1/8", 3.333, "free", "delay hidden by the filter envelope"),
 "7-8": ("filter", "1/1T", 0.625, "free", "a whole-note triplet"),
 "8-1": ("filter, pitch", "1/2.", 0.556, "free", ""),
 "8-2": ("filter, pulse width", "1/2T", 1.25, "free", "hidden by its nearly open FILTER (251)"),
 "8-3": ("filter, pitch", "1/2", 0.833, "free", "first misread as a 2.53 Hz vibrato"),
 "8-4": ("filter, pitch", "1/1T", 0.625, "free", "a whole-note triplet"),
 "8-6": ("pitch", "1/8T", 5.0, "free", ""),
 "8-7": ("filter, sample and hold", "1/16.", 4.444, "restarts", "tested at 150 BPM (6.67 Hz)"),
 "8-8": ("filter", "1/32", 13.333, "restarts", "a 1/32 at 60, 70 and 100 BPM"),
}
NOTE_NONE = {"1-5": "a 3.26 Hz reading is chorus I's 6th harmonic",
             "4-2": "Standing: wide filter LFO at low FILTER; not tested there",
             "4-5": "Standing: slight vibrato; none found",
             "4-6": "Standing: vibrato with delay; none found",
             "5-5": "Standing: fast filter LFO; its jitter is the noisy source"}
DELAY_NOTE = {"4-4": "under 0.2", "7-7": "?", "8-3": "?", "6-4": "?", "2-7": "0.67"}
def f(x, nd=0):
    try:
        v = float(x); return f"{v:.{nd}f}"
    except (TypeError, ValueError):
        return ""
OSC = {"6-8": "noise through a ringing filter", "6-3": "square, modulated at 53 Hz",
       "4-3": "pulse, PWM (averages to a saw spectrum)", "5-6": "pulse, PWM (averages to a saw spectrum)",
       "7-1": "pulse, PWM (averages to a saw spectrum), +1 oct, sub +3 dB", "7-4": "pulse, PWM (averages to a saw spectrum), +1 oct, sub -2 dB",
       "4-1": "saw spectrum (Standing: PWM), +1 oct, sub -3 dB", "5-8": "saw spectrum (Standing: PWM), +1 oct, sub +3 dB",
       "3-5": "saw spectrum (Standing: envelope PWM)", "6-1": "saw spectrum (Standing: envelope PWM)",
       "8-5": "saw spectrum (Standing: envelope PWM), sub -13 dB"}
def db0(x):
    v = round(float(x))
    return f"{0 if v == 0 else v:+d}" if False else str(0 if v == 0 else v)
def osc(s):
    if s in OSC: return OSC[s]
    r = m[s]; w = r["wave"]
    if w.startswith("pulse ~"):
        w = f"pulse {round(float(w.split('~')[1]) * 100)} %"
    elif w.startswith("pulse/mix"):
        w = "mixed"
    parts = [w]
    if r["osc_octave"] == "1": parts[0] += ", +1 oct"
    if r["osc_octave"] == "-1": parts[0] += ", -1 oct"
    if r["sub_db"] and float(r["sub_db"]) > -15:
        v = round(float(r["sub_db"]))
        parts.append("sub, same level" if v == 0 else f"sub {v:+d} dB")
    nd = float(r["noise_db"]) if r["noise_db"] else -99
    if nd > -28 and s not in ("4-4", "5-6"): parts.append("noise")
    return ", ".join(parts)
def env(s):
    r = m[s]
    a = f(r["amp_attack_ms"])
    if r["amp_sustain_db"]:
        rel = f(r["amp_release_-20dB_ms"])
        return f"{a} ms / {db0(r['amp_sustain_db'])} dB / {rel} ms" if rel else f"{a} ms / {db0(r['amp_sustain_db'])} dB / -"
    dec = r["amp_decay_to_-20dB_ms"] or r["env000_decay_to_-20dB_ms"]
    return f"{a} ms / pluck: -20 dB in {f(dec)} ms" if dec else f"{a} ms / pluck"
def delay(s):
    if s in DELAY_NOTE: return DELAY_NOTE[s]
    ds = [float(m[s][k + "_delay_s"]) for k in ("vibrato", "filter_lfo", "pwm") if m[s][k + "_delay_s"]]
    ds = [x for x in ds if x > 0]
    return f"{max(ds):.2f}" if ds else ""
rows = []
for b in range(1, 9):
    for n in range(1, 9):
        s = f"{b}-{n}"; r = m[s]
        ch = r["chorus"] if r["chorus"] != "on" else "on"
        g = r["glide_ms"]
        glide = "-" if g in ("", None) else (f(g) if float(g) > 5 else "no")
        lf = L.get(s)
        if lf:
            what, nv, hz, phase, note = lf
            rate = f"{nv} ({hz:g} Hz)" if nv and hz else (nv or "?")
            dl = delay(s) if s in DELAY_NOTE or delay(s) else "-"
        else:
            what, rate, phase, dl, note = "none", "-", "-", "-", NOTE_NONE.get(s, "")
        name = comp[s]["Name (spreadsheet)"].replace("|", "/")
        rows.append(f"| {s} | {name} | {osc(s)} | {ch} | {env(s)} | {glide} | {what} | {rate} | {phase} | {dl} | {d[s]['FILTER']} / {d[s]['RESONANCE']} / {d[s]['ATTACK']} | {note} |")
print("| Sound | Name (Standing) | Oscillator | Chorus | Attack / sustain / release | Glide (ms) | LFO moves | LFO rate at 100 BPM | LFO phase | LFO delay (s) | FILTER / RES / ATTACK | Notes |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
print("\n".join(rows))
