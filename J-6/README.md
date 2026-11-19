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
judgements of the reference spreadsheet, *Roland J-6 Preset Sounds Settings
Ver. 1.0*, produced by Nick Standing at JabunAudio, quoted for comparison.
Where both can be compared, chorus agrees on 56 of 56 sounds, glide on 60 of
60, vibrato on 49 of 56 and filter LFO on 41 of 56. `j6compare.py` rebuilds
the workbook from the CSV files and the reference spreadsheet.

Findings that hold across the 64 sounds:

- Choosing a sound writes its own `FILTER`, `RESONANCE` and `ATTACK`; `ENV`
  is always 128. 36 sounds have a non-zero attack.
- [ENVELOPE] is a macro on decay, sustain and release, not on release only:
  at 255 every pluck sustains, at 0 releases fall to about 10 ms.
- Chorus I and II are distinct: the stereo difference signal pulses at
  1.09 Hz for I and 1.76 Hz for II; chorus off is exact mono.
- Velocity changes the level by 19-20 dB between 40 and 127 on every sound,
  about level proportional to velocity squared.
- Glide is polyphonic: each voice glides from the last pitch it played.
- With [CHORD] unlit, MIDI notes play single notes at their MIDI pitch; the
  tuning measured within 0.3 cent of 440 Hz.
- The J-6 ignores All Sound Off.

Limits: octave and sub-oscillator are ambiguous for mixed waveforms (a
square plus a saw at one pitch has the same harmonic magnitudes as a
sub-oscillator plus a saw an octave up). Sounds that decay within 1.5 s get
no LFO, PWM or chorus measurement. The default pass was recorded with
`ATTACK` 0, so attack times come from the open pass. The env passes were
recorded in chord mode and are used for envelope levels and times only.

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
