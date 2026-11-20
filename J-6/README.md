# J-6 sound documentation tools

Tools to document the 64 preset sounds of the Roland J-6 (Aira Compact) from
the instrument itself. The sound engine's firmware image (`DD011_app.bin`
inside `J6_UPD.BIN`) is encrypted, so the preset parameters cannot be read from
it. Two sources remain:

1. **Pattern backups.** Choosing a sound writes its default cutoff and
   resonance into the pattern, and the backup records them exactly.
2. **Recordings.** Every sound played with the same test notes, analysed for
   oscillator mix, pulse-width modulation, LFO, envelopes, glide and chorus.

| File | Purpose |
|---|---|
| `j6prm.py` | inspect backups, extract per-sound defaults, generate pattern sets for restore |
| `j6capture.py` | select each pattern by Program Change, play test notes, record the USB audio |
| `j6passes.sh` | generate, restore and record the remaining passes in one run |
| `j6analyze.py` | measure every sound from the recorded takes |
| `j6experiments.py` | analyse the experiment passes: tempo, velocity, polyphony, knob sweeps |
| `j6compare.py` | set the measurements beside the reference spreadsheet in a workbook |

Both need only Python 3.8 or later. `j6capture.py` runs on Linux and needs
`arecord` and `aplaymidi` from alsa-utils, plus `flac` if you want compressed
takes. On Debian:

```bash
sudo apt install alsa-utils flac
```

MIDI goes through the ALSA sequencer by default: the script writes a small MIDI
file and plays it with `aplaymidi` to the client named `J-6`, and the kernel's
sequencer queue does the timing. This works even when another program holds
the J-6's raw MIDI port. `--midi raw` writes to the raw port instead, if it is
free.

## Pattern files (J-6 system program 1.02)

