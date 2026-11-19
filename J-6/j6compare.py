#!/usr/bin/env python3
"""Build the comparison workbook: the reference spreadsheet's judgements beside
the measured values, with harvested defaults and method notes.

  python3 j6compare.py results/measurements.csv results/defaults.csv \
      REFERENCE.xlsx results/J6_sounds_measured.xlsx

REFERENCE.xlsx is "Roland J-6 Preset Sounds Settings Ver. 1.0", produced by
Nick Standing at JabunAudio; its values are quoted for comparison only, with
this citation in the workbook. Needs openpyxl. Agreement flags are formulas:
open the result in a spreadsheet application to see them computed.
"""
import csv, re, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

meas_csv, defaults_csv, sheet_xlsx, out = sys.argv[1:5]
meas = {r["sound"]: r for r in csv.DictReader(open(meas_csv))}
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
    ("Name (spreadsheet)", "name", None, None, 34, "Grey columns quote the reference spreadsheet for comparison: 'Roland J-6 Preset Sounds Settings Ver. 1.0', produced by Nick Standing at JabunAudio. This column is the text before the colon in its Notes column."),
    ("Modulation measurable", "modok", None, None, 12, "'no' when the long note decays before 1.5 s (plucks): LFO, PWM and chorus cannot be measured from these takes."),
    ("Chorus (sheet)", "sheet", "chorus", None, 9, None),
    ("Chorus (measured)", "meas", "chorus", None, 10, "I or II from the rate at which the stereo difference/sum energy ratio pulses (1.09 Hz for I, 1.76 Hz for II); Off when the channels are identical; 'on' when chorus is present but the rate is unclear."),
    ("Chorus agree", "f_chorus", None, None, 9, None),
    ("Glide (sheet)", "sheet", "glide", None, 9, None),
    ("Glide settle (ms)", "meas", "glide_ms", "0", 10, "Time from the moment the E3 note dominates until its pitch stays within 30 cents of E. Counted only if the pitch passes through intermediate values; 0 means it jumped. Each voice glides from the last pitch it played."),
    ("Glide agree", "f_glide", None, None, 9, None),
    ("DCO LFO (sheet)", "sheet", "dco_lfo", None, 9, None),
    ("Vibrato (Hz)", "meas", "vibrato_hz", "0.00", 9, "Rate of an in-phase pitch modulation of the A2 note (open-filter pass)."),
    ("Vibrato p95-p5 (cents)", "meas", "vibrato_swing", "0", 10, "Peak-to-peak pitch swing of the band-limited modulation."),
    ("Vibrato delay (s)", "meas", "vibrato_delay_s", "0.00", 9, "Time until the vibrato reaches half its final depth."),
    ("Vibrato agree", "f_vib", None, None, 9, None),
    ("VCF LFO (sheet)", "sheet", "vcf_lfo", None, 9, None),
    ("Filter LFO (Hz)", "meas", "filter_lfo_hz", "0.00", 9, "Rate of an in-phase brightness (spectral centroid) modulation, default pass."),
    ("Filter LFO p95-p5 (octaves)", "meas", "filter_lfo_swing", "0.00", 10, None),
    ("Filter LFO agree", "f_flfo", None, None, 9, None),
    ("PWM (sheet)", "sheet", "pwm", None, 8, None),
    ("PWM LFO (Hz)", "meas", "pwm_hz", "0.00", 9, "Rate of an in-phase modulation of the even harmonics' share of energy, open-filter pass."),
    ("LFO flags", "meas", "lfo_flags", None, 28, "A detection on a harmonic of the chorus LFO (about 0.545 Hz for I, 0.88 Hz for II) may be the chorus rather than an LFO."),
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
    ("Key tracking (measured)", "meas", "key_tracking", "0.00", 9, "Brightness relative to pitch, A4 against A2, two octaves apart: 1 = cutoff follows the keyboard fully, 0 = fixed cutoff. Approximate."),
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
summary["A2"] = "Reference, quoted for comparison: 'Roland J-6 Preset Sounds Settings Ver. 1.0', produced by Nick Standing at JabunAudio. Measurements: recordings of a factory-reset J-6 on system program 1.02, see Method."
summary["A2"].font = FONT
hdr = ["Attribute", "Agree", "Disagree", "Not measurable", "Agreement"]
for c, h in enumerate(hdr, 1):
    cell = summary.cell(row=4, column=c, value=h); cell.font, cell.fill = BOLD, HEAD
