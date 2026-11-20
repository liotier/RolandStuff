#!/usr/bin/env python3
"""Build the comparison workbook: the reference spreadsheet's judgements beside
the measured values, with harvested defaults and method notes.

  python3 j6compare.py results/measurements.csv results/defaults.csv \
      REFERENCE.xlsx results/J6_sounds_measured.xlsx

REFERENCE.xlsx is Nick Standing (JabunAudio), "Roland J-6 Preset Sounds
Settings Ver. 1.0", published with the video "Roland AIRA Compact J-6
Comprehensive Preset Sounds Patch Sheet! (Free download or donation)",
https://www.youtube.com/watch?v=z6hoNwWadR8. Its values are quoted for
comparison only, with this citation in the workbook. Needs openpyxl.
Agreement flags are formulas: open the result in a spreadsheet application.
"""
import csv, re, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

meas_csv, defaults_csv, sheet_xlsx, out = sys.argv[1:5]
meas = {r["sound"]: r for r in csv.DictReader(open(meas_csv))}
# Experiment results from j6experiments.py, when present beside the measurements
from pathlib import Path
res_dir = Path(meas_csv).parent
# Chorus modes from the opposite-phase test (j6experiments.py chorus), when present
_chorus_csv = Path(meas_csv).parent / "chorus.csv"
if _chorus_csv.exists():
    for _r in csv.DictReader(open(_chorus_csv)):
        if _r["verdict"] in ("I", "II", "fast", "Off") and _r["sound"] in meas:
            meas[_r["sound"]]["chorus"] = _r["verdict"]
keysync, ftrack = {}, {}
if (res_dir / "keysync.csv").exists():
    rank = {"restarts with each note": 0, "free-running": 1, "unclear": 2, "no LFO found": 3}
    for r in csv.DictReader(open(res_dir / "keysync.csv")):
        old = keysync.get(r["sound"])
        if old is None or rank[r["verdict"]] < rank[old["verdict"]]:
            keysync[r["sound"]] = r
# The closing pass (keysync2) settles sounds keysync left unclear: its
# decisive verdicts replace those, at 100 BPM when there is one.
if (res_dir / "keysync2.csv").exists():
    decisive = ("restarts with each note", "free-running")
    for r in csv.DictReader(open(res_dir / "keysync2.csv")):
        old = keysync.get(r["sound"])
        if r["verdict"] in decisive and (old is None or old["verdict"] not in decisive
                                         or (old.get("tempo_bpm") not in ("100", "100.0") and r["tempo_bpm"] == "100.0")):
            keysync[r["sound"]] = r
    # two measurements of one sound's LFO that disagree are reported as such
    rows2 = list(csv.DictReader(open(res_dir / "keysync2.csv")))
    for lab in {r["sound"] for r in rows2}:
        for bpm in {r["tempo_bpm"] for r in rows2 if r["sound"] == lab}:
            mine = [r for r in rows2 if r["sound"] == lab and r["tempo_bpm"] == bpm and r["verdict"] in decisive]
            if len({r["verdict"] for r in mine}) == 2:
                keysync[lab] = dict(mine[0], verdict="conflicting: " + "; ".join(
                    f"{r['measurement']} {r['verdict']}" for r in mine))
# keysync3 (8 s notes, measured past the envelope) has the last word on the
# sounds it tested: its decisive verdicts replace earlier ones, conflicts too
if (res_dir / "keysync3.csv").exists():
    for r in csv.DictReader(open(res_dir / "keysync3.csv")):
        if r["verdict"] in ("restarts with each note", "free-running") and r.get("tempo_bpm") in ("100", "100.0"):
            old = keysync.get(r["sound"])
            if old is None or old.get("source") != "keysync3" or (r["verdict"] == "free-running" and old["verdict"] != "free-running"):
                keysync[r["sound"]] = dict(r, source="keysync3")
# Sounds whose long notes show nothing but chorus harmonics have no LFO
if (res_dir / "longnote.csv").exists():
    ln = list(csv.DictReader(open(res_dir / "longnote.csv")))
    for lab in {r["sound"] for r in ln}:
        mine = [r for r in ln if r["sound"] == lab]
        if all(not r["measurement"] or r["chorus_harmonic"] for r in mine):
            keysync[lab] = {"sound": lab, "verdict": "no LFO: chorus harmonics only (0.25-18 Hz, 20 s notes)",
                            "rate_hz": "", "nearest_note_value": ""}
