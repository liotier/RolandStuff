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

Observed so far: choosing a sound writes its default `FILTER` and `RESONANCE`
into the pattern. Sound 1-3 gave 121 / 79, sound 1-4 gave 128 / 144, and an
initialised pattern (sound 1-1) holds 85 / 24. `ENV` stayed at 128 and
`ATTACK` at 0.

## Procedure

Keep the backup of your own patterns: every restore below overwrites all 64.

### 1. Harvest the defaults (once, by hand)

In each pattern, choose the sound with the same number: pattern 1-1 gets
sound 1-1, and so on through 8-8. Don't touch [FILTER] or [ENVELOPE], with or
without SHIFT. Do this on your own patterns, before restoring any generated
set: those already hold sound n in pattern n, and choosing a sound that is
already selected might not reload its defaults. Then back up and run:

```bash
python3 j6prm.py defaults HARVEST/BACKUP --before ORIGINAL/BACKUP -o defaults.csv
```

It checks that every pattern holds its own sound, compares sounds 1-3 and 1-4
with the values observed on the panel (121 / 79 and 128 / 144), and reports
whether choosing a sound also reset `ENV` and `ATTACK`.

There is no MIDI shortcut: a Program Change on the note channel does not
select a sound (tested on a v1.02 unit). An experimental shortcut through
restore exists:

```bash
python3 j6prm.py generate --template ORIGINAL/BACKUP/J6_PTN59.PRM --omit FILTER,RESONANCE --out passes/harvest
```

The files set each pattern's sound but leave out its cutoff and resonance.
Restore them, back up, and run `defaults` on that backup. It is valid only if
the reference check says OK, which happens only if the J-6 fills missing values
with the sound's defaults. If it fails, restore your original backup before
harvesting by hand, because every pattern then already holds its own sound.

### 2. Set the J-6's MIDI menu

`CH` 1 (notes), `Pc.Ch` 16 (Program Change), `rxPc` On. The script assumes
these values; `--note-channel` and `--pc-channel` change them.

### 3. Generate and restore a pass

```bash
python3 j6prm.py generate --template ORIGINAL/BACKUP/J6_PTN59.PRM --defaults defaults.csv --out passes/default
```

The template can be any freshly initialised pattern of yours (empty bars).
Pattern n gets sound n, delay and reverb levels are set to 0, and the phrase
style is off. Copy `passes/default/RESTORE/*.PRM` into the J-6's `RESTORE`
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
| `open` | `--filter 255 --resonance 0` | | oscillators, PWM, LFO, chorus without filtering |
| `env000` | `--defaults defaults.csv --env 0` | `--stimulus short` | [ENVELOPE] at minimum |
| `env255` | `--defaults defaults.csv --env 255` | `--stimulus short` | [ENVELOPE] at maximum |

Each pass needs its own `generate`, restore and capture run.

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
