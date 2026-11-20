# The Roland J-6's 64 preset sounds, measured

This report documents the 64 preset sounds of the Roland J-6 chord
synthesizer (AIRA Compact, system program 1.02) by measurement. It draws on
the pattern files the instrument writes, on 539 recorded takes (3.4 hours of
audio) from eleven pattern sets restored into it, and on a few thousand lines
of Python. Every result is set beside the patch sheet that Nick Standing
compiled by ear, which supplied the names, the questions and, more often than
not, the answers.

- [Section 1](#1-on-the-shoulders-of-a-giant-nick-standings-patch-sheet) is about that patch sheet, with the receipts.
- [Section 2](#2-results) gives the results in two tables.
- [Section 3](#3-how-we-found-out) tells how they were obtained, in plain terms, with the most surprising findings.
- [Section 4](#4-the-full-method) gives everything else: scripts, signal processing, intermediate results, dead ends.

## 1. On the shoulders of a giant: Nick Standing's patch sheet

Roland names none of the J-6's sounds: its documentation numbers them 1-1 to
8-8 and leaves it there
([owner's manuals](https://www.roland.com/global/support/by_product/j-6/owners_manuals/)).
Into that silence Nick Standing, of JabunAudio, published *Roland J-6 Preset
Sounds Settings Ver. 1.0*, a two-page patch sheet offered free with his video
[Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet! (Free download or donation)](https://www.youtube.com/watch?v=z6hoNwWadR8).

For each of the 64 sounds the sheet gives a name, a note, and a judgement on
22 attributes: glide, octave, LFO rate and delay, vibrato, pulse-width
modulation, pulse, saw, sub-oscillator, noise, high-pass filter, cutoff,
resonance, filter envelope, filter LFO, keyboard tracking, gate or envelope on
the amplifier, attack, decay, sustain (with the range the [ENVELOPE] knob
covers), release and chorus mode. That is 1,408 judgements, made by ear on an
instrument that exposes four sound parameters (two knobs, doubled by [SHIFT])
and hides everything else. The names are his, and they are the only names
these sounds have; this report uses them throughout.

That the sheet exists at all is the first achievement; that it is right is
the second. Checking it took this project a computer driving the
instrument, eleven pattern sets restored into it, 539 recorded takes,
Fourier analysis at six resolutions and a battery of synthetic test
signals. Wherever those could reach, they mostly confirmed what he had
heard, and several times they reached his answer only after detours his ear
had not needed: LFOs locked to the tempo, an LFO at audio rate behind a
"ring modulator", a filter LFO that an open filter hides. Every name in this
report is his, and so are most of its questions. The receipts:

| The patch sheet says | The measurements found |
|---|---|
| "LFO tied to tempo" (a header line) | Every LFO rate is a note value of the pattern tempo. At 150 instead of 100 BPM, 24 LFOs sped up by a median factor of 1.502, against a tempo ratio of 1.500. |
| LFO rate "Slow" (9 sounds), "Mid" (24), "Fast" (7) | 0.556-1.667 Hz, 1.25-5 Hz and 4.44-13.33 Hz at 100 BPM (4-5's faint vibrato, at 2.22 Hz, aside): three ordered classes that overlap only at their edges. |
| 6-3, "Square Ring Mod", LFO rate "Max" | A modulation at 53.33 Hz, a 1/128 note at 100 BPM: an LFO at audio rate, which is what a ring-modulator timbre is made of. |
| 2-1: "LFO retriggers at 1/8th notes ... once Envelope Control is past 50%" | 3.330 Hz with [ENVELOPE] at 255; an eighth note at 100 BPM is 3.333 Hz. |
| Footnote: "Sustains once Envelope control is past 50%" | On 1-3 a sustain appears between ENV 119 and 136, between 47 % and 53 % of the knob's travel. |
| Sustain "Off" at the default, rising with [ENVELOPE] (12 sounds, the footnote's "#") | 11 of them are the plucks of section 2.3, silent before the note-off at ENV 0 and 128 and sustaining at 255; the twelfth, 1-7, sustains at -10 dB after its attack. |
| Sustain range under [ENVELOPE]: none noted, "(Mid -> High)", "(Low -> High)" | The sustain level rises from ENV 0 to 255 by a median 1.8, 6.1 and 10.2 dB on these three sets: the same order. |
| 6-8: "Keyboard tracked self-oscilating filtered noise" | Noise through a filter that rings at RESONANCE 255 and follows the keyboard at 1.00 octave per octave. |
| 8-7 and 8-8: the effect "dissapears for high Filter Settings" | The mechanism that hid 8-2's filter LFO through four rounds of analysis: at its default FILTER of 251 the LFO sweeps a cutoff that already lies above the sound. |
| Attack "None", "Fast", "Mid", "Slow" | Median attack times of 3 ms, 21 ms, 0.13 s and 1.9 s. |
| Release "None", "Fast", "Mid", "Slow" | Median release times (to -20 dB) of 9 ms, 40 ms, 0.26 s and 1.0 s. |
| Cutoff "Low", "Mid", "High"; resonance "Low", "Mid", "High", "Max" | Median default FILTER of 27, 117.5 and 160.5; median default RESONANCE of 0, 43, 158.5 and 255. |
| Noise absent, "Low", "Mid", "High" | Median noise share of -32.85, -31.0, -27.0 and -10.85 dB: the same order. |
| Chorus I, II or off | Agreement on 61 of 64 sounds, four of them (1-7, 2-3, 2-6, 5-1) settled only by a finer test made for this report. |
| Glide | Agreement on the 60 sounds where glide can be measured. |
| LFO delay | Agreement on 34 of the 37 sounds where an LFO was measured. |
| Keyboard tracking of the filter | 6-8 and 2-7 tracked (1.00 and 0.50 octave per octave), 4-4 not (0.0); 4-6, marked untracked, follows at 0.31. |
| A filter LFO on 2-7, 6-4, 6-8, 7-6, 8-2, 8-3 and 8-7, none on 5-3 | Our first analysis disagreed on all eight. Later experiments proved him right on all eight. |
| A vibrato on 7-3 | Missed at first, then found: 16 cents at a dotted sixteenth. |
| A slight vibrato on 4-5 | 2-3 cents at a dotted eighth, following the tempo: under our 6-cent detection threshold, found only for this report. |
| Pulse-width modulation on 4-3, 5-6, 7-1 and 7-4 | Our spectra first read these four as saws: a pulse whose width sweeps widely averages to the spectrum of a saw. With the filter fully open, their even harmonics and their brightness still swing at the LFO's rate (even share by 0.16-0.48, brightness by 0.35-0.68 octave): the waveform itself moves, as he says. |

Where the measurements and the sheet still differ:

- **5-5 "Angry Cat"**, "fast filter modulation": no periodic filter movement
  was found. Its fast brightness jitter belongs to its noisy source, since it
  stays when the filter is fully open, and a noise source through a resonant
  filter does sound like a fast filter modulation. A filter movement smaller
  than a tenth of that jitter would escape the test.
- **4-2**, "Wide LFO Filter Sweep for low Filter/Envelope values": nothing at
  its defaults; the low settings he describes were not tested.
- **1-6**, a filter LFO: measurable only with [ENVELOPE] at 255, where its
  brightness swing at 2.5 Hz could come from the filter or the pulse width.
- **4-6**, a vibrato ("Mid", with a delay): none found, even below the
  detection threshold.
- **2-1, 4-5 and 8-7**, chorus II: all three use a third chorus mode, fast
  (7.57 Hz) and shallow, which the sheet's I, II and off do not provide for:
  the J-6's counterpart of the JUNO-60's "secret" I+II mode (section 4.5.5).
- **Pitch movements he does not list** on 7-6, 8-1, 8-3 and 8-4 (10-14 cents)
  and 5-6 (80 cents). They persist with the filter open, so they are not the
  filter's pull on the pitch; on 5-6 the pulse-width modulation alone may
  produce them (sections 3.3 and 4.5.15).
- **7-3**, a saw without pulse-width modulation: with the filter fully open,
  its even harmonics and its brightness still swing at the LFO's rate, as on
  the four PWM sounds above.
- **LFOs he does not list**: 1-7 (pulse width, which he marks fixed), 5-4
  (pulse width) and 7-2 (a 6-cent vibrato). All three are subtle.
- **Free-running or not**: he calls the LFOs of 8-7 and 8-8 free-running; on
  separated notes both restart. On 5-6 a restart happens only when no other
  key is held, so a legato line hears a free-running LFO; whether 8-7 and 8-8
  behave alike was not tested.
- **Oscillator make-up**: saw against pulse agrees on 43 of 64 sounds, octave
  on 48 of 64. Most differences involve mixes and swept pulses, which a
  spectrum cannot disentangle (section 4.9); they say more about the method
  than about his ear.

He drew the map; this report surveys it.

The sheet is quoted here, cell by cell, as comparison material: the names in
section 2, the receipts above, and his judgements beside our measurements in
`results/J6_sounds_measured.xlsx`. The original, with all its notes, remains
the reference: Nick Standing (JabunAudio), *Roland J-6 Preset Sounds Settings
Ver. 1.0*, distributed with
[his video](https://www.youtube.com/watch?v=z6hoNwWadR8).

## 2. Results

### 2.1 The 64 sounds

One J-6 (system program 1.02, factory reset), each sound at the settings the
J-6 gives it, pattern tempo 100 BPM. Names as written in Standing's sheet.
The same data, one field per attribute for sorting and filtering, is in
[`results/sounds.csv`](results/sounds.csv).

@@TABLE@@

How to read it:

- **Sound**: the panel number (bank-number), with the name Standing gave the
  sound.
- **Oscillator**: the harmonic make-up of an A4 note with the filter fully
  open (FILTER 255, RESONANCE 0), averaged over the note; the waveform on the
  first line, octave and sub-oscillator on the second. "pulse 31 %" is a pulse that is high for 31 % of its period, from
  the ratio of its first two harmonics. "+1 oct": the oscillator sounds an
  octave above the note played. "sub -3 dB": a square sub-oscillator one
  octave below the oscillator, 3 dB under it. "noise": the energy between the
  harmonics exceeds -28 dB relative to them (a threshold placed after seeing
  the sheet; the median shares in section 1 do not depend on it). Averaged
  over time, a pulse whose width sweeps widely has the spectrum of a saw:
  "pulse, PWM" marks the four sounds where, with the filter fully open, both
  the even harmonics and the brightness still swing at the LFO's rate; "saw
  spectrum, PWM per Standing" marks those where this could not be shown.
- **Chorus**: I (its LFO at 0.543 Hz), II (0.879 Hz) or fast (7.57 Hz, the
  counterpart of the JUNO-60's I+II), from the rate at which the two channels
  move in opposite phase (section 4.5.5); Off is exact mono.
- **Attack / sustain / release, glide**: the amplitude envelope of a 6 s A2
  note with the filter fully open. Attack: time to come within 3 dB of the
  peak. Sustain: the level at the end of the note, relative to the peak.
  Release: time to fall by 20 dB after the note-off. A pluck, which has no
  sustain, gets its decay time to -20 dB instead. A glide line appears on the
  sounds that glide: the time the second note of a legato A2-E3 pair takes to
  settle within 40 cents of its pitch. The others jump, except 2-2, 3-1, 4-4
  and 6-8, where the glide could not be measured.
- **LFO**: "none", or up to four lines.
  - What it moves, from the swing of pitch, brightness and even harmonics with
    the filter at the sound's setting and fully open (section 4.5.15).
    "pitch" means that the pitch moves, whatever the cause. "pulse width": the
    even harmonics swing at the LFO's rate even with the filter fully open.
    The chorus moves them too, which makes this the least certain of the three
    readings; "?" marks the two sounds where the sheet hears a saw without
    PWM.
  - Its rate: the note value and its frequency at 100 BPM; at another tempo
    the rate scales with it.
  - Its phase: "free-running": the LFO runs on its own clock and each note
    catches it at a different point; "restarts": a note played while no other
    key is held starts the LFO at the same point every time; "phase not
    tested": plucks.
  - Its delay, when it has one: seconds until the modulation reaches half its
    final depth; "delay hidden": hidden by the sound's own envelope. No delay
    line means none, or one shorter than an LFO cycle.
- **FILTER, RES, ATTACK**: the values (0-255) the J-6 writes into a pattern
  when the sound is chosen, one per line. [ENVELOPE] (`ENV`) is always set to
  128.

### 2.2 The instrument as a whole

| Finding | Evidence | Data in `results/` |
|---|---|---|
| LFO rates are note values of the pattern tempo: from a whole-note triplet (0.625 Hz at 100 BPM) to a thirty-second (13.33 Hz), and a 1/128 (53.3 Hz) on 6-3. | 24 LFOs measured at 100 and 150 BPM: median rate ratio 1.502 for a tempo ratio of 1.500. 8-8 is a 1/32 at 60, 70 and 100 BPM; seven more sounds follow the tempo at 60 BPM. | `tempo.csv`, `longnote.csv`, `verylong.csv` |
| LFO delays are in seconds, not in beats. | 7 delays measurable at both tempos: median ratio 0.97, where tempo-synced delays would give 0.67. | `tempo.csv` |
| One LFO per sound, shared by all voices. | Four notes entering 0 to 1.05 s apart: the voices' phases agree (concentration 1.00) on 6-5 and 5-6. | `chord.csv` |
| 33 LFOs run freely; 4 restart (5-6, 6-3, 8-7's sample and hold, 8-8); 5-5 has none. | Seven or eight notes at irregular intervals: concentration 0.90-1.00 against one clock and at most 0.41 against the note-ons, or the reverse. Seven random phases reach 0.9 with probability 0.0007. | `keysync.csv`, `keysync2.csv`, `keysync3.csv` |
| A restarting LFO restarts only when no other key is held. | In a four-note chord on 5-6, the shared phase is the one the first note sets, within 4 degrees (44-116 degrees off for the others). | `chord.csv` |
| Four voices; a fifth note steals the oldest voice, unless that voice holds the lowest note. | Six held notes entering 0.5 s apart, on 2-7, 4-7 and 7-2. Roland: "Four-voice JUNO-60 synth engine" ([product page](https://www.roland.com/global/products/j-6/)). | `poly.csv` |
| Level follows the square of velocity; brightness ignores velocity. | Exponent 1.99-2.02 on four sounds: 48 dB from velocity 8 to 127. From velocity 40 to 127, the 64 sounds rise by a median 20.0 dB, where the square law predicts 20.1 (8-5 and 2-1 read lower: a 1.9 s attack and a 75 ms decay distort the 0.5 s window). | `velocity.csv`, `measurements.csv` |
| Choosing a sound writes its own FILTER, RESONANCE and ATTACK into the pattern; ENV is always 128. | 64 patterns harvested; 36 sounds have a non-zero ATTACK. | `defaults.csv` |
| FILTER moves the cutoff one octave per 14.4 steps (6-8, below 2 kHz), with offsets of several octaves between sounds and keyboard tracking that differs by sound. | 1 kHz at A2 needs FILTER 158 on 6-8, 78 on 2-7, 31 on 4-6 and less than 17 on 4-4; tracking 1.00, 0.50, 0.31 and 0.0. | `sweep_filter.csv`, `filters*.csv` |
| RESONANCE lifts the resonant peak by up to about 15 dB and lowers the fundamental by 5-6 dB. | 2-7 at FILTER 69, 16 steps. | `sweep_resonance.csv` |
| ATTACK stays under 20 ms up to 68, then doubles every 31 steps, to 1.7 s at 255. | 2-7, 16 steps. | `sweep_attack.csv` |
| [ENVELOPE] moves decay, sustain and release together, in four ways depending on the sound (section 2.3). On 1-3, a pluck: decay to -20 dB from 35 to 215 ms between 0 and 119, a sustain from 136 (-18.7 dB) to 255 (-0.7 dB), and releases up to 26.4 s to -60 dB. | 1-3: 16 steps, then three notes with 30 s of tail. All 64 sounds at ENV 0, 128 and 255. | `sweep_env.csv`, `longtail.csv`, `envelope.csv` |
| The chorus has three modes, each a free-running LFO: I at 0.543 Hz, II at 0.879 Hz, and a fast, shallow mode at 7.57 Hz (2-1, 4-5 and 8-7), the counterpart of the JUNO-60's "secret" I+II. Chorus off is exact mono. | I and II measured on 20 s notes; the fast mode at the same rate at 100 and 150 BPM; each sound's mode from the opposite-phase movement of its two channels. | `longnote.csv`, `chorus.csv` |
| MIDI notes play at their pitch when [CHORD] is unlit, and [CHORD] is lit after every power-on. Tuning is within 0.3 cent of A440. | A2 measured at 110.02 Hz. | `measurements.csv` |
| Glide belongs to each voice: a voice glides from the last pitch it played. | The starting pitch of a glide changes with the voice that plays it. | `measurements.csv` |
| The J-6 ignores the MIDI message All Sound Off. | Releases ring on through it. | - |

### 2.3 What [ENVELOPE] does to each sound

[ENVELOPE] does not act the same way on every sound. Each sound was recorded
with the knob at 0, at its default of 128 and at 255, its other settings
unchanged, and the sounds fall into four groups by what the knob does to
their sustain and release:

@@BLOCK ENVELOPE groups@@

Sustain is the level at the end of a 6 s note relative to its peak ("none":
no sustain); release, the time to fall by 20 dB after the note-off, followed
for 3 s ("-": the note had died before the note-off). In short: plucks need
the knob past the middle to sustain at all; gated sounds have no release at
the middle of the knob and get one only above it; sounds with a tail already
have one at the default, which the knob shortens to tens of milliseconds at 0
and stretches to seconds at 255. On the sustained sounds the knob also raises
the sustain level, by a median 5 dB from 0 to 255 (at most 15 dB), and by
about 20 dB on the decaying tones. Standing's sheet foresaw the plucks: the
twelve sounds it marks "Off" with the footnote "#" are the eleven plucks and
1-7. The values for each sound are in section 4.6 and `results/envelope.csv`.

## 3. How we found out

### 3.1 Why measure

The direct route was closed. The J-6's sound engine runs from an encrypted
firmware image, and this project made no attempt to get around that; Roland
documents nothing beyond the sound numbers. What remained was the instrument
itself: what it writes into its pattern files, and what it sounds like.

Roland describes the engine as a "Four-voice JUNO-60 synth engine" with
"64 ready-to-play synth presets derived from the original JUNO-60"
([product page](https://www.roland.com/global/products/j-6/)). The JUNO-60 of
1982 had, per voice, one oscillator offering pulse and saw, plus a square
sub-oscillator; a non-resonant high-pass and a 24 dB per octave resonant
low-pass filter; one envelope, one triangle LFO, and a chorus with two
buttons ([Wikipedia](https://en.wikipedia.org/wiki/Roland_Juno-60)). That is
the vocabulary of Standing's sheet, and of this report.

### 3.2 The method in six steps

1. **Harvest the defaults.** Choosing a sound on the J-6 writes its own
   FILTER, RESONANCE and ATTACK settings into the current pattern, and a
   backup copies the 64 patterns to a computer as small text files. Choosing
   sound n in pattern n, 64 times, then backing up, yields every sound's
   factory settings, exactly. There is no shortcut: a restored pattern that
   names a sound without its knob values gets 85 and 24, not the sound's own.
2. **Let the instrument play itself.** A script writes 64 pattern files, one
   per sound, with chosen knob settings and tempo, and the J-6 restores them.
   A computer then selects each pattern over MIDI, plays the same test notes
   and records the J-6's USB audio: a long note, a staccato note, a note two
   octaves up, a legato pair for the glide, and two velocities.
3. **Record each sound under several settings.** With the filter fully open
   the oscillator shows bare; with [ENVELOPE] at 0 and at 255 the envelope's
   extremes show; at 150 BPM anything tied to the tempo moves.
4. **Measure.** Every 10 ms, the analysis measures three things on each
   stereo channel: the pitch, the brightness (the spectral centroid, a
   sound's centre of gravity in frequency) and the share of even harmonics,
   which pulse-width modulation moves. An LFO shows as a periodic ripple in
   one of these traces; the chorus shows as a ripple in the difference between
   the two channels.
5. **Ask targeted questions.** Each open question got its own pattern set and
   its own notes: seven notes at irregular intervals to tell a free-running
   LFO from a restarting one; six overlapping notes to count the voices;
   sixteen settings of each knob to map it; four overlapping notes to tell one
   shared LFO from one per voice; notes of 20 and 90 seconds for the slowest
   modulations.
6. **Check the checker.** Before its verdicts were trusted, each experiment's
   analysis ran on synthetic recordings whose answers were known: a vibrato
   that restarts, one that runs freely, a sample and hold, a filter with known
   tracking, releases of known slope, an LFO that follows the tempo and one
   that does not.

### 3.3 Things we learned on the way

- **The LFOs are clocked by the sequencer.** Every LFO runs at a note value of
  the pattern tempo: at 100 BPM, from a whole-note triplet (0.625 Hz, on 7-8
  and 8-4) to a thirty-second (13.33 Hz, on 8-8). Change the tempo and every
  LFO follows. Their delays do not: a delay lasts the same number of seconds
  at any tempo.
- **A ring modulator made of an LFO.** The metallic timbre of 6-3 comes from
  an LFO running at a 1/128 note: 53.3 Hz at 100 BPM, an audio frequency. At
  60 BPM it drops to 32 Hz, and the timbre changes with it: on this sound,
  the tempo knob is a timbre control.
- **Free-running or restarting ?** If an LFO restarts with each note, every
  note begins with the same wobble; if it runs freely, each note catches it at
  a different point. Seven notes at irregular intervals, chosen so that no
  note value lines up with them by chance, tell the two apart: 33 LFOs run
  freely and 4 restart (5-6, 6-3, 8-7, 8-8). The restart happens only when no
  other key is held: chords and legato lines share one running LFO.
- **Four voices, and the bass is protected.** A fifth note steals the oldest
  voice, unless that voice holds the lowest note: the bass survives.
- **The hidden LFO.** 8-2's default FILTER is 251, the filter almost fully
  open. Its LFO sweeps a cutoff that already lies above the sound, which makes
  it inaudible and, through four rounds of analysis, invisible. At FILTER 140
  a 1/2T LFO appears at once. Standing's notes on 8-7 and 8-8, whose effect
  "dissapears for high Filter Settings", describe exactly this.
- **The ocarina's vibrato is a filter.** 6-8 is noise through a filter that
  rings at full resonance, so the pitch heard is the filter's. Its vibrato is
  therefore a filter LFO, which is how Standing listed it.
- **Ghosts of the chorus.** The chorus has its own slow LFO (0.543 Hz for I,
  0.879 Hz for II), whose harmonics leave faint periodic ripples in every
  measurement. Several "LFOs" of our first analysis were such harmonics
  (1-5's 3.26 Hz is the sixth harmonic of chorus I) or real LFOs mismeasured
  beside one. Notes of 20 s, whose finer resolution separates rates 0.1 Hz
  apart, sorted them out.
- **A third chorus.** Besides I and II, three sounds (2-1, 4-5 and 8-7) use a
  fast, shallow chorus whose LFO runs at 7.57 Hz whatever the tempo: closer to a
  vibrato that wobbles the two sides of the stereo image in opposite
  directions. It is the JUNO-60's heritage too: on the original, pressing I
  and II together gave a "secret" third mode (Roland's word), which the J-6
  hands to three presets.
- **Pulse-width modulation fools the spectrum and the pitch tracker.** A
  pulse whose width sweeps widely, averaged over time, has a saw's spectrum,
  which is why our first analysis called four PWM sounds saws. A sweep that
  moves one edge of the pulse also shifts every harmonic in frequency by the
  same small ratio, which a pitch tracker reads as vibrato. On 5-6, the
  pulse-width modulation alone could account for the 80 cents of vibrato
  measured (section 4.5.15).
- **Velocity squared.** The J-6's level follows the square of the MIDI
  velocity: 48 dB from velocity 8 to 127, 12 dB down at 64. Velocity leaves
  the brightness alone.
- **[ENVELOPE] is a macro, and not the same one everywhere.** It moves decay,
  sustain and release together, but what it does depends on the sound: plucks
  need it past the middle to sustain at all; "gated" leads and brass get a
  release only above the middle; pads already have a tail at the default
  (section 2.3). At the top, 1-3 takes 26 seconds to fall by 60 dB.
- **FILTER is relative.** The same FILTER value gives cutoffs octaves apart on
  different sounds: 1 kHz on an A2 needs 158 on 6-8, 78 on 2-7, 31 on 4-6 and
  less than 17 on 4-4. Each sound carries its own offset and keyboard
  tracking.
- **ATTACK doubles every 31 steps.** Below 68 the attack stays under 20 ms;
  from there it doubles every 31 steps, up to 1.7 s at 255.
- **Mistakes teach.** 5-8's slow LFO first read as restarting: a brightness
  spike at each note-on bent the trend removed from 3.5 s notes, and the
  remainder posed as an LFO locked to the note. Notes of 8 s, measured after
  the spike, show it free-running. 8-2's LFO had surfaced early as small
  brightness steps, which we dismissed as noise and buried under a stricter
  threshold; Standing had it right all along.

## 4. The full method

### 4.1 Repository map

| File | Role |
|---|---|
| `j6prm.py` | Reads and writes PRM pattern files: inspection, harvest of the defaults, generation of pattern sets (`--plan` with the built-in plans `sweep`, `filters`, `keysync`, `closing`, `final`, `finalfinal`, or a CSV file) |
| `j6capture.py` | Selects each pattern by Program Change, plays a stimulus through the ALSA sequencer, records the USB audio, and writes a JSON sidecar per take |
| `j6passes.sh` | Chains generation, restore and recording for named passes |
| `j6analyze.py` | Measures each sound from the four main passes and writes `measurements.csv` |
| `j6experiments.py` | Analyses the experiment passes, one CSV file (or more) per experiment |
| `j6synthetic.py` | Builds synthetic takes with known answers for every experiment |
| `j6compare.py` | Builds `J6_sounds_measured.xlsx`: the measurements beside the patch sheet |
| `report/` | Builds this README: `bash report/build.sh` fills `README.tmpl.md` with the tables generated from `results/` (`table.py`, which also writes `results/sounds.csv`, and `blocks.py`); `checks.py` repeats the ad hoc checks quoted in the text; `receipts.py` computes section 1's comparisons from Standing's sheet |

`results/` holds `defaults.csv` (the harvest), `measurements.csv` (the main
passes), `sounds.csv` (the results table of section 2.1, one field per
attribute), the workbook, and the experiments' files: `tempo.csv`,
`velocity.csv`, `poly.csv`, `sweep_filter.csv`, `sweep_resonance.csv`,
`sweep_attack.csv`, `sweep_env.csv`, `keysync.csv`, `filters.csv`,
`filters_curve.csv`, `filters_summary.csv`, `longtail.csv`, `longnote.csv`,
`keysync2.csv`, `chord.csv`, `verylong.csv`, `longnote2.csv`, `keysync3.csv`,
`destinations.csv`, `chorus.csv` and `envelope.csv`, with per-note (`*_notes.csv`) and jitter
(`*_jitter.csv`) companions; `results/synthetic/` holds the synthetic
validation's output. Each script's docstring defines its columns.

The scripts need Python 3.8 or later, numpy, scipy and soundfile (openpyxl
for the workbook), and for the recording alsa-utils and flac. On Debian:

```bash
sudo apt install alsa-utils flac python3-numpy python3-scipy python3-soundfile python3-openpyxl
```

### 4.2 Equipment and conventions

- One Roland J-6, system program 1.02, factory reset, connected by USB to a
  Debian workstation.
- Audio: the J-6's USB audio runs only at 44.1 kHz, 32-bit stereo (`S32_LE`).
  The takes are recorded at that rate, as 24-bit FLAC, so that ALSA does not
  resample.
- MIDI: the J-6's menu set to `CH` 1 (notes), `Pc.Ch` 16 (Program Change),
  `rxPc` On. Notes go through the ALSA sequencer: `j6capture.py` writes a
  small MIDI file and plays it with `aplaymidi`, so the kernel's queue does
  the timing, even while another program holds the raw MIDI port.
- [CHORD] must be unlit. It is lit after every power-on, and in chord mode
  each incoming note plays the chord registered to its key button (on a
  factory-reset unit, an A played F-A-C over A). Unlit, MIDI notes play
  single notes at their MIDI pitch.
- Note names follow Roland's numbering, C4 = 60: A2 is MIDI note 45, 110 Hz.
- Generated patterns have delay and reverb at 0 and the phrase style off.
  Their tempo is 100 BPM unless stated.

### 4.3 Pattern files and the harvest

Backup mode: hold [PLAY] while switching on, with USB connected. The J-6
appears as a drive with `BACKUP` and `RESTORE` folders. To restore, copy
files into `RESTORE`, eject, press [CHORD] and wait until the LEDs stop
blinking
([owner's manual](https://static.roland.com/manuals/J-6_manual_v102/eng/26654319.html)).

- One file per pattern, `J6_PTN01.PRM` to `J6_PTN64.PRM`. File n is the
  pattern labelled bank-number on the panel, with n = 8 × (bank - 1) + number.
- ASCII, LF line endings, 23 header lines `KEY<TAB>= value`, then `BAR 1` to
  `BAR 64`.

| Field | Meaning |
|---|---|
| `SOUND` | 0-63; sound bank-number = `SOUND // 8 + 1` - `SOUND % 8 + 1` (0 is 1-1) |
| `FILTER`, `RESONANCE` | 0-255, the [FILTER] knob and SHIFT + [FILTER] |
| `ENV`, `ATTACK` | 0-255, the [ENVELOPE] knob and SHIFT + [ENVELOPE] |
| `DELAY`, `REVERB` | effect levels; `DELAY_TIME`, `REVERV_TIME` (sic) their times |
| `TEMPO` | BPM × 100 |
| `LEVEL`, `TRANSPOSE` | pattern volume and transposition |
| `STYLE`, `VARIATION`, `STYLE_SW` | phrase settings, -1 / -1 / 0 in an initialised pattern |
| `BAR n` | `NOTE1`-`NOTE4` (MIDI note or -1), style, chord and pad data per bar |

The harvest: in each pattern, choose the sound with the same number, then
save the pattern (the J-6 discards unsaved edits when the pattern changes),
without touching [FILTER] or [ENVELOPE]. With `rxPc` On, this loop switches
the patterns, so that only choosing and saving remain by hand (`hw:4,0,0` is
the J-6's raw MIDI port as `amidi -l` lists it):

```bash
S=1; for n in $(seq $S 64); do l="$(( (n-1)/8+1 ))-$(( (n-1)%8+1 ))"; amidi -p hw:4,0,0 -S "CF $(printf '%02X' $((n-1)))"; read -p "pattern $l: choose sound $l, SAVE the pattern, then press Enter "; done
```

```bash
python3 j6prm.py defaults HARVEST/BACKUP --before ORIGINAL/BACKUP -o defaults.csv
```

`defaults` checks that every pattern holds its own sound, compares sounds 1-3
and 1-4 with the values read on the panel (121 / 79 and 128 / 144), and
reports whether choosing a sound also reset `ENV` and `ATTACK`. It did: 36
sounds carry their own `ATTACK`, and `ENV` is set to 128 for every sound,
even in patterns that held another value.

Two shortcuts were tried and failed. A Program Change on the note channel
does not select a sound. Restoring files that name the sound but omit
`FILTER` and `RESONANCE` (`generate --omit FILTER,RESONANCE`) gives every
pattern 85 / 24: the restore starts from an initialised pattern and applies
the lines present. It does apply generated files exactly as written, which
every later pass relies on.

### 4.4 Recording

Each pass is a pattern set generated by `j6prm.py generate`, restored, then
recorded by `j6capture.py` with a stimulus; `j6passes.sh` chains the three and
pauses only for what needs hands on the J-6 (backup mode, [CHORD], power).
Eleven sets were recorded:

| Set | Patterns | Stimulus, into folder | Question |
|---|---|---|---|
| `default` | the 64 sounds at their defaults | `full` | each sound as selected |
| `open` | FILTER 255, RESONANCE 0 | `full` | oscillator, pulse width, LFO, chorus without filtering |
| `env000` | ENV 0 | `short` | [ENVELOPE] at minimum |
| `env255` | ENV 255 | `short`, 10 s between patterns | [ENVELOPE] at maximum; plucks sustain |
| `tempo150` | defaults at 150 BPM | `full`; `velocity` on 1-3, 2-7, 4-4, 6-8; `poly` on 2-7, 4-7, 7-2 | what follows the tempo; level against velocity; number of voices |
| `sweep` | 16 steps (0, 17 ... 255) of FILTER on 6-8, RESONANCE on 2-7, ATTACK on 2-7, ENV on 1-3 | `full`; `envelope` for ENV | each knob's law |
| `keysync` | defaults; 8-7 at 150 BPM | `retrig` on the 38 sounds with an LFO that sustain | does each LFO restart with each note |
| `filters` | 6-8, 2-7, 4-6, 4-4: a FILTER 255 / RESONANCE 0 reference, then FILTER 17 ... 238 at RESONANCE 255; 1-3 at ENV 221, 238, 255 | `filter`; `longtail` | cutoff offset and keyboard tracking per sound; releases longer than 7.5 s |
| `closing` | 8-8 at 60 and 70 BPM; 5-3, 6-3, 8-2, 3-6, 5-5, 5-8, 7-2, 8-3 at 100 and 60 BPM; 6-5, 5-6 | `longnote`; `retrig8` into `keysync2`; `chord` | tempo sync of 8-8; exact rates and phase of the unclear sounds; shared or per-voice LFOs |
| `final` | 8-2 at its defaults (100 and 60 BPM) and at FILTER 140 and 100; 5-5 at FILTER 255 / RES 0, 120 / 0 and its defaults | `verylong`; `longnote` into `longnote2` | an LFO hidden by 8-2's open filter; a filter movement on 5-5 against the noise of its source |
| `finalfinal` | 5-8 at 100 and 60 BPM; 8-1 and 5-6 at 100 BPM as controls | `retrig8long` into `keysync3` | does 5-8's slow LFO restart with each note |

The stimuli (times in seconds from the first note-on; gate is the note's
length):

| Stimulus | Notes | Measures |
|---|---|---|
| `full` | A2 at 0 (gate 6); A2 at 9 (0.15); A4 at 11.5 (1.5); A2 at 15 (0.8) then E3 at 15.85 (1.2); A3 at velocity 40 at 19.05 and at 127 at 21.05 (0.8 each) | envelope, LFO, chorus; staccato; keyboard tracking; glide; velocity |
| `short` | the first two notes of `full` | envelope extremes |
| `envelope` | A2 (6), then A2 staccato at 14 | long tails of the ENV sweep |
| `velocity` | A3 at velocities 8, 16 ... 120, 127, one per second (0.5) | level and brightness against velocity |
| `poly` | C3, E3, G3, B3, D4, F4 entering 0.5 s apart, all released at 4 s | voices and voice stealing |
| `retrig` | seven A2 notes of 3.5 s at 0, 4.64, 9.16, 13.83, 18.40, 22.91, 27.49 | LFO phase at each note-on |
| `retrig8` | eight A2 notes of 3.5 s at 0, 4.33, 9.92, 14.49, 19.08, 24.67, 30.15, 35.79 | the same at 60, 70 and 100 BPM |
| `retrig8long` | eight A2 notes of 8 s at 0, 9.46, 19.73, 29.91, 39.34, 48.7, 59.05, 68.88 | slow LFOs past their envelope |
| `filter` | A1, A2, A3, A4, 2 s each, 2.5 s apart | resonant peak against each note |
| `longtail` | one A2 of 6 s, 30 s of tail | releases of many seconds |
| `longnote` | one A2 of 20 s | exact rates; the chorus's own rate; tempo tests |
| `verylong` | one A2 of 90 s | modulations down to 0.056 Hz |
| `chord` | A2, D3, F#3, B3 entering at 0, 0.25, 0.51, 1.05, held to 9 s | one LFO for all voices or one per voice |

Each take has a JSON sidecar recording the pattern and its settings, the
planned and actual time of every note, the recording format and the peak
level; `session.json` logs each run, and `hw_params.txt` the J-6's native
audio formats. The commands, run from the folder holding the scripts and the
backups `Factory_backup/` and `Harvest_backup/`:

```bash
bash j6passes.sh default open env000 env255
```

```bash
bash j6passes.sh tempo150 sweep keysync filters closing final finalfinal
```

```bash
python3 j6analyze.py captures -o results/measurements.csv
```

```bash
python3 j6experiments.py captures -o results
```

```bash
python3 j6compare.py results/measurements.csv results/defaults.csv REFERENCE.xlsx results/J6_sounds_measured.xlsx
```

`REFERENCE.xlsx` is Standing's sheet, which is not distributed here.

### 4.5 Signal processing

#### 4.5.1 Aligning each take

The recorder's start-up time varies by tens of milliseconds, so each take is
aligned on its own audio. The power of the signal is computed on 5 ms frames,
and the first note's onset is found by sliding the stimulus's whole note
pattern along the take's onset curve (the rise of the level over 10 ms) in
2 ms steps and keeping the best fit. When the pre-roll is digital silence, as
it was on every take of the main passes, the first non-zero sample gives
the onset exactly and the fit serves as a check (`Take._onset` in `j6analyze.py`).

#### 4.5.2 Fourier transforms: windows, lengths, resolution

Every spectrum is a discrete Fourier transform of a Hann-windowed segment,
zero-padded to a power of two. Two quantities must be kept apart:

- **Resolution** is set by the segment's duration T. The Hann window's main
  lobe spans ±2/T and its 6 dB bandwidth is 2/T, so two components closer
  than about 2/T merge. A 6 s note separates modulation rates about 0.3 Hz
  apart, a 20 s note 0.1 Hz, a 90 s note 0.02 Hz.
- **Bin spacing** is set by the transform length N: fs / N. Zero padding
  interpolates the spectrum between the resolution's limits. It adds no
  resolution, but it locates an isolated peak far more finely than 1/T
  (refined further by a parabola through the logarithm of the three bins
  around the peak).

The Hann window trades a main lobe twice as wide as the rectangular window's
for sidelobes 31 dB down that fall by 18 dB per octave
([Harris 1978](https://doi.org/10.1109/PROC.1978.10837)): in this material a
weak modulation beside the chorus's lines matters more than the last bit of
resolution.

| Use | Segment | FFT length | Bin spacing | Where |
|---|---|---|---|---|
| spectral centroid | 40 ms to 0.5 s | 2^14 | 2.69 Hz | `centroid` |
| pitch, brightness and even-share tracks | 80 ms, every 10 ms | 2^15 | 1.35 Hz | `track` |
| glide | 40 ms, every 5 ms | 2^15 | 1.35 Hz | `glide` |
| oscillator make-up | 100 ms, every 25 ms | 2^16 | 0.67 Hz | `oscillator` |
| general spectra | the segment | 2^17 | 0.34 Hz | `spectrum` |
| resonant peak, resonance gains, single-note check | 0.4-1.2 s | 2^18 | 0.17 Hz | `resonant_peak`, `harmonic_gains`, `single_note` |
| audio-rate components | up to 40 s | 2^21 | 0.021 Hz | `audio_components` |
| modulation spectra of the tracks (sampled at 100 Hz) | the note | 2^15 or 2^16 | 0.0031 or 0.0015 Hz | `lfo`, `peak_height` |
| the chorus LFO (stereo difference, sampled at 100 Hz) | the note | 2^17 | 0.00076 Hz | `measured_chorus_lfo` |

#### 4.5.3 Three traces per channel

Every 10 ms, on each channel, an 80 ms frame gives three numbers. The pitch
is found by summing the spectrum at the first four harmonics of candidates
±120 cents around the expected note, in 1-cent steps. The brightness is the
base-2 logarithm of the spectral centroid between 20 Hz and 16 kHz, so that
it reads in octaves. The even share is the energy of harmonics 2, 4, 6 and 8
over that of harmonics 1 to 8: 0 for a square, 0.23 for a saw, approaching
0.5 for a very narrow pulse.

```python
# j6analyze.py, track()
    nfft = 1 << 15
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    grid_c = np.arange(-120, 121, 1.0)
    w = np.hanning(n)
    rows = []
    for i in range(0, len(sig) - n, h):
        per = []
        for ch in (0, 1):
            fr = sig[i:i + n, ch]
            ...
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
```

#### 4.5.4 Finding an LFO

Each trace is cleaned (gaps interpolated, a quadratic trend removed) and
transformed. A peak between 0.3 and 18 Hz counts as an LFO if it stands at
least 8 times above the median of that range, if the component it isolates
moves both channels in phase (correlation above 0.5: the chorus moves them in
opposite phase), and if its swing (5th to 95th percentile) exceeds 6 cents of
pitch, 0.1 octave of brightness or 0.05 of even share; smaller swings include
the frame analysis's own ripple. Bands of ±0.35 Hz around the chorus's
modulation rate, half and twice it, are excluded; an LFO inside such a band
reads at its edge, which `lfo_flags` reports (the 3.17, 2.53 and 0.53 Hz
readings in `measurements.csv`).

```python
# j6analyze.py, lfo()
    for i in order[:200]:
        rate = f[i]
        if (any(abs(rate - t) < 0.2 for t in tried) or any(abs(rate - e) < guard for e in exclude)
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
            edge = any(abs(abs(rate - e) - guard) < 0.015 for e in exclude)
            return float(rate), float(prom), float(np.percentile(bm, 95) - np.percentile(bm, 5)), mean, edge
```

Vibrato and pulse width are read on the open pass, where every harmonic is
present; the filter LFO on the default pass, where the cutoff sits where the
sound has it. Plucks too short on both are read on the env255 pass, after a
check that its notes are single notes (`single_note`: at least 70 % of the
energy on one harmonic series). One LFO moving several things shows in several
traces at one rate; the weaker reading is then dropped when it is small.

#### 4.5.5 Chorus

Chorus off is exact mono: the stereo difference is digital zero. With chorus
on, the ratio of the difference's power to the sum's pulses as the delays
sweep, twice per cycle of the chorus LFO. Its spectrum, on 10 ms frames,
peaks at 1.09 Hz for chorus I and 1.76 Hz for chorus II; a peak 4 times above
the median names the mode. Measured more finely on the 20 s notes, the chorus
LFOs run at 0.5415-0.5428 Hz (I) and 0.8792-0.8810 Hz (II) and do not follow
the tempo.

This test left 7 sounds undecided ("on"): an LFO of the sound or a short
note can drown the pulsing of the stereo image. A second test
(`chorus_modes` in `j6experiments.py`) uses another property of a chorus:
it sweeps the delays of the two channels in opposite directions, so their
pitch and brightness move in opposite phase at the chorus LFO's rate,
whereas the J-6's LFOs move both channels together. The left-minus-right
difference of the pitch and brightness traces cancels everything the
channels share. Its spectra, from every 6 s A2 note available (default,
open, env255 and tempo150 passes), each divided by its median over
0.25-12 Hz and averaged, are read at the three chorus LFO rates; the
tallest wins if it stands 6 times above the median and twice above the
next. On 2-1, 4-5 and 8-7 the difference moves at 7.57 Hz (at 100 as at
150 BPM on 4-5 and 8-7; 2-1 sustains only at ENV 255, recorded at 100 BPM):
a third chorus mode, faster and shallower (the stereo difference lies 11 to
20 dB under the sum, against 3 to 8 dB for I and II).

The three modes are the JUNO's. On the JUNO-60, pressing I and II together
calls up "a 'secret' third mode for exaggerated movement with a distinctive
swirl", in Roland's words for its software recreation
([Roland](https://www.roland.com/global/products/rc_juno-60_chorus/)). A
circuit analysis of the JUNO-60 chorus
([pendragon-andyh/Juno60](https://github.com/pendragon-andyh/Juno60/blob/master/Chorus/README.md))
measures its rates and quotes the service notes:

| Mode | J-6, measured | JUNO-60, measured in that analysis | JUNO-6 service notes, as quoted there |
|---|---|---|---|
| I | 0.543 Hz | 0.513 Hz | 0.4 Hz |
| II | 0.879 Hz | 0.863 Hz | 0.67 Hz |
| I+II (fast) | 7.57 Hz | 9.75 Hz | 8.06 Hz |

I and II sit within 6 % and 2 % of the JUNO-60 figures. The third mode runs
22 % slower than that analysis measured, and 6 % slower than the JUNO-6's
figure; the JUNO-60 service notes, according to the same analysis, print
"1Hz", probably a typo for 10 Hz. The analysis also gives the third mode a
delay swept over 3.3-3.7 ms, against 1.66-5.35 ms for I and II (its table
gives no unit; seconds are implied), which is consistent with the
shallowness measured here, and calls it "similar to a Leslie rotary
speaker". It labels that mode's outputs "Mono" without saying what
that means; on the J-6 the two channels still move in opposite phase, with
a stereo image much narrower than in I and II. The departure, if any, is in
use rather than substance: the J-6's patterns carry no chorus setting (their
files have no chorus field), so the mode comes with the sound, and the third
mode, hidden on the JUNO-60, comes with three of its presets.

#### 4.5.6 Oscillator make-up

On the A4 note of the open pass, 100 ms frames every 25 ms follow the pitch
and accumulate the power of 24 components on a grid of half the note's
frequency, which holds a sub-oscillator too. The averaged levels are then
classified. A square has odd harmonics only, the third at -9.5 dB. A saw has
every harmonic at 1/k (-6, -9.5, -12 dB for the 2nd to 4th). A pulse of
width d has harmonics proportional to sin(πkd)/k, so the ratio of the first
two gives d = arccos(a2 / a1) / π. A sub-oscillator shows as components below
the oscillator following a square's law. The noise share is the energy
farther than 1.5 % (at least 22 Hz) from every component, over the energy
near them.

Averaging has a blind spot. The power of harmonic k of a pulse of width d is
proportional to sin²(πkd)/k². If d sweeps evenly over a wide range, the mean
of sin²(πkd) is close to 1/2 for every k, and the average spectrum falls as
1/k, exactly like a saw. Numerically, a width swept from 5 % to 50 % averages
to within 0.3 dB of a saw's harmonic levels up to the 8th harmonic, and
within 1.2 dB from 10 % to 50 %. The PWM sounds of section 2 owe their "saw
spectrum" to this.

#### 4.5.7 Envelopes and glide

The amplitude envelope is read on the open pass, where the filter does not
shape the level, from the power on 5 ms frames smoothed over 50 ms: attack to
-3 dB of the smoothed peak, decays to -20 and -40 dB, sustain as the level
over the last 0.45 s of the 6 s note, and release times after the note-off.
The long-tail experiment follows releases down to -150 dBFS: below its
signal the J-6 outputs digital silence, so no noise floor stops them. The
glide is the time after which the second note of the A2-E3 pair stays within
40 cents of E3 (more on sounds with vibrato), counted only if the pitch
passes through intermediate values for at least 10 ms on 40 ms frames.

#### 4.5.8 LFO delay

The modulation trace is band-passed around the LFO rate (±rate/2) by zeroing
FFT bins, after padding with as many zeros as it has samples: without the
padding, the circular transform folds the end of the note onto its start.
The depth envelope is the magnitude of the analytic signal (Hilbert
transform), and the delay is the time at which it reaches half its median
over 50-85 % of the note. A delay shorter than one LFO cycle cannot be told
from the filter's own rise and reads 0.

#### 4.5.9 Does an LFO restart with each note ?

Each note's trace, from 1 s after its note-on (past the delays, at most
0.9 s), is fitted by least squares with a sinusoid at a fixed rate plus a
constant. The fit's phase is taken twice: against the note-on, and against
the start of the take, which is the clock a free-running LFO would follow.
Agreement among the notes' phases is measured by their concentration, the
mean resultant length of circular statistics
([Wikipedia](https://en.wikipedia.org/wiki/Directional_statistics)): 1 when
all phases are equal, about 0.3 when they are random.

```python
# j6experiments.py
def phase_fit(t, s, f):
    m = np.column_stack([np.cos(2 * np.pi * f * t), np.sin(2 * np.pi * f * t), np.ones_like(t)])
    (a, b, *_), *_ = np.linalg.lstsq(m, s, rcond=None)
    return math.hypot(a, b), math.atan2(b, a)


def concentration(angles) -> float:
    return float(abs(np.mean(np.exp(1j * np.asarray(angles)))))

# the verdict, per modulation
verdict = ("restarts with each note" if r_note >= 0.8 and r_note - r_take >= 0.3 else
           "free-running" if r_take >= 0.9 and r_take - r_note >= 0.3 else "unclear")
```

The test works only if one hypothesis predicts scattered phases where the
other predicts equal ones. With notes at regular intervals, a free-running
LFO whose period divides the interval would meet every note at the same
phase and pass for a restarting one. The onsets were therefore chosen by
search so that, for every note value at the tempi used, the phases a
free-running LFO would show at the note-ons have a concentration of at most
0.46 (`retrig`), 0.43 (`retrig8`) or 0.40 (`retrig8long`). A first choice of
90 BPM for 8-8 would have given 0.82 at its 12 Hz and was abandoned.

Uniformly random phases reach a concentration of 0.9 with probability 0.0007
for seven notes and 0.0002 for eight, and 0.8 with probability 0.006 and
0.003 (Monte Carlo, two million draws). The rate search below tries a handful
of independent candidates, which multiplies these odds by a few at most.

The rate matters as much as the phase. A rate error of δ shifts the phase
against the take by 2πδt, which grows over the 30 s of a take; the note-on
phases are immune to it. The rate is therefore searched for where the
take-referenced phases agree best (weighted by amplitude): first among the
note values within 0.45 Hz of the per-note estimate, then within ±0.06 Hz of
it in 0.002 Hz steps. The search stays narrow because onsets about 4.6 s
apart make rates 0.22 Hz apart look alike (an alias: 0.22 Hz × 4.6 s is one
cycle). Harmonics of the chorus LFO (2 to 12 times its rate, within 0.03 Hz)
are skipped. Where the long notes had measured a sound's rates, the phases
are measured at those rates instead.

#### 4.5.10 Does a modulation follow the tempo ?

On a 20 s or 90 s note, every peak between five cycles per note (0.25 or
0.056 Hz) and 18 Hz standing 8 times above the median and moving both
channels in phase is listed, each named by its nearest note value and checked
against the harmonics of the chorus LFO measured on the same note (within
0.015 Hz plus 0.002 Hz per harmonic). For a sound recorded at two tempi, each
modulation found at one tempo is looked for at the other, at the rate scaled
by the tempo ratio and at the same rate: the taller peak (8 times the median
at least, and twice the other) decides "follows the tempo" or "fixed rate".

#### 4.5.11 Steps: sample and hold, and square LFOs

A sample and hold changes the brightness in jumps. The size of the
frame-to-frame jumps of the log centroid (40 ms frames, every 10 ms) is
searched for a periodicity; a peak 6 times above the median (4 in the
averaged spectra of several notes), at a note value, counts. The edges of a
square or saw LFO produce the same signature, which is how 8-2's and 5-8's
LFOs were found. The measure is used only when no periodic modulation is
found, since the jumps of a deep vibrato would pass for steps.

#### 4.5.12 Audio-rate components

Components of the long note's spectrum (2^21 points, 0.021 Hz bins) between
15 Hz and 0.95 times the fundamental, within 10 dB of the strongest
component and more than 0.5 Hz from a sub-oscillator's lines, betray an
audio-rate modulation. On 6-3 they sit at 53.317 Hz at 100 BPM and 31.991 Hz
at 60 BPM: 32 cycles per beat. The 6.81 Hz "LFO" read on 6-3 earlier is a
beat between its products and the note's harmonics, and vanishes at 60 BPM.

#### 4.5.13 Locating the resonant peak

A resonant peak is located by dividing each harmonic's level by the same
harmonic in a reference take of the same sound with FILTER 255 and RESONANCE
0, on 2^18-point spectra from 0.8 s after each note-on (past the filter
envelope's sweep). The largest gain is the peak if it stands 6 dB above the
median gain of the harmonics below it and 12 dB above that of the harmonics
beyond 1.5 times its frequency: a lowpass resonance attenuates what lies above
it, while a bump with nothing falling off above it is a difference between
takes. A parabola through the gains against log frequency refines it. Peaks
on the 6th harmonic or above and below 10 kHz are used; lower, the harmonics
sample a sharp peak too coarsely (errors of 100-500 cents on synthetic data).

```python
# j6experiments.py, resonant_peak()
    if gain - np.median(g[valid[valid < j]]) < 6:
        return None, gain
    # a lowpass resonance attenuates what lies well above it; a bump with
    # nothing falling off above it is a difference between the takes
    above = valid[(valid + 1) >= 1.5 * (j + 1)]
    if not len(above) or gain - np.median(g[above]) < 12:
        return None, gain
    x = np.log2(f0 * np.array([j, j + 1, j + 2]))
    c2, c1, _ = np.polyfit(x, g[j - 1:j + 2], 2)
    xv = -c1 / (2 * c2) if c2 < 0 else x[1]
    return float(2 ** min(max(xv, x[0]), x[2])), gain
```

Keyboard tracking is the median, over FILTER values, of the slope of log2
(peak) against log2(note) for notes at least an octave apart; the curve
brings each peak to A2 with that tracking.

#### 4.5.14 A filter movement, or a noisy source ?

A noisy source through a resonant filter makes the brightness jitter even if
the filter stands still. Two measures separate the cases by comparing takes
of one sound at several FILTER settings. The brightness jitter is split into
what moves both channels together and what differs between them. The
harmonics' own level fluctuations (1-45 Hz, octaves rms, 100 ms frames) are
measured with the filter fully open, where only the source's fluctuation
remains, and at the sound's setting: what the setting adds is the filter's
movement. A first version used the correlation between harmonics; on 8-2,
whose filter LFO is plain at FILTER 140, it gave 0.13, because a resonant
cutoff sweeping across the harmonics moves those above and below it in
opposite directions.

#### 4.5.15 What does each LFO move ?

At each sound's settled LFO rate, the swing of pitch, brightness and even
share in a band of ±rate/4 is measured with the filter at the sound's
setting and fully open (`destinations` in `j6experiments.py`). A filter LFO's
swing collapses when the filter opens, and so does the pitch "vibrato" a
resonant sweep induces (2-8: 24.5 cents at its setting, 0.9 open). A vibrato
or a pulse-width modulation, both in the oscillator, stays.

Neither trace is a clean signature on its own. The even share also moves
with the chorus, and on several sounds the ±rate/4 band holds a harmonic of
the chorus LFO (on 7-1 and 7-4, 2.64 Hz, three times chorus II's 0.879 Hz).
A deep filter LFO still acts at FILTER 255: 8-1's brightness swings by 0.93
octave at its setting and still 0.51 fully open, while its even share does
not move at all. The "pulse, PWM" label of section 2's oscillator column
therefore requires both an even-share swing and a brightness swing that
survive the open filter; the "pulse width" entries of its LFO column rest on
the even share alone, with this caveat.

A pulse-width modulation can also move the pitch reading. For a pulse of
width d with one fixed edge, harmonic k has the complex amplitude
e^(-iπkd) sin(πkd) / (πk): its phase is -πkd. If d moves, every harmonic's
frequency shifts by -k d'(t) / 2 Hz, the same ratio -d'(t) / (2 f0) for all
of them, and a pitch tracker reads a vibrato. (Equivalently, a pulse is the
difference between a saw and a delayed copy of it; sweeping the width slides
the copy's phase, which momentarily detunes it against the first saw.) For
5-6, a
width swinging ±0.2 at 4.44 Hz, which its even-share swing of 0.5 suggests,
predicts about 88 cents peak to peak; 79-84 cents were measured. This
explanation is not demonstrated: the width's actual swing is unknown, and the
estimate fits less well on the other PWM sounds.

### 4.6 Intermediate results

The tables below are generated from the CSV files in `results/` by
`report/blocks.py`.

**FILTER on 6-8** (RESONANCE 255, the filter ringing; peak read directly):

@@BLOCK FILTER sweep@@

The ringing peak moves one octave per 14.4 steps between 85 and 170 at A2
(a fit below 2 kHz; 14.65 up to 187), then flattens towards 13 kHz (A2) and
16 kHz (A4). Below 85 the filter is closed.
A4 puts the peak two octaves above A2: full keyboard tracking.

**RESONANCE on 2-7** (FILTER 69), gains against RESONANCE 0:

@@BLOCK RESONANCE sweep@@

The peak's gain is given at the nearest harmonic. It saturates above 170-204,
while the fundamental loses 5-6 dB, the passband loss of a four-pole filter
with resonance feedback. No self-oscillation on this sound.

**ATTACK on 2-7**:

@@BLOCK ATTACK sweep@@

**ENV on 1-3** (brightness as spectral centroid):

@@BLOCK ENV sweep@@

**Long releases on 1-3** (30 s of tail):

@@BLOCK Long releases@@

The release is a clean exponential down to -140 dBFS and stops lengthening at
238.

**Velocity** (A3, levels against velocity 127):

@@BLOCK Velocity@@

The brightness scatter on 2-7 and 4-4 is their chorus and LFO caught at
different phases, not a trend.

**Polyphony** (2-7: six held notes entering 0.5 s apart; level of each note's
fundamental against the loudest, "." before the note starts):

@@BLOCK Polyphony@@

E3 falls silent when D4 enters, and G3 when F4 enters, while C3, the oldest
but lowest, keeps sounding; 4-7 and 7-2 behave alike.

**Tempo** (every LFO found at both 100 and 150 BPM; "track" is the trace it
was found on):

@@BLOCK Tempo@@

22 of 24 keep their note value; the two others are on 8-4, whose 0.625 Hz LFO
a 6 s note resolves poorly. The 7-1 and 7-4 ratios of 1.428 are 2.222 Hz read
as 3.17 Hz at 150 BPM, at the edge of a chorus band: the true rate there is
3.333 Hz, a ratio of 1.500.

**FILTER per sound** (RESONANCE 255, resonant peak brought to A2 with each
sound's tracking):

@@BLOCK FILTER per sound@@

6-8 agrees with the direct reading of its self-oscillation within 3 %. 4-4
and 4-6 rise one octave per about 31 steps near 17, steepening to 16-18 near
68-85, with the same ratios step by step, as if they shared one curve at
different offsets. From about 102 on 4-4, 119 on 4-6 and 153 on 2-7, the
response up to 12 kHz stays within a few dB of FILTER 255.

**LFO phase** (concentrations of the phases at the note-ons; "brightness
steps" is the step measure of 4.5.11; when two measures of one LFO disagree,
both are shown):

@@BLOCK LFO phase@@

The free-running rates sit within 0.1 % of a note value. 8-8 restarts at 60,
70 and 100 BPM, and its 13.33 Hz is the same on A2 and A4, so it is an LFO
and not a beat between detuned oscillators.

**Closing pass**: each modulation of a long note looked for at the other
tempo:

@@BLOCK Closing pass@@

An "unclear" row is a modulation whose peaks at the other tempo decided
nothing (neither candidate 8 times the median and twice the other): 6-3's
beat, and secondary readings on 3-6, 7-2 and 8-3 beside their main LFOs.

**Chord test** (four notes held together; each voice read on its own
fundamental and second harmonic, which no other note shares):

@@BLOCK Chord test@@

**Final pass, 8-2** (90 s notes at FILTER 251, 20 s notes at 140 and 100):

@@BLOCK Final pass: 8-2@@

**Final pass, jitter** (5-5 and 8-2 at several FILTER settings):

@@BLOCK Final pass: brightness@@

On 5-5 the harmonics fluctuate by 0.52 octave rms with the filter open, 0.52
at FILTER 120 and 0.56 at its defaults: the filter adds under a tenth of the
source's own fluctuation. On 8-2, revealing the filter LFO raises the same
measure from 0.51 (FILTER 251) to 1.33 (FILTER 140).

**Finalfinal pass** (5-8 on 8 s notes, measured from 1 s and fitted from 2 s
after each note-on; 8-1 and 5-6 as controls):

@@BLOCK Finalfinal pass@@

Replaying the old measurement on these notes reproduces the earlier false
restart: the first 3.5 s fitted from 1 s give 0.91 against the note-on,
while a 3.5 s window starting 2 s in gives 0.95 against the clock.

**Chorus modes** (section 4.5.5: heights of the left-minus-right spectra
at the three chorus LFO rates, against their median; the sounds the main
analysis had left undecided):

@@BLOCK Chorus modes@@

**[ENVELOPE] per sound** (sustain at the end of a 6 s A2 note against its
peak, and release to -20 dB after the note-off, followed for 3 s; ENV 0 was
recorded in chord mode, which leaves levels and times usable):

@@BLOCK ENVELOPE per sound@@

**Destinations** (swing at the LFO rate; "a / b" is the filter at the
sound's setting / fully open; plucks on the ENV 255 pass):

@@BLOCK Destinations@@

### 4.7 Dead ends and corrections

In the order they happened.

1. **The firmware.** The update's application image is encrypted. This
   project did not attempt to circumvent that and measured the instrument
   instead.
2. **Harvest shortcuts.** A Program Change on the note channel does not
   select a sound, and restoring pattern files that name a sound but omit its
   knob values loads 85 / 24 (section 4.3). The 64 sounds were chosen by hand.
3. **48 kHz.** The first pilot recorded at 48 kHz, and ALSA resampled the
   J-6's 44.1 kHz by linear interpolation. The capture script now reads the
   native rate from the device and records at it.
4. **Chord mode.** [CHORD] is lit after every power-on, and three passes were
   recorded with each test note playing a chord. The default and env255 passes
   were recorded again; env000 serves for envelope times only. The batch
   script now asks for [CHORD] to be unlit, and env255 takes are checked for
   single notes before use.
5. **ATTACK forced to 0.** The first pattern sets set ATTACK to 0, before the
   harvest showed that 36 sounds carry their own. The default pass was
   recorded again with the harvested values.
6. **The delay estimator's wrap-around.** The band-pass by FFT is circular:
   the end of a note folded onto its start and faked or masked delays.
   Zero padding changed 42 values. A rule tried next (measure from the minimum
   after the onset transient) produced 12 false delays and was reverted.
7. **Chorus ghosts.** The first analysis reported LFOs at 3.17, 2.53 and
   0.53 Hz: rates at the edges of the bands excluded around the chorus, where
   a nearby LFO reads. The phase experiment found the true rates (3.333, 2.5,
   0.556 or 0.625 Hz), and `lfo_flags` now marks such readings. Likewise 2-1,
   read at 3.17 Hz, measures 3.330 Hz when the exclusion is lifted.
8. **Snapping and aliasing.** Snapping every rate to the nearest note value
   misnamed 6-3's 6.81 Hz and 7-7's 4.40 Hz, which is the 5th harmonic of the
   chorus II LFO. A wide search for the most coherent rate then found aliases
   0.22 Hz away. The search became narrow and skips chorus harmonics
   (4.5.9).
9. **The filter curve.** A single exponential fit gave 4-6 48.7 steps per
   octave, because a stationary bump of 6-8 dB near 5.5 kHz posed as a
   resonant peak. The lowpass-skirt rule (4.5.13) and a curve without assumed
   shape replaced it. Keyboard tracking read from brightness misled too: with
   an open filter brightness follows the oscillator, and 4-4 read 0.63 where
   the resonant peak gives 0.0.
10. **Endless releases.** The long-tail analysis stopped its release search
    at -100 dBFS, a limit meant for a noise floor; the J-6 outputs digital
    silence below its signal, so the -60 dB point was never found. The limit
    is now -150 dBFS.
11. **The chord test** first locked onto the third harmonic of the chorus LFO;
    chorus harmonics are now excluded. Its first rule for declaring a result
    was too strict for 5-6.
12. **Long notes.** The sidelobes of strong peaks were counted as modulations
    until suppressed; the jumps of a deep vibrato were read as sample and
    hold until the step measure was confined to sounds with nothing periodic.
13. **8-2's steps.** The closing pass found 1.251 Hz brightness steps on 8-2
    at 10.5 times the median. They were dismissed as spurious and the step
    threshold was raised to 12 to drop them. The final pass then revealed the
    hidden 1/2T LFO they came from, and the threshold went back to 6.
14. **5-5's correlation test** was invalid (4.5.14) and was replaced by the
    size of the harmonics' fluctuation.
15. **5-8's false restart.** On 3.5 s notes, 5-8's 0.556 Hz LFO read as
    restarting on its brightness level and as free-running on its steps.
    Fitting a trend inside the window (linear, quadratic) was tried and
    rejected: it absorbed part of other slow LFOs (7-8, 8-4, 5-3) and shifted
    the choice between aliased rates without removing the bias. A synthetic
    sound with a brightness spike at each note-on did not reproduce the error,
    because its LFO was deeper than 5-8's 0.14 octave. Notes of 8 s settled
    it (4.6, finalfinal pass).
16. **A rounding regression.** The harmonic-fluctuation code broke on a
    4,409-sample frame where 4,410 were expected; frames are now cut to
    length.
17. **Report generation.** The first table of LFO destinations picked 2-6's
    7.498 Hz (the third harmonic of its 2.5 Hz LFO) and 7-2's 5.0 Hz (its
    pulse width at twice the rate) as their rates; it now takes the first
    decisive reading per experiment. Two delays from questionable detections
    (1-7, 5-4) nearly reached the results table, which now takes delays from
    the main passes only.
18. **PWM read as saws.** The oscillator classification called the PWM
    sounds saws (4.5.6). The table now says "pulse, PWM" where the even
    harmonics and the brightness both swing with the filter fully open
    (4.5.15).
19. **Chorus "on".** The first chorus test left seven sounds undecided, and
    the report first printed them as "chorus on". The opposite-phase test
    (4.5.5) settled four as chorus I and found the third mode on the other
    three.
20. **4-5's vibrato.** Its 2-cent pitch ripples at 2.22 and 4.44 Hz were
    first put down to harmonics of the chorus LFO, on the assumption that
    4-5 used chorus I or II. With its chorus at 7.57 Hz, that explanation
    fell; at 150 BPM the ripples move to 3.33 and 6.67 Hz, the same note
    values: a tempo-synced vibrato, as Standing heard.

### 4.8 Synthetic validation

`j6synthetic.py` builds, for every experiment, takes in the format
`j6capture.py` records, each with one right answer:

```bash
python3 j6synthetic.py synthetic
```

```bash
python3 j6experiments.py synthetic -o synthetic_results
```

The outputs are kept in `results/synthetic/`.

@@BLOCK Synthetic validation@@

The longnote2 case shows the separation of 4.5.14 at work: a random filter
movement on a noisy source raises the shared jitter (0.150 against 0.005
between channels) and the harmonics' fluctuation (0.771 against 0.049 with
the filter open), while the same source behind a static filter shows neither
(0.006, 0.066). Its random movement also produces spurious peaks at 4.317,
1.276 and 1.933 Hz, none on a note value.

The synthetic sample and hold sits close to the step detector's threshold:
with the random seeds 3, 7 and 11 its steps reach 4.55, 3.90 and 4.48 times
the median, against a threshold of 4. The threshold was not lowered, because
on real sounds the 5th harmonic of the chorus II LFO (4.40 Hz) would then pass
for a sample and hold; the generator uses seed 3, and this marginal case is
recorded here.

### 4.9 Limits and open questions

- One unit, on system program 1.02. Another firmware may differ.
- Octave and sub-oscillator are ambiguous for mixed waveforms: a square plus
  a saw at one pitch has the same harmonic magnitudes as a sub-oscillator plus
  a saw an octave up.
- Averaged spectra cannot tell a widely swept pulse from a saw (4.5.6); the
  envelope-driven PWM of 3-5, 6-1 and 8-5 is not tested.
- Pitch readings on sounds with pulse-width modulation may be the pulse's own
  phase motion rather than vibrato (4.5.15).
- The plucks (1-4, 1-6, 2-1, 2-4) were measured only with [ENVELOPE] at 255;
  their LFO phase is not tested, and 1-4's slow movement is unverified.
- Rates below 0.3 Hz are not detected on 6 s notes; the 90 s notes reach
  0.056 Hz, but only on 8-2.
- A vibrato under 6 cents escapes the main analysis (4-5's 2-cent vibrato was
  found only by comparing note values at two tempi); so does a filter
  movement under a tenth of a noisy source's jitter (5-5).
- 4-2's "Wide LFO Filter Sweep for low Filter/Envelope values" is not tested
  at low settings.
- Whether the LFOs of 6-3, 8-7 and 8-8 also restart when notes join held ones
  is not tested; on 5-6 the LFO does not.
- The "pulse width" readings of the LFO column rest on the even share, which
  the chorus also moves (4.5.15); 7-2 and 7-3 are doubtful.
- The key tracking column of `measurements.csv`, read from brightness,
  misreads sounds whose filter is open (4-4 reads 0.63 there and 0.0 from the
  resonant peak, 2-7 0.78 and 0.50); the filter sweep's values prevail.

### 4.10 Reproducing it

Everything runs from one experiment folder holding the scripts, the backups
`Factory_backup/` and `Harvest_backup/` (with `defaults.csv`), and the
`passes/` and `captures/` folders the scripts create. Every restore
overwrites all 64 patterns: keep a backup of your own.

1. Harvest the defaults (section 4.3) and back up.
2. Set the J-6's MIDI menu (section 4.2).
3. Generate a pass, for example the default one, from a template pattern with
   empty bars (a blank pattern of banks 3-8 after a factory reset):

   ```bash
   python3 j6prm.py generate --template Factory_backup/BACKUP/J6_PTN17.PRM --defaults Harvest_backup/defaults.csv --out passes/default
   ```

   Copy `passes/default/RESTORE/*.PRM` into the J-6's `RESTORE` folder,
   eject, press [CHORD], wait for the LEDs, switch off, switch on normally,
   and make sure [CHORD] is unlit.
4. Record a pilot, check that the J-6 moves to the pattern announced (if it
   is one off, `--pc-offset 1` or `-1`), then the whole pass, which skips the
   takes already recorded:

   ```bash
   python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE --outdir captures/default --patterns 1..3 --flac
   ```

   ```bash
   python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE --outdir captures/default --patterns 1..64 --flac
   ```

5. Or let `j6passes.sh` chain all of it for the named passes (section 4.4).
   `j6experiments.py --only chorus,envelope` runs chosen analyses instead of
   every one whose folder exists.
   `J6_MOUNT` overrides the drive's mount point (default `/media/$USER/J-6`),
   and `J6_PATTERNS=1..3` limits a run to a few patterns.

Troubleshooting:

- **arecord says "Device or resource busy"**: the desktop sound server holds
  the J-6's audio. Set its card profile to off with `pactl` or pavucontrol
  while recording.
- **amidi says "Device or resource busy"**: a sequencer client is connected
  to the J-6, for example a browser page using Web MIDI. `aconnect -l` hides
  some clients; `cat /proc/asound/seq/clients` lists them all. The default
  `--midi seq` route works regardless, but close any program that could send
  MIDI to the J-6 while recording.
- **Every note plays a chord**: [CHORD] is lit.
- **Silent takes**: check the J-6's `CH` setting and its volume.
- **Every take sounds the same**: `rxPc` is off, or `Pc.Ch` differs from
  `--pc-channel`.

### 4.11 Sources

- Nick Standing (JabunAudio), *Roland J-6 Preset Sounds Settings Ver. 1.0*,
  with the video
  [Roland AIRA Compact J-6 Comprehensive Preset Sounds Patch Sheet! (Free download or donation)](https://www.youtube.com/watch?v=z6hoNwWadR8).
- Roland, [J-6 product page](https://www.roland.com/global/products/j-6/)
  ("Four-voice JUNO-60 synth engine"; "64 ready-to-play synth presets derived
  from the original JUNO-60").
- Roland, [J-6 owner's manuals](https://www.roland.com/global/support/by_product/j-6/owners_manuals/)
  and the
  [backup and restore page of the v1.02 manual](https://static.roland.com/manuals/J-6_manual_v102/eng/26654319.html).
- Wikipedia, [Roland Juno-60](https://en.wikipedia.org/wiki/Roland_Juno-60).
- Roland, [JUNO-60 Chorus software effect](https://www.roland.com/global/products/rc_juno-60_chorus/)
  (the "secret" third mode).
- pendragon-andyh, [Juno60: Chorus](https://github.com/pendragon-andyh/Juno60/blob/master/Chorus/README.md)
  (rates, delays and service-note figures of the JUNO-60 and JUNO-6 chorus).
- F. J. Harris, "On the use of windows for harmonic analysis with the
  discrete Fourier transform", *Proceedings of the IEEE* 66 (1), 1978,
  pp. 51-83, [doi:10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837).
- Wikipedia, [Directional statistics](https://en.wikipedia.org/wiki/Directional_statistics)
  (mean resultant length).
- Wikipedia, [Standing on the shoulders of giants](https://en.wikipedia.org/wiki/Standing_on_the_shoulders_of_giants).