if (res_dir / "filters_summary.csv").exists():
    ftrack = {r["sound"]: r for r in csv.DictReader(open(res_dir / "filters_summary.csv"))}
harv = {r["sound"]: r for r in csv.DictReader(open(defaults_csv))}
src = openpyxl.load_workbook(sheet_xlsx).worksheets[0]
keys = "glide octave rate delay dco_lfo pwm pulse saw sub noise hpf freq res env vcf_lfo kybd vca A D preset2 S R chorus notes".split()
sheet = {}
for row in src.iter_rows(values_only=True):
    if row[0] and re.match(r"^\s*\d\s*-\s*\d\s*$", str(row[0])):
        sheet[re.sub(r"\s", "", str(row[0]))] = dict(zip(keys, row[1:25]))
order = [f"{b}-{n}" for b in range(1, 9) for n in range(1, 9)]

FONT = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
HEAD = PatternFill("solid", fgColor="DDE4EE")
SHEETF = PatternFill("solid", fgColor="F3F3F3")
thin = Side(style="thin", color="BBBBBB")

def num(v):
    if v in (None, ""):
        return None
    try:
        x = float(v)
        return int(x) if x.is_integer() else x
    except ValueError:
        return v

def txt(v):
    return None if v is None else (str(v).strip() if not isinstance(v, (int, float)) else v)

wb = openpyxl.Workbook()
summary = wb.active; summary.title = "Summary"
comp = wb.create_sheet("Comparison")
msheet = wb.create_sheet("Measurements")
dsheet = wb.create_sheet("Defaults")
method = wb.create_sheet("Method")