Backup mode: hold [PLAY] while switching on, with USB connected. The J-6
appears as a drive with `BACKUP` and `RESTORE` folders. To restore, copy files
into `RESTORE`, eject, press [CHORD] and wait until the LEDs stop blinking
([owner's manual](https://static.roland.com/manuals/J-6_manual_v102/eng/26654319.html)).

- One file per pattern, `J6_PTN01.PRM` to `J6_PTN64.PRM`. File `n` is the
  pattern labelled bank-number on the panel, with n = 8 × (bank − 1) + number.
- ASCII, LF line endings, 23 header lines `KEY<TAB>= value`, then
  `BAR 1` to `BAR 64`.

| Field | Meaning |
|---|---|
| `SOUND` | 0-63, sound bank-number = `SOUND // 8 + 1` - `SOUND % 8 + 1` (0 is 1-1) |
| `FILTER`, `RESONANCE` | 0-255, the [FILTER] knob and SHIFT + [FILTER] |
| `ENV`, `ATTACK` | 0-255, the [ENVELOPE] knob and SHIFT + [ENVELOPE] |
| `DELAY`, `REVERB` | effect levels; `DELAY_TIME`, `REVERV_TIME` (sic) their times |
| `TEMPO` | BPM × 100 |
| `LEVEL`, `TRANSPOSE` | pattern volume and transposition |
| `STYLE`, `VARIATION`, `STYLE_SW` | phrase settings, -1 / -1 / 0 in an initialised pattern |
| `BAR n` | `NOTE1`-`NOTE4` (MIDI note or -1), style, chord and pad data per bar |

Observed on a v1.02 unit, by harvesting all 64 sounds from a factory-reset
state: choosing a sound writes its own default `FILTER`, `RESONANCE` and
`ATTACK` into the pattern. Sound 1-3 gives 121 / 79 / 0, sound 1-4 gives
128 / 144 / 0, and 36 of the 64 sounds have a non-zero `ATTACK`. `ENV` is set
to 128 for every sound, including in patterns that held another value, so
[ENVELOPE] acts as a neutral-centred setting rather than a per-sound value.

## Procedure

Everything runs from one experiment folder holding the scripts
(`j6prm.py`, `j6capture.py`, `j6passes.sh`, `j6analyze.py`,
`j6experiments.py`), your backups
`Factory_backup/` and `Harvest_backup/` (with `defaults.csv`), and the
`passes/` and `captures/` folders the scripts create. For example:

```bash
bash j6passes.sh tempo150 sweep
```

```bash
python3 j6analyze.py captures -o measurements.csv
```

```bash
python3 j6experiments.py captures -o results
```

Keep the backup of your own patterns: every restore below overwrites all 64.

### 1. Harvest the defaults (once, by hand)

In each pattern, choose the sound with the same number, then save the pattern:
pattern 1-1 gets sound 1-1, and so on through 8-8. The J-6 discards unsaved
edits when you change pattern. Don't touch [FILTER] or [ENVELOPE], with or
without SHIFT. With the J-6's menu `rxPc` On, this loop switches the patterns
for you, so you only choose the sound and save:

```bash
S=1; for n in $(seq $S 64); do l="$(( (n-1)/8+1 ))-$(( (n-1)%8+1 ))"; amidi -p hw:4,0,0 -S "CF $(printf '%02X' $((n-1)))"; read -p "pattern $l: choose sound $l, SAVE the pattern, then press Enter "; done
```

`hw:4,0,0` is the J-6's raw MIDI port as `amidi -l` lists it. A factory reset
leaves demo patterns in banks 1-2 and sound 1-1 in banks 3-8, so no pattern
starts with its own sound. Do this on your own patterns, before restoring any generated
set: those already hold sound n in pattern n, and choosing a sound that is
already selected might not reload its defaults. Then back up and run:

```bash
python3 j6prm.py defaults HARVEST/BACKUP --before ORIGINAL/BACKUP -o defaults.csv
```

It checks that every pattern holds its own sound, compares sounds 1-3 and 1-4
with the values observed on the panel (121 / 79 and 128 / 144), and reports
whether choosing a sound also reset `ENV` and `ATTACK`.

There is no shortcut; both were tested on a v1.02 unit:

- A Program Change on the note channel does not select a sound.
- Restoring files that name the sound but omit `FILTER` and `RESONANCE`
  (`generate --omit FILTER,RESONANCE`) gives every pattern 85 / 24. The
  restore routine starts from an initialised pattern and applies the lines
  present; it does not load the sound's defaults. It does apply generated
  files exactly as written, which the recording passes rely on.

### 2. Set the J-6's MIDI menu

`CH` 1 (notes), `Pc.Ch` 16 (Program Change), `rxPc` On. The script assumes
these values; `--note-channel` and `--pc-channel` change them.

Chord mode must be off ([CHORD] unlit). With it off, incoming MIDI notes play
single notes at their MIDI pitch (A2 measured at 110.02 Hz). In chord mode, the
J-6 treats each incoming note like a keyboard button: the pitch class selects
the chord registered to that button and the octave shifts its voicing. On a factory-reset
unit, A (MIDI 45, 57, 69) played F-A-C over A, and E (MIDI 52) played C-D-E-G
over E.

The J-6's USB audio runs only at 44.1 kHz (32-bit stereo on a v1.02 unit).
The script reads the native rate from `hw_params.txt` and records at it, so
that ALSA does not resample.

### 3. Generate and restore a pass

```bash
python3 j6prm.py generate --template FACTORY/BACKUP/J6_PTN17.PRM --defaults defaults.csv --out passes/default
```

The template can be any pattern with empty bars: a blank factory pattern
(banks 3-8 after a factory reset) or one you initialised. Pattern n gets
sound n, with the harvested `FILTER`, `RESONANCE`, `ENV` and `ATTACK` unless
an option overrides them; delay and reverb levels are set to 0, and the
phrase style is off. Copy `passes/default/RESTORE/*.PRM` into the J-6's `RESTORE`
folder, eject, press [CHORD], wait for the LEDs, switch off, then switch on
normally.

### 4. Record: pilot first

```bash
python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE --outdir captures/default --patterns 1..3 --flac
```

Keep the sequencer stopped and the knobs untouched. Watch that the J-6 moves to
the pattern the script announces. If it is one pattern off, rerun with
`--pc-offset 1` or `--pc-offset -1`. Send the pilot takes for checking before
the full run, which skips takes already recorded:

```bash
python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE --outdir captures/default --patterns 1..64 --flac
```

### 5. The other passes

| Pass | `j6prm.py generate` options | `j6capture.py` options | Purpose |
|---|---|---|---|
| `default` | `--defaults defaults.csv` | | each sound as selected |
| `open` | `--defaults defaults.csv --filter 255 --resonance 0` | | oscillators, PWM, LFO, chorus without filtering |
| `env000` | `--defaults defaults.csv --env 0` | `--stimulus short` | [ENVELOPE] at minimum |
| `env255` | `--defaults defaults.csv --env 255` | `--stimulus short` | [ENVELOPE] at maximum |

Each pass needs its own `generate`, restore and capture run. Check that
[CHORD] is unlit after every restore: chord mode can be on afterwards, and a
pass recorded in chord mode is unusable for spectral analysis. `j6passes.sh`
chains them: it generates the sets, then for each pass waits for the J-6 drive
(backup mode), copies the files into `RESTORE`, unmounts, and records once you
have pressed [CHORD] and switched the J-6 off and on. Run it from the folder
holding `Factory_backup/` and `Harvest_backup/`:

```bash
bash j6passes.sh
```

`J6_MOUNT` overrides the drive's mount point (default `/media/$USER/J-6`), and
`J6_PATTERNS=1..3` limits a run to a few patterns. It knows the passes
`default`, `open`, `env000` and `env255`; env255 waits 10 s between patterns,
because a note rings for seconds at that setting and the J-6 ignores All
Sound Off.

### 6. Restore your own patterns

Copy your original backup into `RESTORE` and restore it.

## Test notes

Roland numbering, C4 = 60. The `short` stimulus is the first two notes only.

| Time (s) | Note | Gate (s) | Measures |
|---|---|---|---|
| 0.00 | A2 (110 Hz) | 6.00 | envelope, LFO, PWM, chorus, 3 s release tail |
| 9.00 | A2 | 0.15 | behaviour with a short gate |
| 11.50 | A4 (440 Hz) | 1.50 | keyboard tracking |
| 15.00, 15.85 | A2 then E3 | 0.80, 1.20 | glide |
| 19.05, 21.05 | A3 at velocity 40, then 127 | 0.80 each | velocity sensitivity |

Each take is about 26 s (`full`) or 13 s (`short`), so a pass takes about 30
or 16 minutes. As FLAC, expect roughly 260 MB or 130 MB per pass.

Each take has a JSON sidecar recording the pattern, its settings (with
`--prm-dir`), the planned and actual time of every note, and the peak level.
`session.json` logs each run, and `hw_params.txt` the J-6's native audio
formats.

## Analysis and results

`j6analyze.py` measures every sound from the four passes' takes and writes
one CSV row per sound. It needs numpy, scipy and soundfile:

```bash
sudo apt install python3-numpy python3-scipy python3-soundfile
```

```bash
python3 j6analyze.py captures -o measurements.csv
```

`results/defaults.csv` holds the harvested defaults (`FILTER`, `RESONANCE`,
`ENV`, `ATTACK` per sound), and `results/measurements.csv` the measurements
from a factory-reset v1.02 unit. The script's header defines each column.

`results/J6_sounds_measured.xlsx` sets the measurements beside the
judgements of the reference spreadsheet, quoted for comparison: Nick Standing
(JabunAudio), *Roland J-6 Preset Sounds Settings Ver. 1.0*, published with the
video [Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet!](https://www.youtube.com/watch?v=z6hoNwWadR8).
Chorus agrees on 64 of 64 sounds, glide on 60 of 60 measurable, vibrato on 56
of 64 and filter LFO on 53 of 64. `j6compare.py` rebuilds the workbook from
the CSV files and the reference spreadsheet.

Findings that hold across the 64 sounds:

- Choosing a sound writes its own `FILTER`, `RESONANCE` and `ATTACK`; `ENV`
  is always 128. 36 sounds have a non-zero attack.
- [ENVELOPE] is a macro on decay, sustain and release, not on release only:
  at 255 every pluck sustains, at 0 releases fall to about 10 ms.
- Chorus I and II are distinct: the stereo difference signal pulses at
  1.09 Hz for I and 1.76 Hz for II; chorus off is exact mono.
- Velocity changes the level by 19-20 dB between 40 and 127 on every sound:
  level is proportional to velocity squared (exponent 2.00 from 8 to 127, see
  Experiments). It does not change the brightness.
- Glide is polyphonic: each voice glides from the last pitch it played.
- The LFOs follow the pattern tempo. Measured across seven notes, the
  rates of 27 sounds' LFOs fall within 0.1 % of a note value at 100 BPM, from
  a whole-note triplet (0.625 Hz) to a thirty-second (13.33 Hz), and at
  150 BPM they run 1.5 times faster (see Experiments). Their delays do not
  follow the tempo. Most LFOs run freely; three restart with each note. The
  chorus is free-running.
- LFO rates of 3.17, 2.53 and 0.53 Hz in `measurements.csv` are artifacts:
  the analysis ignores a band of 0.35 Hz around each chorus harmonic, and an
  LFO inside such a band reads at its edge. The true rates (3.33, 2.5, 0.556
  or 0.625 Hz) come from the keysync experiment; `lfo_flags` marks the cases.
- LFO delay (time until the modulation reaches half its later depth) agrees
  with the reference spreadsheet's Delay column on 34 of the 37 sounds where
  an LFO was measured. Delays shorter than one LFO cycle read 0, and an onset
  transient in the same measurement can hide one (7-7).
- [CHORD] is on after every power-on, and then each MIDI note plays a chord.
  With [CHORD] unlit, MIDI notes play single notes at their MIDI pitch; the
  tuning measured within 0.3 cent of 440 Hz.
- The J-6 ignores All Sound Off.

Limits: octave and sub-oscillator are ambiguous for mixed waveforms (a
square plus a saw at one pitch has the same harmonic magnitudes as a
sub-oscillator plus a saw an octave up). Sounds that decay within 1.5 s get
no LFO, PWM or chorus measurement in the default and open passes; they are
measured on the env255 pass, where they sustain. LFO rates below 0.3 Hz are
not detected. The env000 pass was recorded in chord mode and is used for
envelope levels and times only. The `key_tracking` column, from brightness,
misreads sounds whose filter is open, where brightness follows the
oscillator: 4-4 reads 0.63 there and 0.0 in the filter sweep, 2-7 0.78 and
0.50.

## Experiments

Further pattern sets, recorded with `bash j6passes.sh tempo150 sweep`,
`bash j6passes.sh keysync filters` and `bash j6passes.sh closing` (one
restore each) and analysed with
`python3 j6experiments.py captures`, which writes CSV files into `results/`
and prints a summary:

| Set | Patterns | Recordings | Question |
|---|---|---|---|
| `tempo150` | every sound at its defaults, tempo 150 BPM | full pass; velocity ladder on 1-3, 2-7, 4-4, 6-8; polyphony test on 2-7, 4-7, 7-2 | do the LFO rates and delays scale by 1.5 with tempo, and does anything else; level against velocity; number of voices |
| `sweep` | 16 steps (0, 17 ... 255) of FILTER on 6-8, RESONANCE on 2-7, ATTACK on 2-7, ENV on 1-3 | full stimulus, then the ENV sweep with long tails | knob value against cutoff (Hz, read from the self-oscillating filter), resonance, attack time, decay / sustain / release |
| `keysync` | every sound at its defaults (8-7 at 150 BPM) | `retrig` on the 38 sounds with an LFO that sustain: seven A2 notes of 3.5 s at irregular spacing | does each LFO (and 8-7's sample and hold) restart with each note or run freely |
| `filters` | 6-8, 2-7, 4-6, 4-4: FILTER 255 / RESONANCE 0, then FILTER 17 ... 238 at RESONANCE 255; 1-3 at ENV 221, 238, 255 | `filter` (A1, A2, A3, A4, 2 s each) on the first 60; `longtail` (one 6 s note, 30 s of release) on the last three | each sound's cutoff offset, steps per octave and keyboard tracking; releases longer than 7.5 s |
| `closing` | 8-8 at 60 and 70 BPM; 5-3, 6-3, 8-2 at 100 and 60 BPM; 3-6, 5-5, 5-8, 7-2, 8-3 at 100 and 60 BPM; 6-5 and 5-6 | `longnote` (one 20 s A2 note) on all but 6-5 and 5-6; `retrig8` (eight A2 notes) on those at 60-100 BPM; `chord` (four staggered notes) on 5-3, 6-3, 8-2, 6-5, 5-6 | does 8-8's 13.33 Hz LFO follow the tempo; exact rates, tempo sync and phase of the unclear sounds; do sounds where no LFO was found have one; do the voices share one LFO phase |

`j6prm.py generate --plan sweep` builds the sweep set (the plan is built in);
`--plan FILE` builds any pattern set from a CSV giving each pattern its sound
and knob values (columns pattern, sound, FILTER, RESONANCE, ENV, ATTACK, BPM);
`keysync` and `filters` are built in too. `j6capture.py` has six extra stimuli:
`envelope` (6 s note, 8 s tail, staccato, 6 s tail), `velocity` (A3 at 16
velocities, 8 to 127), `poly` (six notes entering 0.5 s apart, released
together), `retrig`, `filter`, `longtail`, `longnote`, `retrig8` and `chord`
(above).

`longnote` resolves rates to about 0.05 Hz, enough to tell an LFO from a
harmonic of the chorus LFO, whose own rate it measures on the same note
(0.543 Hz for chorus I, 0.878-0.880 Hz for chorus II on the 6 s notes).
`retrig8` spreads its onsets for every note value at 60, 70 and 100 BPM
(concentration at most 0.43; the `retrig` onsets give 0.82 for 12 Hz at
90 BPM, which is why 8-8 is tested at 60 and 70). In `chord`, each voice is
read on its own fundamental and 2nd harmonic, which no other note shares.

The `retrig` onsets (0, 4.64, 9.16, 13.83, 18.40, 22.91, 27.49 s) are chosen
so that, for every note value at 100 BPM, an LFO running freely would meet the
seven note-ons at scattered phases (concentration at most 0.46, where 1 means
the same phase each time), while an LFO that restarts with each note shows the
same phase on all seven. In `filters`, the resonant peak is located by
comparing each harmonic with the sound's FILTER 255 / RESONANCE 0 reference,
so it works whether or not the filter self-oscillates; on synthetic test
signals the fit recovers the mapping within 5 cents.

Results from the same unit (`results/tempo.csv`, `velocity.csv`, `poly.csv`,
`sweep_*.csv`, `keysync.csv`, `filters*.csv`, `longtail.csv`):

- **Tempo.** Of the LFOs detected at both 100 and 150 BPM (24), the rates
  scale by a median 1.502 against a tempo ratio of 1.500, and 22 keep their
  note value; the two others are on 8-4, whose LFO (0.625 Hz, from the
  keysync experiment) the 6 s note resolves poorly. The seven LFO delays measurable at both
  tempos stay the same (median ratio 0.97, against 0.67 if they followed the
  tempo): rates are tempo-synced, delays are in seconds. Attack, sustain,
  release and glide differ by a median of 2 ms, 0.2 dB, 5 ms and 0 ms; the
  larger differences fall on sounds whose LFO, running faster, moves these
  measurements. Chorus is unchanged.
- **Sample and hold.** 8-7, which the reference spreadsheet describes as a
  free-running S&H LFO to the filter, shows random brightness steps at
  4.44 Hz at 100 BPM and 6.67 Hz at 150 BPM: a dotted sixteenth at both
  tempos, so the S&H clock follows the tempo too, and its steps restart with
  each note (keysync). Its random level changes also make its attack and
  release measurements arbitrary.
- **LFO phase** (keysync: seven A2 notes of 3.5 s at irregular spacing, 38
  sounds). An LFO was found on 33. Of these, 27 run freely: their phase
  agrees against the clock (concentration 0.92-1.00) and not against the
  note-on (at most 0.41). Three restart with each note (1.00 against the
  note-on, at most 0.46 against the clock): 5-6 (4.44 Hz, vibrato, filter and
  PWM together), 8-8 (13.33 Hz; the same rate on A2 and A4, so an LFO and not
  a beat between detuned oscillators) and 8-7's sample and hold. 5-3, 6-3
  (6.81 Hz, not a note value) and 8-2 are unclear. The free-running rates sit
  within 0.1 % of a note value; 7-8 and 8-4 run at 0.625 Hz, a whole-note
  triplet. A delay fades the depth in with each note while the phase runs on.
  The PWM at 4.40 Hz on 7-7 is the 5th harmonic of the chorus II LFO
  (0.88 Hz), and 2-6's 7.5 Hz pitch modulation the 3rd harmonic of its 2.5 Hz
  LFO.
- **Velocity.** On 1-3, 2-7, 4-4 and 6-8, level follows velocity squared:
  exponent 1.99-2.02, 48 dB from velocity 8 to 127. Brightness shows no trend
  (the scatter on 2-7 and 4-4 is their chorus and LFO caught at different
  phases).
- **Polyphony.** Four voices. With six held notes C3 E3 G3 B3 D4 F4 entering
  0.5 s apart, E3 falls silent when D4 enters and G3 when F4 enters, while
  C3, the oldest and lowest, keeps sounding, on all three sounds tested. The
  voice allocation steals the oldest note except the lowest (measured on each
  note's fundamental).
- **FILTER** (6-8, whose RESONANCE 255 makes the filter ring). The resonant
  peak moves one octave per 14.4 steps: about 30 Hz at 85, 67 Hz at 102,
  817 Hz at 153, 1.75 kHz at 170 (A2), then flattens towards 13 kHz at 255
  (A2) and about 16 kHz (A4). Below 85 the filter is closed. It follows the
  keyboard fully: A4 puts the peak two octaves above A2 (1.00 octave per
  octave).
- **FILTER per sound** (filters: RESONANCE 255, notes A1 to A4, the resonant
  peak located against a FILTER 255 / RESONANCE 0 reference). One FILTER
  value gives cutoffs octaves apart on different sounds: 1 kHz at A2 needs
  FILTER 158 on 6-8, 78 on 2-7, 31 on 4-6, and less than 17 on 4-4. Keyboard
  tracking differs too: 6-8 1.00, 2-7 0.50, 4-6 0.31, 4-4 0.0 (the reference
  spreadsheet marks 6-8 and 2-7 tracked, 4-6 and 4-4 not). So does the curve:
  6-8 rises one octave per 14-15 steps from 153 to 187; 4-4 and 4-6 one
  octave per about 31 steps near 17, steepening to 16-18 near 68-85, with the
  same ratios step by step, as if they shared one curve at different
  offsets. From about 102 on 4-4, 119 on 4-6 and 153 on 2-7, the response up
  to 12 kHz stays within a few dB of FILTER 255. The 6-8 values agree with the direct
  reading of its self-oscillation within 3 %.
- **RESONANCE** (2-7, FILTER 69). Against RESONANCE 0, the resonant peak
  rises to about +15 dB (at 660 Hz for A2, near 1.3 kHz for A4, to the nearest
  harmonic) and saturates above 170-204; the fundamental drops 5-6 dB, the
  passband loss of a ladder-type filter. No self-oscillation on this sound.
- **ATTACK** (2-7). Rise to -3 dB stays under 20 ms up to 68, then doubles
  every 31 steps: 32 ms at 85, 141 ms at 136, 571 ms at 204, 1.7 s at 255
  (2.8 s to the peak). Sustain and release do not change.
- **ENV** (1-3). 0-119 is a pluck without sustain whose decay to -20 dB
  lengthens from 35 to 215 ms. From 136 a sustain appears (-18.7 dB) and rises
  to -0.7 dB at 255, while the release to -20 dB lengthens from 0.3 s to
  5.6 s at 221; a staccato note's release matches the long note's.
  Brightness follows the same envelope: at ENV 255 it holds, at 136 it falls
  after the onset.
- **Long releases** (longtail, 1-3). The release is a clean exponential down
  to -140 dBFS: 3.5 dB/s at ENV 221 (-60 dB after 17.0 s), 2.27 dB/s at both
  238 and 255 (-60 dB after 26.4 s). The release stops lengthening at 238.

## Troubleshooting

- **arecord says "Device or resource busy"**: the desktop sound server holds
  the J-6's audio. Set its card profile to off with `pactl` or pavucontrol
  while recording.
- **amidi says "Device or resource busy"**: a sequencer client is connected to
  the J-6, for example a browser page using Web MIDI. `aconnect -l` hides some
  clients; `cat /proc/asound/seq/clients` lists them all. The default
  `--midi seq` route works regardless, but close any program that could send
  MIDI to the J-6 while you record.
- **Silent takes**: check the J-6's `CH` setting and that its volume is up.
- **Every take sounds the same**: `rxPc` is off or `Pc.Ch` differs from
  `--pc-channel`.