for i, (name, col) in enumerate((("Chorus I / II / Off", "Chorus agree"), ("Glide yes / no", "Glide agree"),
                                 ("Vibrato (DCO LFO) yes / no", "Vibrato agree"), ("Filter LFO yes / no", "Filter LFO agree")), 5):
    rng = f"Comparison!${L(col)}$2:${L(col)}${last}"
    summary.cell(row=i, column=1, value=name)
    summary.cell(row=i, column=2, value=f'=COUNTIF({rng},"yes")')
    summary.cell(row=i, column=3, value=f'=COUNTIF({rng},"no")')
    summary.cell(row=i, column=4, value=f'=COUNTIF({rng},"n/a")')
    summary.cell(row=i, column=5, value=f'=IF(B{i}+C{i}=0,"",B{i}/(B{i}+C{i}))').number_format = "0%"
    for c in range(1, 6): summary.cell(row=i, column=c).font = FONT
notes = [
    "Agreement is counted only where both sources say something comparable. 'Not measurable' marks plucks whose long note decays before modulation can be measured.",
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
    ("Passes: default (each sound's harvested FILTER, RESONANCE, ENV 128, ATTACK; but recorded with ATTACK 0, see caveats), open (FILTER 255, RESONANCE 0, own ATTACK), env000 and env255 ([ENVELOPE] at 0 and 255).", False),
    ("Delay and reverb levels were 0 in every pass. Pattern tempo 100 BPM.", False),
    ("Alignment: the first note's onset is found from the audio, because the recorder's start-up varies by tens of milliseconds; the notes' relative timing is exact.", False),
    ("", False),
    ("Caveats", True),
    ("The default pass was recorded with ATTACK 0 for all sounds, so attack times come from the open pass, whose patterns carry each sound's own ATTACK.", False),
    ("The env000 and env255 passes were recorded in chord mode: valid for envelope levels and times, not for spectra or pitch.", False),
    ("The J-6 ignores All Sound Off, so with [ENVELOPE] at 255 a sound can still ring when the next take starts; those releases are measured only down to that floor.", False),
    ("Octave and sub-oscillator are ambiguous for mixed waveforms: a square plus a saw at one pitch has the same harmonic magnitudes as a sub-oscillator plus a saw an octave up.", False),
    ("LFO detection needs a long note: plucks that decay within about 1.5 s get no LFO, PWM or chorus measurement. The chorus produces modulation at its own rate's harmonics; detections on them are flagged.", False),
    ("Glide is polyphonic: each voice glides from the last pitch it played, so only the settle time is comparable between sounds.", False),
    ("[ENVELOPE] acts on decay, sustain and release together; at 255 every pluck sustains (see the ENV 0 / ENV 255 sustain columns).", False),
    ("", False),
    ("Sources", True),
    ("Reference spreadsheet (grey columns of the Comparison sheet, quoted for comparison): 'Roland J-6 Preset Sounds Settings Ver. 1.0', produced by Nick Standing at JabunAudio.", False),
    ("J-6 Owner's Manual v1.02, Top Panel: https://static.roland.com/manuals/J-6_manual_v102/eng/26654326.html", False),
    ("J-6 Owner's Manual v1.02, Backup/Restore: https://static.roland.com/manuals/J-6_manual_v102/eng/26654319.html", False),
    ("Tools and procedure: https://github.com/liotier/RolandStuff/tree/claude/affectionate-franklin-t1cy4x/J-6", False),
]
for i, (t, bold) in enumerate(lines, 1):
    method.cell(row=i, column=1, value=t).font = BOLD if bold else FONT
method.column_dimensions["A"].width = 150
wb.save(out)
print("saved", out)