# ---------------- Comparison ----------------
cols = [  # (header, source, key, number format, width, comment)
    ("Sound", "label", None, None, 7, None),
    ("Name (spreadsheet)", "name", None, None, 34, "Grey columns quote the reference spreadsheet for comparison: Nick Standing (JabunAudio), 'Roland J-6 Preset Sounds Settings Ver. 1.0', patch sheet published with the video 'Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet! (Free download or donation)', https://www.youtube.com/watch?v=z6hoNwWadR8. This column is the text before the colon in its Notes column."),
    ("Modulation measurable", "modok", None, None, 12, "'no' when no take of the sound lasts 1.5 s. Plucks are measured on the env255 pass, where [ENVELOPE] at 255 makes them sustain."),
    ("Chorus (sheet)", "sheet", "chorus", None, 9, None),
    ("Chorus (measured)", "meas", "chorus", None, 10, "I (LFO at 0.543 Hz), II (0.879 Hz) or fast (7.57 Hz), from the rate at which the two channels move in opposite phase (chorus.csv); Off when the channels are identical."),
    ("Chorus agree", "f_chorus", None, None, 9, None),
    ("Glide (sheet)", "sheet", "glide", None, 9, None),
    ("Glide settle (ms)", "meas", "glide_ms", "0", 10, "Time from the moment the E3 note dominates until its pitch stays within 30 cents of E. Counted only if the pitch passes through intermediate values; 0 means it jumped. Each voice glides from the last pitch it played."),
    ("Glide agree", "f_glide", None, None, 9, None),
    ("DCO LFO (sheet)", "sheet", "dco_lfo", None, 9, None),
    ("Vibrato (Hz)", "meas", "vibrato_hz", "0.00", 9, "Rate of an in-phase pitch modulation of the A2 note (open-filter pass)."),
    ("Vibrato p95-p5 (cents)", "meas", "vibrato_swing", "0", 10, "Peak-to-peak pitch swing of the band-limited modulation."),
    ("Vibrato note at 100 BPM", "meas", "vibrato_note", None, 9, "Note value whose repetition rate at the patterns' 100 BPM matches the measured rate (1/8. = dotted eighth, 1/4T = quarter triplet). Every LFO detected matches one: the J-6's LFOs follow the tempo."),
    ("Vibrato agree", "f_vib", None, None, 9, None),
    ("VCF LFO (sheet)", "sheet", "vcf_lfo", None, 9, None),
    ("Filter LFO (Hz)", "meas", "filter_lfo_hz", "0.00", 9, "Rate of an in-phase brightness (spectral centroid) modulation, default pass."),
    ("Filter LFO p95-p5 (octaves)", "meas", "filter_lfo_swing", "0.00", 10, None),
    ("Filter LFO note at 100 BPM", "meas", "filter_lfo_note", None, 9, None),
    ("Filter LFO agree", "f_flfo", None, None, 9, None),
    ("PWM (sheet)", "sheet", "pwm", None, 8, None),
    ("PWM LFO (Hz)", "meas", "pwm_hz", "0.00", 9, "Rate of an in-phase modulation of the even harmonics' share of energy, open-filter pass."),
    ("PWM note at 100 BPM", "meas", "pwm_note", None, 9, None),
    ("Delay (sheet)", "sheet", "delay", None, 8, None),
    ("LFO delay (s)", "lfodelay", None, "0.00", 9, "Longest of the vibrato, filter LFO and PWM delays: time from the note-on until the modulation reaches half the depth it has later in the note. Delays shorter than one LFO cycle read 0; a strong onset transient in the same measurement (a filter envelope sweep) can hide a delay. Empty when no LFO was detected."),
    ("Delay agree", "f_delay", None, None, 9, None),
    ("LFO phase at note-on", "ks_verdict", None, None, 14, "From seven or eight A2 notes at irregular spacing (keysync and closing experiments, sounds with an LFO that sustain): 'restarts with each note' when the LFO's phase is the same at every note-on, 'free-running' when it is the same against the clock. 'no LFO' when a 20 s note shows only harmonics of the chorus LFO. Empty: not tested."),
    ("LFO rate across notes (Hz)", "ks_rate", None, "0.000", 10, "Rate at which the seven notes' phases agree, to about 0.1 %: the LFO's exact rate. Where it differs from the rate columns, those sit at the edge of a band excluded around the chorus (see LFO flags)."),
    ("LFO note value", "ks_note", None, None, 8, "Nearest note value at the pattern tempo (100 BPM; 8-7 tested at 150 BPM)."),
    ("LFO flags", "meas", "lfo_flags", None, 28, "The chorus LFO (about 0.545 Hz for I, 0.88 Hz for II) is free-running and shows at its harmonics. Detections on one of them that match no note value were dropped; those listed here match a note value and are kept."),
    ("Pulse (sheet)", "sheet", "pulse", None, 8, None),
    ("Saw (sheet)", "sheet", "saw", None, 7, None),
    ("Waveform (measured)", "meas", "wave", None, 16, "From the harmonic levels of the A4 note, open-filter pass, averaged over the note. 'pulse ~d' gives the duty cycle d that fits the 2nd/1st harmonic ratio for a pure pulse; a saw mixed with a pulse also lands there."),
    ("Octave (sheet)", "sheet", "octave", None, 8, None),
    ("Oscillator octave (measured)", "meas", "osc_octave", "0", 10, "Octave of the oscillator against the played note. Ambiguous for mixed waveforms: a square plus a saw at one pitch has the same harmonic magnitudes as a sub-oscillator plus a saw an octave up."),
    ("Sub (sheet)", "sheet", "sub", None, 7, None),
    ("Sub level (dB re oscillator)", "meas", "sub_db", "0.0", 10, "Component one octave below the oscillator, following a square wave's 1/3, 1/5 law; empty when absent."),
    ("Noise (sheet)", "sheet", "noise", None, 8, None),
    ("Noise share (dB)", "meas", "noise_db", "0.0", 9, "Energy between harmonics relative to energy on them, A4 note, open-filter pass. Around -30 dB means no noise; above about -26 dB, noise. Strong vibrato also raises it."),
    ("A (sheet)", "sheet", "A", None, 7, None),
    ("Attack to -3 dB (ms)", "meas", "amp_attack_ms", "0", 9, "Open-filter pass (its patterns carry each sound's own ATTACK), 50 ms smoothed level."),
    ("S (sheet)", "sheet", "S", None, 16, None),
    ("Sustain (dB re peak)", "meas", "amp_sustain_db", "0.0", 9, "Level 5.5-5.95 s into the 6 s note, relative to its peak; empty when it decays to silence."),
    ("R (sheet)", "sheet", "R", None, 7, None),
    ("Release to -20 dB (ms)", "meas", "amp_release_-20dB_ms", "0", 9, "After the 6 s note's note-off; empty when the note had already decayed."),
    ("Freq (sheet)", "sheet", "freq", None, 8, None),
    ("FILTER default (0-255)", "harv", "FILTER", "0", 9, "Harvested from the J-6: the value choosing the sound writes into a pattern."),
    ("Res (sheet)", "sheet", "res", None, 7, None),
    ("RESONANCE default (0-255)", "harv", "RESONANCE", "0", 10, "Harvested from the J-6."),
    ("ATTACK default (0-255)", "harv", "ATTACK", "0", 9, "Harvested from the J-6 (SHIFT + [ENVELOPE])."),
    ("Kybd (sheet)", "sheet", "kybd", None, 7, None),
    ("Key tracking (measured)", "meas", "key_tracking", "0.00", 9, "Brightness relative to pitch, A4 against A2, two octaves apart: 1 = cutoff follows the keyboard fully, 0 = fixed cutoff. Approximate: on a sound whose filter is open the brightness follows the oscillator, not the cutoff (4-4 reads 0.63 here, 0.0 in the filter sweep)."),
    ("Key tracking, filter sweep", "ftrack", None, "0.00", 9, "Octaves of cutoff per octave of pitch, from the resonant peak at notes A1 to A4 over a FILTER sweep at RESONANCE 255 (filters experiment, four sounds)."),
    ("Velocity 40 to 127 (dB)", "meas", "velocity_40_to_127_db", "0.0", 9, "Level difference between A3 at velocity 40 and 127; 20.1 dB corresponds to level proportional to velocity squared."),
    ("Sustain, ENV 0 (dB)", "meas", "env000_sustain_db", "0.0", 9, "Sustain with [ENVELOPE] at 0 (chord-mode take: envelope only)."),
    ("Sustain, ENV 255 (dB)", "meas", "env255_sustain_db", "0.0", 9, "Sustain with [ENVELOPE] at 255 (chord-mode take: envelope only)."),
]
for c, (h, _, _, _, w, cm) in enumerate(cols, 1):
    cell = comp.cell(row=1, column=c, value=h)
    cell.font, cell.fill = BOLD, HEAD
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    if cm:
        cell.comment = Comment(cm, "measurement")
    comp.column_dimensions[get_column_letter(c)].width = w
