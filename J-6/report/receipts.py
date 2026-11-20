"""Section 1's comparisons between the patch sheet and the measurements:
LFO rate classes, attack, release, cutoff, resonance and noise classes,
octave, saw and the agreement columns of the workbook.

  python3 report/receipts.py results table.md REFERENCE.xlsx

REFERENCE.xlsx is Nick Standing's sheet (see README.md), not distributed here;
table.md is the output of report/table.py.
"""
import openpyxl, re, statistics as st, sys
R = sys.argv[1]; T = sys.argv[2]
wb = openpyxl.load_workbook(f"{R}/J6_sounds_measured.xlsx", data_only=True)
ws = wb["Comparison"]; hdr = [c.value for c in ws[1]]
rows = [dict(zip(hdr, r)) for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]
ref = openpyxl.load_workbook(f"{sys.argv[3]}", data_only=True)["Sheet1"]
sheet = {}
for r in ref.iter_rows(min_row=7, values_only=True):
    if r[0] and re.match(r"\d - \d", str(r[0])):
        sheet[str(r[0]).replace(" ", "")] = r
# table.md: LFO rate Hz
hz = {}
for line in open(T):
    c = [x.strip() for x in line.split("|")[1:-1]]
    if len(c) > 8 and re.match(r"\d-\d$", c[0]):
        m = re.search(r"\(([\d.]+) Hz\)", c[7])
        hz[c[0]] = float(m.group(1)) if m else None
print("== LFO rate classes (sheet Rate column) against settled rates")
cls = {}
for s, r in sheet.items():
    rate = str(r[3]).strip()
    cls.setdefault(rate, []).append((s, hz.get(s)))
for k, v in sorted(cls.items()):
    vals = sorted(x for _, x in v if x)
    print(f"  {k!r}: {len(v)} sounds, measured {vals}, none: {[s for s, x in v if not x]}")
def med(xs):
    xs = [x for x in xs if x is not None]
    return (st.median(xs), min(xs), max(xs), len(xs)) if xs else None
print("== Attack class (A) against attack to -3 dB (ms)")
for k in ("None", "Fast", "Mid", "Slow"):
    print(f"  {k}: {med([r['Attack to -3 dB (ms)'] for r in rows if str(r['A (sheet)']).strip() == k])}")
print("== Release class (R) against release to -20 dB (ms)")
for k in ("None", "Fast", "Mid", "Slow"):
    print(f"  {k}: {med([r['Release to -20 dB (ms)'] for r in rows if str(r['R (sheet)']).strip() == k])}")
print("== Freq class against FILTER default")
for k in ("Low", "Mid", "High"):
    print(f"  {k}: {med([r['FILTER default (0-255)'] for r in rows if str(r['Freq (sheet)']).strip() == k])}")
print("== Res class against RESONANCE default")
for k in ("Low", "Mid", "High", "Max*"):
    print(f"  {k}: {med([r['RESONANCE default (0-255)'] for r in rows if str(r['Res (sheet)']).strip() == k])}")
print("== Noise class against noise share (dB); found = above -28 dB")
for k in ("x", "Low", "Mid", "High"):
    v = [(r['Sound'], r['Noise share (dB)']) for r in rows if str(r['Noise (sheet)']).strip() == k]
    found = [s for s, x in v if x is not None and x > -28]
    print(f"  {k}: {len(v)} sounds, above -28 dB: {len(found)} {found}; median {med([x for _, x in v])}")
print("== Octave")
ok = [r['Sound'] for r in rows if str(r['Octave (sheet)']).strip().replace('+', '') == str(r['Oscillator octave (measured)'])]
print(f"  agree {len(ok)}/64; disagree: {[ (r['Sound'], r['Octave (sheet)'], r['Oscillator octave (measured)']) for r in rows if r['Sound'] not in ok]}")
print("== Saw")
agree = 0; dis = []
for r in rows:
    sh = str(r['Saw (sheet)']).strip() == 'SAW'; me = str(r['Waveform (measured)']).startswith('saw')
    if sh == me: agree += 1
    else: dis.append((r['Sound'], r['Saw (sheet)'], r['Pulse (sheet)'], r['Waveform (measured)']))
print(f"  agree {agree}/64; disagree {dis}")
print("== agreement columns")
for col in ("Chorus agree", "Glide agree", "Vibrato agree", "Filter LFO agree", "Delay agree"):
    vals = [r[col] for r in rows]
    print(f"  {col}: yes {vals.count('yes')}, no {vals.count('no')}, other {[v for v in set(vals) if v not in ('yes','no')]}")
print("== disagreements (vibrato, filter LFO)")
for col, sc in (("Vibrato agree", "DCO LFO (sheet)"), ("Filter LFO agree", "VCF LFO (sheet)")):
    print(f"  {col}: {[(r['Sound'], r[sc]) for r in rows if r[col] == 'no']}")