comp.row_dimensions[1].height = 54
colidx = {h: i for i, (h, *_) in enumerate(cols, 1)}
L = lambda h: get_column_letter(colidx[h])
for r_i, lab in enumerate(order, 2):
    s, m, hv = sheet[lab], meas[lab], harv[lab]
    modok = "no" if (m.get("lfo_flags") or "") == "note too short to measure modulation" else "yes"
    for c, (h, kind, key, fmt, _, _) in enumerate(cols, 1):
        cell = comp.cell(row=r_i, column=c)
        if kind == "label": cell.value = lab
        elif kind == "name": cell.value = str(s["notes"]).split(":")[0].strip()
        elif kind == "modok": cell.value = modok
        elif kind == "sheet": cell.value = txt(s[key]); cell.fill = SHEETF
        elif kind == "meas":
            v = m.get(key)
            if key == "lfo_flags" and v == "note too short to measure modulation": v = None
            cell.value = num(v)
        elif kind == "harv": cell.value = num(hv[key])
        elif kind == "ks_verdict": cell.value = keysync[lab]["verdict"] if lab in keysync else None
        elif kind == "ks_rate":
            ks = keysync.get(lab)
            cell.value = num(ks["rate_hz"]) if ks and ks["verdict"].startswith(("free-running", "restarts", "conflicting")) else None
        elif kind == "ks_note":
            ks = keysync.get(lab)
            cell.value = ks["nearest_note_value"] if ks and ks["verdict"].startswith(("free-running", "restarts", "conflicting")) else None
        elif kind == "ftrack": cell.value = num(ftrack[lab]["key_tracking"]) if lab in ftrack else None
        elif kind == "lfodelay":
            ds = [num(m.get(f"{k}_delay_s")) for k in ("vibrato", "filter_lfo", "pwm")]
            ds = [d for d in ds if isinstance(d, (int, float))]
            cell.value = max(ds) if ds else None
        elif kind == "f_delay":
            ok = f"{L('Modulation measurable')}{r_i}"
            sd, md = f"{L('Delay (sheet)')}{r_i}", f"{L('LFO delay (s)')}{r_i}"
            cell.value = f'=IF(OR({ok}="no",{md}=""),"n/a",IF(({sd}="Y")=({md}>0),"yes","no"))'
        elif kind == "f_chorus":
            sc, mc = f"{L('Chorus (sheet)')}{r_i}", f"{L('Chorus (measured)')}{r_i}"
            cell.value = f'=IF({mc}="","n/a",IF(OR({mc}={sc},AND({mc}="on",{sc}<>"Off")),"yes","no"))'
        elif kind == "f_glide":
            sg, mg = f"{L('Glide (sheet)')}{r_i}", f"{L('Glide settle (ms)')}{r_i}"
            cell.value = f'=IF({mg}="","n/a",IF(({sg}<>"x")=({mg}>5),"yes","no"))'
        elif kind in ("f_vib", "f_flfo"):
            sk, mk = (("DCO LFO (sheet)", "Vibrato (Hz)") if kind == "f_vib" else ("VCF LFO (sheet)", "Filter LFO (Hz)"))
            ok = f"{L('Modulation measurable')}{r_i}"
            sv, mv = f"{L(sk)}{r_i}", f"{L(mk)}{r_i}"
            cell.value = f'=IF({ok}="no","n/a",IF(({sv}<>"x")=({mv}<>""),"yes","no"))'
        cell.font = FONT
        if fmt and isinstance(cell.value, (int, float)): cell.number_format = fmt
comp.freeze_panes = "C2"
last = len(order) + 1

# ---------------- Summary ----------------
summary["A1"] = "J-6 preset sounds: measured against the reference spreadsheet"; summary["A1"].font = Font(name="Arial", size=12, bold=True)
summary["A2"] = "Reference, quoted for comparison: Nick Standing (JabunAudio), 'Roland J-6 Preset Sounds Settings Ver. 1.0', patch sheet published with the video 'Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet! (Free download or donation)', https://www.youtube.com/watch?v=z6hoNwWadR8. Measurements: recordings of a factory-reset J-6 on system program 1.02, see Method."
summary["A2"].font = FONT
hdr = ["Attribute", "Agree", "Disagree", "Not measurable", "Agreement"]
for c, h in enumerate(hdr, 1):
    cell = summary.cell(row=4, column=c, value=h); cell.font, cell.fill = BOLD, HEAD
for i, (name, col) in enumerate((("Chorus I / II / Off", "Chorus agree"), ("Glide yes / no", "Glide agree"),
                                 ("Vibrato (DCO LFO) yes / no", "Vibrato agree"), ("Filter LFO yes / no", "Filter LFO agree"),
                                 ("LFO delay yes / no", "Delay agree")), 5):
    rng = f"Comparison!${L(col)}$2:${L(col)}${last}"
    summary.cell(row=i, column=1, value=name)
    summary.cell(row=i, column=2, value=f'=COUNTIF({rng},"yes")')
    summary.cell(row=i, column=3, value=f'=COUNTIF({rng},"no")')
    summary.cell(row=i, column=4, value=f'=COUNTIF({rng},"n/a")')
    summary.cell(row=i, column=5, value=f'=IF(B{i}+C{i}=0,"",B{i}/(B{i}+C{i}))').number_format = "0%"
    for c in range(1, 6): summary.cell(row=i, column=c).font = FONT
notes = [
    "Agreement is counted only where both sources say something comparable. 'Not measurable' marks plucks whose long note decays before modulation can be measured, and for the delay, sounds where no LFO was detected.",
    "Continuous attributes (attack, sustain, release, cutoff, resonance, sub level, noise) are listed side by side on the Comparison sheet without a score: the spreadsheet's words (Low, Mid, Fast...) have no defined boundaries.",
    "Spreadsheet columns are shaded grey on the Comparison sheet; hover over a header for the measurement's definition.",
]
for i, n in enumerate(notes, 11):
    summary.cell(row=i, column=1, value=n).font = FONT
summary.column_dimensions["A"].width = 30
for c in "BCDE": summary.column_dimensions[c].width = 14

# ---------------- Measurements ----------------
mkeys = list(next(iter(meas.values())).keys())
for c, k in enumerate(mkeys, 1):
    cell = msheet.cell(row=1, column=c, value=k); cell.font, cell.fill = BOLD, HEAD
    msheet.column_dimensions[get_column_letter(c)].width = max(10, min(len(k) + 2, 26))
for r_i, lab in enumerate(order, 2):
    for c, k in enumerate(mkeys, 1):
        cell = msheet.cell(row=r_i, column=c, value=num(meas[lab][k])); cell.font = FONT
msheet.freeze_panes = "B2"

# ---------------- Defaults ----------------
dh = ["Sound", "FILTER", "RESONANCE", "ENV", "ATTACK", "FILTER (% of range)", "RESONANCE (% of range)", "ATTACK (% of range)"]
for c, h in enumerate(dh, 1):
    cell = dsheet.cell(row=1, column=c, value=h); cell.font, cell.fill = BOLD, HEAD
    dsheet.column_dimensions[get_column_letter(c)].width = 13 if c < 6 else 20
dsheet["J1"] = "Range maximum"; dsheet["J1"].font = BOLD
dsheet["K1"] = 255; dsheet["K1"].font = Font(name="Arial", size=10, color="0000FF")
dsheet["K1"].comment = Comment("Knob values in the J-6's pattern files run from 0 to 255 (observed in backups).", "measurement")
for r_i, lab in enumerate(order, 2):
    hv = harv[lab]
    vals = [lab, num(hv["FILTER"]), num(hv["RESONANCE"]), num(hv["ENV"]), num(hv["ATTACK"])]
    for c, v in enumerate(vals, 1):
        dsheet.cell(row=r_i, column=c, value=v).font = FONT
    for c, src_col in ((6, "B"), (7, "C"), (8, "E")):
        cell = dsheet.cell(row=r_i, column=c, value=f"={src_col}{r_i}/$K$1"); cell.number_format = "0%"; cell.font = FONT
dsheet.freeze_panes = "B2"
dsheet["A67"] = "Source: one backup of a factory-reset J-6 (v1.02) after giving pattern n sound n on the panel; reference sounds 1-3 and 1-4 match values observed separately."
dsheet["A67"].font = FONT

# ---------------- Method ----------------
lines = [
    ("Method", True),
    ("Instrument: Roland J-6, system program 1.02, factory reset. USB audio recorded at its native 44.1 kHz, 24-bit stereo.", False),
    ("Stimulus per sound: A2 held 6 s, A2 staccato 0.15 s, A4 1.5 s, A2 then E3 (glide), A3 at velocity 40 and 127. Chord mode off: incoming notes play single notes.", False),
    ("Passes: default (each sound's harvested FILTER, RESONANCE, ENV 128 and ATTACK), open (FILTER 255, RESONANCE 0), env000 and env255 ([ENVELOPE] at 0 and 255). Pattern tempo 100 BPM.", False),
    ("Delay and reverb levels were 0 in every pass. Pattern tempo 100 BPM.", False),
    ("Alignment: the first note's onset is found from the audio, because the recorder's start-up varies by tens of milliseconds; the notes' relative timing is exact.", False),
    ("", False),
    ("Caveats", True),
    ("[CHORD] is on after every power-on; with it on, each MIDI note plays a chord. The env000 pass was recorded in chord mode and is used for envelope levels and times only.", False),
    ("The J-6 ignores All Sound Off. The env255 pass waited 10 s between patterns; previous sounds were still audible at -77 to -95 dBFS in 24 takes, negligible against notes at -25 to -45 dBFS.", False),
    ("Octave and sub-oscillator are ambiguous for mixed waveforms: a square plus a saw at one pitch has the same harmonic magnitudes as a sub-oscillator plus a saw an octave up.", False),
    ("LFO detection needs about 1.5 s of sound: plucks are measured on the env255 pass. Rates below 0.3 Hz are not detected. The analysis resolves about 0.2 Hz.", False),
    ("The LFOs follow the pattern tempo. Measured across seven notes (keysync experiment), the rates of 27 sounds' LFOs fall within 0.1 % of a note value at 100 BPM, from a whole-note triplet (0.625 Hz, 7-8 and 8-4) to a thirty-second (13.33 Hz, 8-8). In a pass at 150 BPM the 24 LFOs detected at both tempos ran 1.50 times faster (median ratio 1.502). Rates of 3.17, 2.53 and 0.53 Hz in the rate columns are artifacts: they sit at the edge of a band excluded around a chorus harmonic, and the true rate (3.33, 2.5, 0.556 or 0.625 Hz) lies inside it (flagged in LFO flags; see LFO rate across notes). The LFO delays did not follow the tempo: in the seven cases measurable at both tempos they stayed the same (median ratio 0.97, against 0.67 if they followed the tempo), so delays are set in seconds.", False),
    ("LFO delay: time from the note-on until the modulation reaches half the depth it has later in the note. Delays shorter than one LFO cycle read 0; an onset transient in the same measurement hides a delay (sound 7-7, filter LFO).", False),
    ("Glide is polyphonic: each voice glides from the last pitch it played, so only the settle time is comparable between sounds.", False),
    ("[ENVELOPE] acts on decay, sustain and release together; at 255 every pluck sustains (see the ENV 0 / ENV 255 sustain columns).", False),
    ("", False),
    ("Further experiments (results/*.csv in the repository)", True),
    ("Sample and hold: 8-7's random filter steps come at 4.44 Hz at 100 BPM and 6.67 Hz at 150 BPM, a dotted sixteenth at both: the S&H clock follows the tempo, and it restarts with each note.", False),
    ("LFO phase (keysync, closing, final and finalfinal experiments, 38 sounds, seven or eight A2 notes at irregular spacing): 33 LFOs run freely (the phase agrees against the clock, 0.90-1.00, not against the note-on); 4 restart with each note: 5-6 (4.44 Hz), 8-8 (13.33 Hz; 8.00 at 60 BPM and 9.33 at 70 BPM: a 1/32 at every tempo), 8-7's sample and hold, and 6-3's audio-rate modulation. 5-8 (0.556 Hz) runs freely: on eight 8 s notes measured from 2 s, 0.98-1.00 against the clock at 100 and 60 BPM, beside a free-running control (8-1, 1.00) and a restarting one (5-6, 1.00 against the note-on). Its earlier 'restart' reading came from the first two seconds of 3.5 s notes, where a +1.1 octave brightness spike at each note-on bends the whole-note detrending; that artifact can only make LFOs look restarting, and all other slow LFOs read free-running. 8-2's LFO (1/2T, 1.25 Hz) is hidden by its nearly open default FILTER 251: it shows at FILTER 140 and 100, and as small steps on 90 s notes at 251; it runs freely and follows the tempo. 5-5 shows nothing but harmonics of the chorus LFO, and its harmonics fluctuate 0.52 octave rms with the filter fully open against 0.56 at its defaults (8-2: 0.51 at FILTER 251, 1.33 at 140 once its LFO shows): the jitter is the source's, any filter movement under a tenth of it. 7-2 has a small free-running vibrato (6 cents, 1/4T) the spreadsheet does not list. A delay fades the depth in with each note while the phase runs on. The PWM at 4.40 Hz on 7-7 and 8-2 is the 5th harmonic of the chorus II LFO (0.879 Hz), and 2-6's 7.5 Hz pitch modulation the 3rd harmonic of its 2.5 Hz LFO.", False),
    ("One LFO per sound, shared by the voices (closing experiment, four staggered notes held together): on 6-5 (free-running) and 5-6 (restarting) the four voices' vibrato phases agree (concentration 1.00). On 5-6 the shared phase is the one the first note alone would give, within 4 degrees: the LFO restarts when a note starts from silence, not when notes are added to held ones.", False),
    ("6-3 'Square Ring Mod': its strongest component is a modulation at 53.32 Hz at 100 BPM and 31.99 Hz at 60 BPM, 32 cycles per beat (a 1/128 note), restarting with each note: the filter LFO at its maximum rate ('Max' in the spreadsheet), in the audio range. The 6.81 Hz 'filter LFO' measured earlier is a beat between its products and the note's harmonics.", False),
    ("Corrected rates (closing experiment, 20 s notes, checked at 60 BPM): 5-3 0.833 Hz (1/2, PWM and filter), 3-6 1.667 Hz (1/4), 8-3 0.833 Hz (1/2), 5-8 0.556 Hz (1/2.), 7-2 2.5 Hz (1/4T); all follow the tempo. The chorus LFO measures 0.543 Hz (chorus I) and 0.879 Hz (chorus II) on the same notes.", False),
    ("Velocity: level proportional to velocity squared (exponent 2.00, 8 to 127, four sounds); no effect on brightness.", False),
    ("Polyphony: four voices. Of six held notes entering in turn, the 2nd and 3rd are dropped when the 5th and 6th enter; the lowest note keeps sounding.", False),
    ("FILTER (sound 6-8, RESONANCE 255): the resonant peak moves one octave per 14.4 steps below 2 kHz, from about 30 Hz at 85 (A2), flattening towards 13-16 kHz; it follows the keyboard fully (1.00 octave per octave).", False),
    ("FILTER per sound (filters experiment, RESONANCE 255, notes A1 to A4, resonant peak against a FILTER 255 / RESONANCE 0 reference): the cutoff for one FILTER value differs by octaves between sounds: 1 kHz at A2 needs FILTER 158 on 6-8, 78 on 2-7, 31 on 4-6, and lies below 17 on 4-4. Keyboard tracking: 6-8 1.00, 2-7 0.50, 4-6 0.31, 4-4 0.0 (the spreadsheet marks 6-8 and 2-7 tracked, 4-6 and 4-4 not). The curve differs too: 6-8 rises one octave per 14-15 steps from 153 to 187; 4-4 and 4-6 one octave per about 31 steps near 17, steepening to 16-18 near 68-85. The 6-8 values match the earlier direct measurement of its self-oscillation within 3 %.", False),
    ("RESONANCE (sound 2-7): at 255 the resonant peak stands about 15 dB above its level at 0 and the fundamental drops 5-6 dB.", False),
    ("ATTACK (sound 2-7): rise to -3 dB under 20 ms up to 68, then doubling every 31 steps to 1.7 s at 255; release unaffected.", False),
    ("ENV (sound 1-3): 0-119 is a pluck whose decay to -20 dB lengthens from 35 to 215 ms; from 136 a sustain appears (-19 dB) and rises to -0.7 dB at 255 while the release to -20 dB lengthens from 0.3 s at 136 to 5.6 s at 221, beyond the 7.5 s measured at 238 and 255.", False),
    ("Chorus modes (chorus.csv): the chorus sweeps the two channels in opposite phase, so the left-minus-right difference of pitch and brightness shows the chorus LFO alone. It confirms the 57 sounds the first test had decided and settles the 7 it had left undecided: 1-7, 2-3, 2-6 and 5-1 use chorus I; 2-1, 4-5 and 8-7 a third mode, fast (7.57 Hz, the same at 100 and 150 BPM) and shallow, which the reference spreadsheet hears as II.", False),
    ("[ENVELOPE] (envelope.csv, every sound at ENV 0, 128 and 255): four groups. Plucks (11) sustain only past the middle of the knob; decaying tones (3) keep a faint sustain; gated sounds (18) have releases under 50 ms up to the middle; the others (32) have a release tail at the default.", False),
    ("Long releases (1-3, one note, 30 s of release): at ENV 221 the release falls 3.5 dB/s (-60 dB after 17 s); at ENV 238 and 255 it is the same, 2.27 dB/s (-60 dB after 26.4 s): the release reaches its longest at 238.", False),
    ("", False),
    ("Sources", True),
    ("Reference spreadsheet (grey columns of the Comparison sheet, quoted for comparison): Nick Standing (JabunAudio), 'Roland J-6 Preset Sounds Settings Ver. 1.0', patch sheet published with the video 'Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet! (Free download or donation)', https://www.youtube.com/watch?v=z6hoNwWadR8.", False),
    ("J-6 Owner's Manual v1.02, Top Panel: https://static.roland.com/manuals/J-6_manual_v102/eng/26654326.html", False),
    ("J-6 Owner's Manual v1.02, Backup/Restore: https://static.roland.com/manuals/J-6_manual_v102/eng/26654319.html", False),
    ("Tools and procedure: https://github.com/liotier/RolandStuff/tree/claude/affectionate-franklin-t1cy4x/J-6_presets_measurement", False),
]
for i, (t, bold) in enumerate(lines, 1):
    method.cell(row=i, column=1, value=t).font = BOLD if bold else FONT
method.column_dimensions["A"].width = 150
wb.save(out)
print("saved", out)
