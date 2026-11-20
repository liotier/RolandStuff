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
| LFO rate "Slow" (9 sounds), "Mid" (24), "Fast" (7) | 0.556-1.667 Hz, 1.25-5 Hz and 4.44-13.33 Hz at 100 BPM: three ordered classes that overlap only at their edges. |
| 6-3, "Square Ring Mod", LFO rate "Max" | A modulation at 53.33 Hz, a 1/128 note at 100 BPM: an LFO at audio rate, which is what a ring-modulator timbre is made of. |
| 2-1: "LFO retriggers at 1/8th notes ... once Envelope Control is past 50%" | 3.330 Hz with [ENVELOPE] at 255; an eighth note at 100 BPM is 3.333 Hz. |
| Footnote: "Sustains once Envelope control is past 50%" | On 1-3 a sustain appears between ENV 119 and 136, between 47 % and 53 % of the knob's travel; at 255 all ten plucks sustain. |
| 6-8: "Keyboard tracked self-oscilating filtered noise" | Noise through a filter that rings at RESONANCE 255 and follows the keyboard at 1.00 octave per octave. |
| 8-7 and 8-8: the effect "dissapears for high Filter Settings" | The mechanism that hid 8-2's filter LFO through four rounds of analysis: at its default FILTER of 251 the LFO sweeps a cutoff that already lies above the sound. |
| Attack "None", "Fast", "Mid", "Slow" | Median attack times of 3 ms, 21 ms, 0.13 s and 1.9 s. |
| Release "None", "Fast", "Mid", "Slow" | Median release times (to -20 dB) of 9 ms, 40 ms, 0.26 s and 1.0 s. |
| Cutoff "Low", "Mid", "High"; resonance "Low", "Mid", "High", "Max" | Median default FILTER of 27, 117.5 and 160.5; median default RESONANCE of 0, 43, 158.5 and 255. |
| Noise absent, "Low", "Mid", "High" | Median noise share of -32.85, -31.0, -27.0 and -10.85 dB: the same order. |
| Chorus I, II or off | Agreement on 64 of 64 sounds. |
| Glide | Agreement on the 60 sounds where glide can be measured. |
| LFO delay | Agreement on 34 of the 37 sounds where an LFO was measured. |
| Keyboard tracking of the filter | 6-8 and 2-7 tracked (1.00 and 0.50 octave per octave), 4-4 not (0.0); 4-6, marked untracked, follows at 0.31. |
| A filter LFO on 2-7, 6-4, 6-8, 7-6, 8-2, 8-3 and 8-7, none on 5-3 | Our first analysis disagreed on all eight. Later experiments proved him right on all eight. |
| A vibrato on 7-3 | Missed at first, then found: 16 cents at a dotted sixteenth. |
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
- **4-5 and 4-6**, a vibrato ("Low" and "Mid"): none above our 6-cent
  threshold. 4-5 shows pitch ripples of 2 cents at 2.2 and 4.4 Hz, but they
  fall within the resolution of the chorus's harmonics.
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

| Sound<br>(name by Standing) | Oscillator,<br>chorus | Attack / sustain /<br>release, glide | LFO: moves,<br>rate at 100 BPM,<br>phase, delay | FILTER<br>RES<br>ATTACK | Notes |
|---|---|---|---|---|---|
| **1-1** Mellow Sub Octave Pluck | pulse 31&nbsp;%<br>chorus I | 0&nbsp;ms / -13&nbsp;dB / 71&nbsp;ms | none | 85<br>24<br>0 |  |
| **1-2** Square Pluck | square<br>chorus Off | 0&nbsp;ms / -19&nbsp;dB / 2&nbsp;ms | none | 85<br>23<br>0 |  |
| **1-3** Mellow Mallet | square<br>chorus Off | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 239&nbsp;ms | none | 121<br>79<br>0 |  |
| **1-4** Noisy Mellow Pluck | square, noise<br>chorus Off | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 424&nbsp;ms | filter ?<br>slow, 0.3-0.6&nbsp;Hz<br>phase not tested | 128<br>144<br>0 | seen only with ENV 255: a 0.23 octave brightness swing at 0.556&nbsp;Hz (1/2.); unverified |
| **1-5** Noisy Octave Pluck | pulse 43&nbsp;%, noise<br>+1 oct, sub -2&nbsp;dB<br>chorus I | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 234&nbsp;ms | none | 78<br>97<br>0 | a 3.26&nbsp;Hz reading is chorus I's 6th harmonic |
| **1-6** Harpsichord | pulse 30&nbsp;%<br>+1 oct, sub +2&nbsp;dB<br>chorus Off | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 244&nbsp;ms | pulse width, pitch<br>1/4T (2.5&nbsp;Hz)<br>phase not tested<br>delay 0.55&nbsp;s | 137<br>29<br>0 | measured with ENV 255, where it sustains |
| **1-7** Chorus Clavinet | pulse 16&nbsp;%<br>chorus on | 3&nbsp;ms / -10&nbsp;dB / 30&nbsp;ms | pulse width<br>1/4T (2.5&nbsp;Hz)<br>free-running | 0<br>28<br>0 | spreadsheet: pulse width fixed |
| **1-8** Chorus Harp | square<br>+1 oct, sub, same level<br>chorus I | 7&nbsp;ms / pluck,<br>-20&nbsp;dB in 1541&nbsp;ms | none | 27<br>33<br>0 |  |
| **2-1** Staccato Steel Drum | pulse 34&nbsp;%, noise<br>chorus on | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 75&nbsp;ms | filter, pulse width<br>1/8 (3.333&nbsp;Hz)<br>phase not tested | 95<br>31<br>0 | 3.330&nbsp;Hz with ENV 255 (first read at 3.17&nbsp;Hz, a chorus band edge); Standing: 1/8th notes |
| **2-2** Bright Detuned Saw Pluck | saw<br>+1 oct, sub +3&nbsp;dB<br>chorus II | 0&nbsp;ms / pluck,<br>-20&nbsp;dB in 688&nbsp;ms | none | 0<br>7<br>0 |  |
| **2-3** Synthy 80s Clean Guitar | pulse 31&nbsp;%<br>+1 oct, sub -1&nbsp;dB<br>chorus on | 3&nbsp;ms / pluck,<br>-20&nbsp;dB in 803&nbsp;ms | none | 65<br>120<br>18 |  |
| **2-4** Gliding Noisy Pluck | pulse 39&nbsp;%, noise<br>+1 oct, sub +2&nbsp;dB<br>chorus II | 7&nbsp;ms / pluck,<br>-20&nbsp;dB in 334&nbsp;ms<br>glide 15&nbsp;ms | pulse width<br>1/8. (2.222&nbsp;Hz)<br>phase not tested | 110<br>179<br>38 | measured with ENV 255 |
| **2-5** Octave Splash | pulse 44&nbsp;%, noise<br>+1 oct, sub -2&nbsp;dB<br>chorus II | 35&nbsp;ms / pluck,<br>-20&nbsp;dB in 474&nbsp;ms | none | 87<br>158<br>91 |  |
| **2-6** Plectrum Wind | pulse 18&nbsp;%, noise<br>chorus on | 7&nbsp;ms / 0&nbsp;dB / 227&nbsp;ms<br>glide 1127&nbsp;ms | filter<br>1/4T (2.5&nbsp;Hz)<br>free-running | 121<br>183<br>2 | a 7.5&nbsp;Hz pitch ripple is the LFO's 3rd harmonic |
| **2-7** Plectrum Mellotron Chorus | pulse 40&nbsp;%<br>+1 oct, sub -1&nbsp;dB<br>chorus II | 0&nbsp;ms / -1&nbsp;dB / 14&nbsp;ms | filter<br>1/8 (3.333&nbsp;Hz)<br>free-running<br>delay 0.67&nbsp;s | 69<br>0<br>0 | its pitch ripple is the filter's pull |
| **2-8** Air Harp | pulse 37&nbsp;%<br>chorus I | 0&nbsp;ms / -9&nbsp;dB / 698&nbsp;ms | filter<br>1/16. (4.444&nbsp;Hz)<br>free-running<br>delay 0.37&nbsp;s | 121<br>55<br>0 |  |
| **3-1** Ambient Piano | pulse 33&nbsp;%<br>chorus I | 2&nbsp;ms / -28&nbsp;dB / - | none | 122<br>0<br>0 |  |
| **3-2** Synth Vibraphone | square<br>chorus Off | 0&nbsp;ms / -10&nbsp;dB / 429&nbsp;ms | none | 119<br>102<br>0 |  |
| **3-3** Hammered Dulcimar | pulse 44&nbsp;%<br>+1 oct, sub -2&nbsp;dB<br>chorus II | 5&nbsp;ms / -22&nbsp;dB / 690&nbsp;ms | none | 146<br>34<br>0 |  |
| **3-4** Saw Piano | saw<br>chorus I | 0&nbsp;ms / -11&nbsp;dB / 630&nbsp;ms | none | 106<br>0<br>0 |  |
| **3-5** Brass Pluck | saw spectrum, envelope<br>PWM per Standing<br>chorus I | 12&nbsp;ms / -17&nbsp;dB / 9&nbsp;ms | none | 115<br>43<br>58 |  |
| **3-6** Resonant Blown Glass | square<br>+1 oct, sub -8&nbsp;dB<br>chorus I | 80&nbsp;ms / -6&nbsp;dB / 850&nbsp;ms | filter<br>1/4 (1.667&nbsp;Hz)<br>free-running | 75<br>115<br>117 | first suspected to be a chorus harmonic |
| **3-7** Acid Saw | saw<br>chorus Off | 21&nbsp;ms / -6&nbsp;dB / 18&nbsp;ms | none | 84<br>126<br>77 |  |
| **3-8** Bright Trumpet | saw<br>chorus Off | 15&nbsp;ms / -3&nbsp;dB / 66&nbsp;ms | pitch<br>1/16. (4.444&nbsp;Hz)<br>free-running<br>delay 0.85&nbsp;s | 0<br>0<br>67 |  |
| **4-1** Octave PWM Lead | saw spectrum,<br>PWM per Standing<br>+1 oct, sub -3&nbsp;dB<br>chorus II | 12&nbsp;ms / -3&nbsp;dB / 8&nbsp;ms | pulse width<br>1/2T (1.25&nbsp;Hz)<br>free-running | 64<br>0<br>61 |  |
| **4-2** Gliding Pulse Lead I | pulse 42&nbsp;%<br>+1 oct, sub +5&nbsp;dB<br>chorus I | 15&nbsp;ms / -1&nbsp;dB / 6&nbsp;ms<br>glide 15&nbsp;ms | none | 110<br>170<br>13 | Standing: wide filter LFO at low FILTER; not tested there |
| **4-3** Slow PWM Lead | pulse, PWM<br>chorus II | 14&nbsp;ms / -1&nbsp;dB / 35&nbsp;ms | pulse width<br>1/2. (0.556&nbsp;Hz)<br>free-running | 255<br>0<br>0 |  |
| **4-4** Vibrato Saw Lead | saw<br>chorus II | 4&nbsp;ms / -1&nbsp;dB / 150&nbsp;ms | pitch, 145 cents<br>1/8T (5&nbsp;Hz)<br>free-running<br>delay under 0.2&nbsp;s | 121<br>64<br>0 |  |
| **4-5** Gliding Pluse Lead II | pulse 45&nbsp;%<br>chorus on | 6&nbsp;ms / 0&nbsp;dB / 3&nbsp;ms<br>glide 55&nbsp;ms | none | 255<br>0<br>0 | Standing: slight vibrato; none found |
| **4-6** Octave Dirty Strings | pulse 38&nbsp;%, noise<br>+1 oct, sub -6&nbsp;dB<br>chorus II | 42&nbsp;ms / -1&nbsp;dB / 183&nbsp;ms | none | 169<br>39<br>91 | Standing: vibrato with delay; none found |
| **4-7** Octave Mixed Lead | pulse 37&nbsp;%<br>+1 oct, sub -6&nbsp;dB<br>chorus II | 9&nbsp;ms / -1&nbsp;dB / 40&nbsp;ms | none | 152<br>14<br>0 |  |
| **4-8** Blown Octave Square | square<br>+1 oct, sub -1&nbsp;dB<br>chorus II | 20&nbsp;ms / -6&nbsp;dB / 6&nbsp;ms | none | 205<br>120<br>84 |  |
| **5-1** Thick Attack Lead | saw<br>+1 oct, sub -5&nbsp;dB<br>chorus on | 2&nbsp;ms / -8&nbsp;dB / 9&nbsp;ms | pulse width<br>1/4T (2.5&nbsp;Hz)<br>free-running | 147<br>18<br>57 |  |
| **5-2** The Fake Slim Shady | pulse 23&nbsp;%<br>+1 oct, sub -7&nbsp;dB<br>chorus Off | 0&nbsp;ms / -6&nbsp;dB / 183&nbsp;ms | pitch<br>1/16. (4.444&nbsp;Hz)<br>free-running | 158<br>92<br>0 |  |
| **5-3** Ya-ee Choir | saw<br>+1 oct, sub -2&nbsp;dB<br>chorus II | 13&nbsp;ms / -1&nbsp;dB / 1027&nbsp;ms | pulse width<br>1/2 (0.833&nbsp;Hz)<br>free-running | 119<br>255<br>0 | first read at 2.59&nbsp;Hz, a chorus product |
| **5-4** Dark Strings | pulse 40&nbsp;%<br>chorus II | 14&nbsp;ms / -2&nbsp;dB / 245&nbsp;ms | pulse width<br>1/8 (3.333&nbsp;Hz)<br>free-running | 133<br>24<br>58 | the spreadsheet lists no LFO |
| **5-5** Angry Cat | saw, noise<br>chorus II | 11&nbsp;ms / 0&nbsp;dB / 636&nbsp;ms<br>glide 649&nbsp;ms | none | 51<br>138<br>36 | Standing: fast filter LFO; its jitter is the noisy source |
| **5-6** Brass Choir | pulse, PWM<br>chorus II | 27&nbsp;ms / -4&nbsp;dB / 712&nbsp;ms | pulse width, pitch<br>1/16. (4.444&nbsp;Hz)<br>restarts | 79<br>60<br>82 | restarts only when no other key is held; the voices share it; the pitch swing may be the PWM's own phase motion |
| **5-7** Whoa Flute | saw<br>+1 oct, sub +4&nbsp;dB<br>chorus Off | 67&nbsp;ms / -8&nbsp;dB / 4&nbsp;ms<br>glide 15&nbsp;ms | filter<br>1/8T (5&nbsp;Hz)<br>free-running | 98<br>114<br>113 |  |
| **5-8** Honky Tonk Clav | saw spectrum,<br>PWM per Standing<br>+1 oct, sub +3&nbsp;dB<br>chorus II | 3&nbsp;ms / -8&nbsp;dB / 9&nbsp;ms | filter or pulse width<br>1/2. (0.556&nbsp;Hz)<br>free-running | 27<br>20<br>0 | first misread as restarting |
| **6-1** PWM Envelope | saw spectrum, envelope<br>PWM per Standing<br>chorus I | 3&nbsp;ms / -12&nbsp;dB / 20&nbsp;ms | none | 136<br>2<br>0 |  |
| **6-2** Solo String | saw<br>chorus Off | 47&nbsp;ms / 0&nbsp;dB / 258&nbsp;ms | pitch<br>1/8T (5&nbsp;Hz)<br>free-running<br>delay 0.88&nbsp;s | 169<br>0<br>97 |  |
| **6-3** Square Ring Mod | square, modulated at 53&nbsp;Hz<br>chorus II | 13&nbsp;ms / -1&nbsp;dB / 79&nbsp;ms | filter (per Standing), at audio rate<br>1/128 (53.33&nbsp;Hz)<br>restarts | 161<br>39<br>0 | the ring-modulator timbre; it changes with the tempo |
| **6-4** Mellow Trumpet | saw<br>chorus Off | 25&nbsp;ms / -5&nbsp;dB / 101&nbsp;ms | filter<br>1/16. (4.444&nbsp;Hz)<br>free-running<br>delay hidden | 53<br>0<br>82 |  |
| **6-5** Horn | saw<br>chorus Off | 10&nbsp;ms / -4&nbsp;dB / 71&nbsp;ms | filter<br>1/8T (5&nbsp;Hz)<br>free-running<br>delay 0.86&nbsp;s | 134<br>0<br>61 |  |
| **6-6** Square Chorus Lead | square<br>chorus I | 12&nbsp;ms / -4&nbsp;dB / 9&nbsp;ms | none | 48<br>113<br>0 |  |
| **6-7** Clarinet | square<br>chorus Off | 21&nbsp;ms / -3&nbsp;dB / 107&nbsp;ms | pitch<br>1/8T (5&nbsp;Hz)<br>free-running<br>delay 0.54&nbsp;s | 130<br>43<br>72 |  |
| **6-8** Ocarina | noise through a ringing filter<br>chorus Off | 60&nbsp;ms / 0&nbsp;dB / 17&nbsp;ms | filter, heard as pitch<br>1/8 (3.333&nbsp;Hz)<br>free-running | 112<br>255<br>103 | the filter rings: its LFO sounds as vibrato |
| **7-1** PWM String Ensemble I | pulse, PWM<br>+1 oct, sub +3&nbsp;dB<br>chorus II | 42&nbsp;ms / -1&nbsp;dB / 233&nbsp;ms | pulse width<br>1/8. (2.222&nbsp;Hz)<br>free-running | 207<br>7<br>80 |  |
| **7-2** Saw String Ensemble | saw<br>+1 oct, sub +7&nbsp;dB<br>chorus II | 126&nbsp;ms / -2&nbsp;dB / 357&nbsp;ms | pitch, pulse width ?<br>1/4T (2.5&nbsp;Hz)<br>free-running | 166<br>17<br>122 | the spreadsheet lists no LFO; a 6-cent vibrato; the even harmonics move at twice its rate |
| **7-3** Brass Ensemble | saw, noise<br>chorus II | 198&nbsp;ms / -5&nbsp;dB / 209&nbsp;ms | pitch, pulse width ?<br>1/16. (4.444&nbsp;Hz)<br>free-running | 129<br>15<br>154 | Standing: vibrato, saw without PWM; with the filter open its even harmonics and brightness still swing |
| **7-4** PWM String Ensemble II | pulse, PWM<br>+1 oct, sub -2&nbsp;dB<br>chorus II | 46&nbsp;ms / -1&nbsp;dB / 1080&nbsp;ms | pulse width<br>1/8. (2.222&nbsp;Hz)<br>free-running | 135<br>17<br>89 |  |
| **7-5** Ghost Pad | saw, noise<br>chorus I | 399&nbsp;ms / 0&nbsp;dB / 256&nbsp;ms | pitch<br>1/32. (8.889&nbsp;Hz)<br>free-running | 116<br>0<br>183 |  |
| **7-6** Evolving Filter Pad I (Bright) | pulse 25&nbsp;%<br>chorus II | 46&nbsp;ms / -10&nbsp;dB / 247&nbsp;ms | filter, pitch<br>1/4T (2.5&nbsp;Hz)<br>free-running<br>delay 0.82&nbsp;s | 182<br>0<br>97 |  |
| **7-7** Evolving Filter Pad II (Mellow) | square<br>+1 oct, sub +3&nbsp;dB<br>chorus II | 346&nbsp;ms / -1&nbsp;dB / 1894&nbsp;ms | filter<br>1/8 (3.333&nbsp;Hz)<br>free-running<br>delay hidden | 98<br>97<br>179 | delay hidden by the filter envelope |
| **7-8** Evolving Filter Pad III (Mellow Slow and Wide) | saw<br>chorus II | 211&nbsp;ms / -10&nbsp;dB / 906&nbsp;ms | filter<br>1/1T (0.625&nbsp;Hz)<br>free-running | 152<br>64<br>155 | a whole-note triplet |
| **8-1** Evolving Filter Pad IV (Bright Slow and Wide) | saw<br>+1 oct, sub -14&nbsp;dB<br>chorus II | 19&nbsp;ms / -4&nbsp;dB / 155&nbsp;ms | filter, pitch<br>1/2. (0.556&nbsp;Hz)<br>free-running | 183<br>132<br>69 |  |
| **8-2** Evolving Filter Pad V (Squishy I) | pulse 42&nbsp;%<br>chorus II | 327&nbsp;ms / -5&nbsp;dB / 289&nbsp;ms<br>glide 160&nbsp;ms | filter, pulse width<br>1/2T (1.25&nbsp;Hz)<br>free-running | 251<br>144<br>195 | hidden by its nearly open FILTER (251) |
| **8-3** Evolving Filter Pad VI (Squishy II) | pulse 34&nbsp;%<br>chorus I | 235&nbsp;ms / -8&nbsp;dB / 257&nbsp;ms | filter, pitch<br>1/2 (0.833&nbsp;Hz)<br>free-running<br>delay hidden | 212<br>81<br>165 | first misread as a 2.53&nbsp;Hz vibrato |
| **8-4** Evolving Filter Pad VII (Blossoming I) | saw<br>+1 oct, sub -10&nbsp;dB<br>chorus II | 2001&nbsp;ms / -9&nbsp;dB / 570&nbsp;ms | filter, pitch<br>1/1T (0.625&nbsp;Hz)<br>free-running | 84<br>64<br>255 | a whole-note triplet |
| **8-5** Evolving Filter Pad VII (Blossoming II) | saw spectrum, envelope<br>PWM per Standing<br>sub -13&nbsp;dB<br>chorus I | 1880&nbsp;ms / 0&nbsp;dB / - | none | 116<br>178<br>255 |  |
| **8-6** Decaying Filter Pad (Blossoming III) | pulse 33&nbsp;%<br>+1 oct, sub +3&nbsp;dB<br>chorus I | 7&nbsp;ms / -34&nbsp;dB / 33&nbsp;ms | pitch<br>1/8T (5&nbsp;Hz)<br>free-running<br>delay 0.91&nbsp;s | 157<br>148<br>0 |  |
| **8-7** Sample and Hold Pad | pulse 28&nbsp;%<br>chorus on | 173&nbsp;ms / 0&nbsp;dB / 1541&nbsp;ms | filter, sample and hold<br>1/16. (4.444&nbsp;Hz)<br>restarts | 28<br>159<br>146 | tested at 150 BPM (6.67&nbsp;Hz) |
| **8-8** Plectrum Tremolo Pad | saw<br>+1 oct, sub, same level<br>chorus II | 6&nbsp;ms / -10&nbsp;dB / 746&nbsp;ms | filter<br>1/32 (13.333&nbsp;Hz)<br>restarts | 105<br>255<br>0 | a 1/32 at 60, 70 and 100 BPM |

How to read it:

- **Sound**: the panel number (bank-number), with the name Standing gave the
  sound.
- **Oscillator, chorus**: the harmonic make-up of an A4 note with the filter
  fully open (FILTER 255, RESONANCE 0), averaged over the note; the waveform
  on the first line, octave and sub-oscillator on the second, the chorus on
  the last. "pulse 31 %" is a pulse that is high for 31 % of its period, from
  the ratio of its first two harmonics. "+1 oct": the oscillator sounds an
  octave above the note played. "sub -3 dB": a square sub-oscillator one
  octave below the oscillator, 3 dB under it. "noise": the energy between the
  harmonics exceeds -28 dB relative to them (a threshold placed after seeing
  the sheet; the median shares in section 1 do not depend on it). Averaged
  over time, a pulse whose width sweeps widely has the spectrum of a saw:
  "pulse, PWM" marks the four sounds where, with the filter fully open, both
  the even harmonics and the brightness still swing at the LFO's rate; "saw
  spectrum, PWM per Standing" marks those where this could not be shown.
  Chorus I or II is told by the rate at which the stereo image pulses
  (1.09 Hz for I, 1.76 Hz for II); "on" when the mode could not be told; Off
  is exact mono.
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
| [ENVELOPE] moves decay, sustain and release together. On 1-3: a pluck from 0 to 119 (decay to -20 dB from 35 to 215 ms), a sustain from 136 (-18.7 dB) to 255 (-0.7 dB), and releases up to 26.4 s to -60 dB. At 255 every pluck sustains; at 0 the releases shrink to tens of milliseconds. | 1-3: 16 steps, then three notes with 30 s of tail. All 64 sounds at ENV 0 (median release to -20 dB: 29 ms) and at 255 (the ten plucks sustain at -0.7 to -2.4 dB). | `sweep_env.csv`, `longtail.csv`, `measurements.csv` |
| Chorus I and II are free-running LFOs at 0.543 and 0.879 Hz; chorus off is exact mono. | The stereo difference measured on 20 s notes. | `longnote.csv` |
| MIDI notes play at their pitch when [CHORD] is unlit, and [CHORD] is lit after every power-on. Tuning is within 0.3 cent of A440. | A2 measured at 110.02 Hz. | `measurements.csv` |
| Glide belongs to each voice: a voice glides from the last pitch it played. | The starting pitch of a glide changes with the voice that plays it. | `measurements.csv` |
| The J-6 ignores the MIDI message All Sound Off. | Releases ring on through it. | - |

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
- **[ENVELOPE] is a macro.** It moves decay, sustain and release together.
  On 1-3, below 47 % of its travel the sound is a pluck whose decay lengthens
  with the knob; above 53 % a sustain appears and the release lengthens, up to
  26 seconds to fall by 60 dB. At the top of its travel every pluck sustains.
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
| `report/` | Builds this README: `bash report/build.sh` fills `README.tmpl.md` with the tables generated from `results/` (`table.py`, `blocks.py`); `checks.py` repeats the ad hoc checks quoted in the text; `receipts.py` computes section 1's comparisons from Standing's sheet |

`results/` holds `defaults.csv` (the harvest), `measurements.csv` (the main
passes), the workbook, and the experiments' files: `tempo.csv`,
`velocity.csv`, `poly.csv`, `sweep_filter.csv`, `sweep_resonance.csv`,
`sweep_attack.csv`, `sweep_env.csv`, `keysync.csv`, `filters.csv`,
`filters_curve.csv`, `filters_summary.csv`, `longtail.csv`, `longnote.csv`,
`keysync2.csv`, `chord.csv`, `verylong.csv`, `longnote2.csv`, `keysync3.csv`
and `destinations.csv`, with per-note (`*_notes.csv`) and jitter
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
the tempo. Wikipedia's JUNO-60 article gives 0.4 and 0.6 Hz for the
original's chorus; no primary source was found to compare with.

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

| FILTER | level, A2 (dBFS) | ringing peak, A2 (Hz) | level, A4 (dBFS) | ringing peak, A4 (Hz) |
|---|---|---|---|---|
| 0 | -78.7 | - | -66.7 | - |
| 17 | -77.1 | - | -65.0 | - |
| 34 | -73.7 | - | -61.8 | - |
| 51 | -69.3 | - | -57.3 | 30 |
| 68 | -63.7 | - | -51.8 | 58 |
| 85 | -57.3 | 30 | -45.7 | 120 |
| 102 | -50.5 | 67 | -40.1 | 268 |
| 119 | -43.7 | 155 | -36.7 | 622 |
| 136 | -38.5 | 362 | -35.5 | 1429 |
| 153 | -36.0 | 817 | -35.2 | 3272 |
| 170 | -35.4 | 1751 | -35.2 | 7027 |
| 187 | -35.2 | 3578 | -35.4 | 14144 |
| 204 | -35.1 | 6221 | -39.3 | 15872 |
| 221 | -35.2 | 9753 | -39.3 | 15252 |
| 238 | -35.2 | 12453 | -39.4 | 15950 |
| 255 | -35.2 | 13186 | -39.4 | 15542 |

The ringing peak moves one octave per 14.4 steps between 85 and 170 at A2
(a fit below 2 kHz; 14.65 up to 187), then flattens towards 13 kHz (A2) and
16 kHz (A4). Below 85 the filter is closed.
A4 puts the peak two octaves above A2: full keyboard tracking.

**RESONANCE on 2-7** (FILTER 69), gains against RESONANCE 0:

| RESONANCE | fundamental, A2 (dB) | peak, A2 (dB) | at (Hz) | fundamental, A4 (dB) | peak, A4 (dB) | at (Hz) |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0.0 | 110 | 0.0 | 0.0 | 440 |
| 17 | -1.0 | 2.9 | 550 | -0.5 | 3.1 | 880 |
| 34 | -1.7 | 5.1 | 550 | 0.8 | 4.4 | 1320 |
| 51 | -2.2 | 6.3 | 550 | -0.2 | 6.0 | 1320 |
| 68 | -2.8 | 8.4 | 550 | -0.8 | 7.2 | 1320 |
| 85 | -3.2 | 9.3 | 550 | -0.7 | 8.9 | 1320 |
| 102 | -3.7 | 10.6 | 660 | -2.3 | 9.4 | 1320 |
| 119 | -3.9 | 11.7 | 770 | -1.4 | 11.4 | 1320 |
| 136 | -4.2 | 12.9 | 660 | -3.4 | 11.6 | 1320 |
| 153 | -4.5 | 14.0 | 660 | -1.9 | 14.5 | 1320 |
| 170 | -4.6 | 15.1 | 660 | -3.1 | 14.8 | 1320 |
| 187 | -5.0 | 14.9 | 660 | -3.1 | 16.1 | 1320 |
| 204 | -5.2 | 16.6 | 660 | -2.8 | 16.7 | 1320 |
| 221 | -5.5 | 15.3 | 660 | -4.1 | 16.5 | 1320 |
| 238 | -5.8 | 15.2 | 660 | -4.9 | 15.8 | 1320 |
| 255 | -6.2 | 14.7 | 660 | -4.9 | 15.6 | 1320 |

The peak's gain is given at the nearest harmonic. It saturates above 170-204,
while the fundamental loses 5-6 dB, the passband loss of a four-pole filter
with resonance feedback. No self-oscillation on this sound.

**ATTACK on 2-7**:

| ATTACK | to -20 dB (ms) | to -10 dB (ms) | to -3 dB (ms) | to peak (ms) | sustain (dB) | release to -20 dB (ms) |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 5 | 15 | -1.4 | 11 |
| 17 | 0 | 0 | 2 | 12 | -2.2 | 9 |
| 34 | 0 | 0 | 0 | 10 | -2.8 | 11 |
| 51 | 0 | 2 | 7 | 17 | -3.1 | 8 |
| 68 | 2 | 12 | 17 | 27 | -4.1 | 8 |
| 85 | 7 | 17 | 32 | 42 | -5.4 | 14 |
| 102 | 17 | 32 | 57 | 82 | -6.5 | 9 |
| 119 | 26 | 46 | 86 | 131 | -6.9 | 8 |
| 136 | 41 | 76 | 141 | 201 | -7.5 | 8 |
| 153 | 54 | 114 | 224 | 314 | -7.7 | 11 |
| 170 | 74 | 164 | 308 | 453 | -8.2 | 5 |
| 187 | 125 | 215 | 430 | 614 | -8.1 | 7 |
| 204 | 147 | 292 | 571 | 916 | -7.6 | 4 |
| 221 | 229 | 434 | 808 | 1262 | -8.1 | 1 |
| 238 | 325 | 634 | 1233 | 1851 | -8.2 | 2 |
| 255 | 432 | 876 | 1704 | 2806 | -8.0 | 4 |

**ENV on 1-3** (brightness as spectral centroid):

| ENV | decay to -20 dB (ms) | to -40 dB (ms) | sustain (dB) | release to -20 dB (ms) | to -40 dB (ms) | staccato release to -20 dB (ms) | brightness at 0.05 / 1 / 5 s (Hz) |
|---|---|---|---|---|---|---|---|
| 0 | 35 | 65 | - | - | - | - | 231 / - / - |
| 17 | 50 | 95 | - | - | - | - | 231 / - / - |
| 34 | 65 | 125 | - | - | - | 37 | 232 / - / - |
| 51 | 85 | 165 | - | - | - | 69 | 238 / - / - |
| 68 | 105 | 210 | - | - | - | 81 | 250 / - / - |
| 85 | 135 | 269 | - | - | - | 113 | 269 / - / - |
| 102 | 170 | 334 | - | - | - | 152 | 284 / 519 / - |
| 119 | 215 | 419 | - | - | - | 186 | 297 / 544 / - |
| 136 | - | - | -18.7 | 325 | - | 326 | 335 / 239 / 239 |
| 153 | - | - | -10.4 | 580 | 1184 | 582 | 379 / 290 / 288 |
| 170 | - | - | -7.3 | 969 | 1941 | 940 | 403 / 316 / 306 |
| 187 | - | - | -5.5 | 1593 | 3200 | 1595 | 416 / 351 / 330 |
| 204 | - | - | -4.0 | 2775 | 5578 | 2801 | 425 / 384 / 352 |
| 221 | - | - | -2.5 | 5595 | - | - | 431 / 412 / 380 |
| 238 | - | - | -1.3 | - | - | - | 434 / 425 / 405 |
| 255 | - | - | -0.7 | - | - | - | 436 / 431 / 419 |

**Long releases on 1-3** (30 s of tail):

| ENV | level at note-off (dBFS) | -20 dB (s) | -40 dB (s) | -60 dB (s) | decay (dB/s) |
|---|---|---|---|---|---|
| 221 | -43.1 | 5.64 | 11.34 | 16.99 | 3.50 |
| 238 | -42.1 | 8.84 | 17.70 | 26.45 | 2.26 |
| 255 | -41.1 | 8.74 | 17.58 | 26.35 | 2.27 |

The release is a clean exponential down to -140 dBFS and stops lengthening at
238.

**Velocity** (A3, levels against velocity 127):

| velocity | 1-3 level (dB) | 2-7 level (dB) | 4-4 level (dB) | 6-8 level (dB) |
|---|---|---|---|---|
| 8 | -48.3 | -48.5 | -48.2 | -48.0 |
| 16 | -36.0 | -36.6 | -36.0 | -36.0 |
| 24 | -29.3 | -30.9 | -29.1 | -28.9 |
| 32 | -24.1 | -24.5 | -24.6 | -24.0 |
| 40 | -20.2 | -20.6 | -21.5 | -20.1 |
| 48 | -17.1 | -17.1 | -17.2 | -16.9 |
| 56 | -14.2 | -14.3 | -14.3 | -14.2 |
| 64 | -12.1 | -12.0 | -11.9 | -11.9 |
| 72 | -9.9 | -10.5 | -10.1 | -9.9 |
| 80 | -8.3 | -8.5 | -8.1 | -8.0 |
| 88 | -6.5 | -8.3 | -6.4 | -6.4 |
| 96 | -5.2 | -5.6 | -5.2 | -4.9 |
| 104 | -3.6 | -4.1 | -5.0 | -3.5 |
| 112 | -2.5 | -2.5 | -2.7 | -2.2 |
| 120 | -1.1 | -1.0 | -1.1 | -1.0 |
| 127 | 0.0 | 0.0 | 0.0 | 0.0 |

| sound | exponent n (level ~ velocity^n) | largest residual (dB) | brightness trend 0-127 (oct) | brightness scatter (oct) |
|---|---|---|---|---|
| 1-3 | 2.00 | 0.19 | 0.00 | 0.00 |
| 2-7 | 2.02 | 1.42 | 0.14 | 0.19 |
| 4-4 | 1.99 | 1.13 | -0.03 | 0.15 |
| 6-8 | 2.00 | 0.04 | 0.00 | 0.00 |

The brightness scatter on 2-7 and 4-4 is their chorus and LFO caught at
different phases, not a trend.

**Polyphony** (2-7: six held notes entering 0.5 s apart; level of each note's
fundamental against the loudest, "." before the note starts):

| window (s) | C3 | E3 | G3 | B3 | D4 | F4 |
|---|---|---|---|---|---|---|
| 0.05-0.45 | 0 | . | . | . | . | . |
| 0.55-0.95 | -6 | 0 | . | . | . | . |
| 1.05-1.45 | -11 | -6 | 0 | . | . | . |
| 1.55-1.95 | -6 | -2 | 0 | -2 | . | . |
| 2.05-2.45 | -6 | -55 | 0 | -2 | -6 | . |
| 2.55-2.95 | -2 | -57 | -62 | -9 | -6 | 0 |
| 3.05-3.45 | -6 | -62 | -66 | -4 | -11 | 0 |
| 3.55-3.95 | -5 | -60 | -62 | -6 | -5 | 0 |

E3 falls silent when D4 enters, and G3 when F4 enters, while C3, the oldest
but lowest, keeps sounding; 4-7 and 7-2 behave alike.

**Tempo** (every LFO found at both 100 and 150 BPM; "track" is the trace it
was found on):

| sound | track | 100 BPM (Hz) | note | 150 BPM (Hz) | note | ratio | delay at 100 / 150 BPM (s) |
|---|---|---|---|---|---|---|---|
| 2-6 | brightness | 2.53 | 1/4T | 3.87 | 1/4T | 1.530 | 0.00 / 0.00 |
| 2-7 | pitch | 3.17 | 1/8 | 5.00 | 1/8 | 1.577 | 0.67 / 0.65 |
| 2-8 | pitch | 4.44 | 1/16. | 6.67 | 1/16. | 1.502 | 0.43 / 0.40 |
| 3-8 | pitch | 4.44 | 1/16. | 6.67 | 1/16. | 1.502 | 0.71 / 0.71 |
| 4-4 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.00 / 0.00 |
| 5-2 | pitch | 4.44 | 1/16. | 6.66 | 1/16. | 1.500 | 0.00 / 0.00 |
| 5-4 | even share | 3.17 | 1/8 | 5.02 | 1/8 | 1.584 | 0.52 / 0.00 |
| 5-6 | pitch | 4.44 | 1/16. | 6.67 | 1/16. | 1.502 | 0.00 / 0.00 |
| 5-6 | even share | 4.44 | 1/16. | 6.67 | 1/16. | 1.502 | 0.00 / 0.36 |
| 5-7 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.00 / 0.00 |
| 6-2 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.89 / 0.90 |
| 6-4 | pitch | 4.44 | 1/16. | 6.67 | 1/16. | 1.502 | 0.00 / 0.64 |
| 6-5 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.67 / 0.77 |
| 6-7 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.58 / 0.54 |
| 6-8 | pitch | 3.33 | 1/8 | 5.00 | 1/8 | 1.502 | 0.00 / 0.00 |
| 7-1 | pitch | 2.22 | 1/8. | 3.17 | 1/8. | 1.428 | 0.00 / 0.00 |
| 7-3 | even share | 4.43 | 1/16. | 6.67 | 1/16. | 1.506 | 0.00 / 0.00 |
| 7-4 | pitch | 2.22 | 1/8. | 3.17 | 1/8. | 1.428 | 0.00 / 0.00 |
| 7-5 | pitch | 8.88 | 1/32. | 13.33 | 1/32. | 1.501 | 0.00 / 0.00 |
| 7-6 | pitch | 2.49 | 1/4T | 3.87 | 1/4T | 1.554 | 0.84 / 0.68 |
| 7-7 | brightness | 3.17 | 1/8 | 5.00 | 1/8 | 1.577 | 0.00 / 0.00 |
| 8-4 | pitch | 0.53 | 1/2. | 1.23 | 1/2 | 2.321 | 0.00 / 0.00 |
| 8-4 | brightness | 0.30 | 1/1 | 0.30 | ? | 1.000 | 0.00 / 0.00 |
| 8-6 | pitch | 5.00 | 1/8T | 7.50 | 1/8T | 1.500 | 0.00 / 1.00 |

22 of 24 keep their note value; the two others are on 8-4, whose 0.625 Hz LFO
a 6 s note resolves poorly. The 7-1 and 7-4 ratios of 1.428 are 2.222 Hz read
as 3.17 Hz at 150 BPM, at the edge of a chorus band: the true rate there is
3.333 Hz, a ratio of 1.500.

**FILTER per sound** (RESONANCE 255, resonant peak brought to A2 with each
sound's tracking):

| FILTER | 6-8 | 2-7 | 4-6 | 4-4 |
|---|---|---|---|---|
| 17 |  |  | 730 | 1214 |
| 34 |  |  | 1070 | 1763 |
| 51 |  |  | 1769 | 3022 |
| 68 |  | 529 | 3411 | 5815 |
| 85 |  | 1533 | 7167 |  |
| 102 |  | 2825 |  |  |
| 119 |  | 5799 |  |  |
| 153 | 794 |  |  |  |
| 170 | 1758 |  |  |  |
| 187 | 3527 |  |  |  |
| 204 | 6295 |  |  |  |
| 221 | 9729 |  |  |  |
| 238 | 12380 |  |  |  |

| sound | keyboard tracking (octave per octave) | spread | FILTER values used | FILTER for 1 kHz at A2 |
|---|---|---|---|---|
| 6-8 | 1.00 | 0.01 | 4 | 158 |
| 2-7 | 0.50 | 0.05 | 3 | 78 |
| 4-6 | 0.31 | 0.02 | 5 | 31 |
| 4-4 | -0.03 | 0.02 | 4 | below 17 |

6-8 agrees with the direct reading of its self-oscillation within 3 %. 4-4
and 4-6 rise one octave per about 31 steps near 17, steepening to 16-18 near
68-85, with the same ratios step by step, as if they shared one curve at
different offsets. From about 102 on 4-4, 119 on 4-6 and 153 on 2-7, the
response up to 12 kHz stays within a few dB of FILTER 255.

**LFO phase** (concentrations of the phases at the note-ons; "brightness
steps" is the step measure of 4.5.11; when two measures of one LFO disagree,
both are shown):

| sound | pass | BPM | measured on | rate (Hz) | note | against the note-on | against the clock | verdict |
|---|---|---|---|---|---|---|---|---|
| 1-7 | keysync | 100 | even share | 2.500 | 1/4T | 0.33 | 0.92 | free-running |
| 2-6 | keysync | 100 | brightness | 2.500 | 1/4T | 0.26 | 1.00 | free-running |
| 2-7 | keysync | 100 | pitch | 3.333 | 1/8 | 0.35 | 0.99 | free-running |
| 2-8 | keysync | 100 | pitch | 4.444 | 1/16. | 0.35 | 1.00 | free-running |
| 3-6 | keysync | 100 | - | - | - | - | - | no LFO found |
| 3-6 | keysync2 | 100 | brightness | 1.667 | 1/4 | 0.16 | 0.92 | free-running |
| 3-8 | keysync | 100 | pitch | 4.444 | 1/16. | 0.35 | 1.00 | free-running |
| 4-1 | keysync | 100 | brightness | 1.250 | 1/2T | 0.08 | 1.00 | free-running |
| 4-3 | keysync | 100 | brightness | 0.556 | 1/2. | 0.15 | 0.99 | free-running |
| 4-4 | keysync | 100 | pitch | 5.000 | 1/8T | 0.25 | 1.00 | free-running |
| 5-1 | keysync | 100 | pitch | 2.500 | 1/4T | 0.23 | 1.00 | free-running |
| 5-2 | keysync | 100 | pitch | 4.444 | 1/16. | 0.36 | 1.00 | free-running |
| 5-3 | keysync | 100 | even share | 4.297 | 1/16. | 0.22 | 0.08 | unclear |
| 5-3 | keysync2 | 100 | brightness | 0.833 | 1/2 | 0.21 | 0.96 | free-running |
| 5-3 | keysync2 | 60 | even share | 0.500 | 1/2 | 0.40 | 0.99 | free-running |
| 5-4 | keysync | 100 | even share | 3.333 | 1/8 | 0.41 | 0.97 | free-running |
| 5-5 | keysync | 100 | - | - | - | - | - | no LFO found |
| 5-5 | keysync2 | 100 | - | - | - | - | - | no LFO found |
| 5-6 | keysync | 100 | brightness | 4.443 | 1/16. | 1.00 | 0.36 | restarts with each note |
| 5-6 | keysync3 | 100 | brightness | 4.442 | 1/16. | 1.00 | 0.29 | restarts with each note |
| 5-7 | keysync | 100 | even share | 5.000 | 1/8T | 0.25 | 1.00 | free-running |
| 5-8 | keysync | 100 | - | - | - | - | - | no LFO found |
| 5-8 | keysync2 | 100 | brightness steps | 0.556 | 1/2. | 0.37 | 0.91 | free-running |
| 5-8 | keysync2 | 100 | brightness | 0.556 | 1/2. | 0.93 | 0.32 | restarts with each note |
| 5-8 | keysync3 | 100 | brightness steps | 0.556 | 1/2. | 0.39 | 0.98 | free-running |
| 5-8 | keysync3 | 60 | brightness steps | 0.333 | 1/2. | 0.39 | 1.00 | free-running |
| 6-2 | keysync | 100 | pitch | 5.000 | 1/8T | 0.24 | 1.00 | free-running |
| 6-3 | keysync | 100 | brightness | 6.808 | 1/16 | 0.40 | 0.22 | unclear |
| 6-3 | keysync2 | 100 | audio-rate component | 53.333 | 1/128 | 1.00 | 0.62 | restarts with each note |
| 6-3 | keysync2 | 60 | audio-rate component | 32.000 | 1/128 | 1.00 | 0.41 | restarts with each note |
| 6-4 | keysync | 100 | pitch | 4.444 | 1/16. | 0.36 | 1.00 | free-running |
| 6-5 | keysync | 100 | brightness | 5.000 | 1/8T | 0.25 | 1.00 | free-running |
| 6-7 | keysync | 100 | pitch | 5.000 | 1/8T | 0.25 | 1.00 | free-running |
| 6-8 | keysync | 100 | pitch | 3.333 | 1/8 | 0.35 | 1.00 | free-running |
| 7-1 | keysync | 100 | brightness | 2.222 | 1/8. | 0.35 | 1.00 | free-running |
| 7-2 | keysync | 100 | - | - | - | - | - | no LFO found |
| 7-2 | keysync2 | 100 | pitch | 2.500 | 1/4T | 0.19 | 1.00 | free-running |
| 7-3 | keysync | 100 | brightness | 4.444 | 1/16. | 0.35 | 1.00 | free-running |
| 7-4 | keysync | 100 | brightness | 2.222 | 1/8. | 0.34 | 1.00 | free-running |
| 7-5 | keysync | 100 | pitch | 8.889 | 1/32. | 0.25 | 0.99 | free-running |
| 7-6 | keysync | 100 | brightness | 2.500 | 1/4T | 0.29 | 1.00 | free-running |
| 7-7 | keysync | 100 | brightness | 3.333 | 1/8 | 0.35 | 0.99 | free-running |
| 7-8 | keysync | 100 | brightness | 0.625 | 1/1T | 0.07 | 1.00 | free-running |
| 8-1 | keysync | 100 | brightness | 0.556 | 1/2. | 0.13 | 1.00 | free-running |
| 8-1 | keysync3 | 100 | brightness | 0.556 | 1/2. | 0.37 | 1.00 | free-running |
| 8-2 | keysync | 100 | brightness | 1.410 | 1/2T | 0.65 | 0.21 | unclear |
| 8-2 | keysync2 | 100 | brightness steps | 1.250 | 1/2T | 0.36 | 0.93 | free-running |
| 8-2 | keysync2 | 60 | brightness steps | 0.750 | 1/2T | 0.36 | 0.90 | free-running |
| 8-3 | keysync | 100 | - | - | - | - | - | no LFO found |
| 8-3 | keysync2 | 100 | brightness | 0.833 | 1/2 | 0.13 | 0.98 | free-running |
| 8-4 | keysync | 100 | pitch | 0.625 | 1/1T | 0.05 | 0.99 | free-running |
| 8-6 | keysync | 100 | pitch | 5.000 | 1/8T | 0.25 | 1.00 | free-running |
| 8-7 | keysync | 150 | brightness steps | 6.659 | 1/16. | 1.00 | 0.39 | restarts with each note |
| 8-8 | keysync | 100 | brightness | 13.333 | 1/32 | 1.00 | 0.24 | restarts with each note |
| 8-8 | keysync2 | 60 | pitch | 8.000 | 1/32 | 1.00 | 0.20 | restarts with each note |
| 8-8 | keysync2 | 70 | pitch | 9.333 | 1/32 | 1.00 | 0.42 | restarts with each note |

The free-running rates sit within 0.1 % of a note value. 8-8 restarts at 60,
70 and 100 BPM, and its 13.33 Hz is the same on A2 and A4, so it is an LFO
and not a beat between detuned oscillators.

**Closing pass**: each modulation of a long note looked for at the other
tempo:

| sound | measured on | found | looked for at | verdict |
|---|---|---|---|---|
| 8-8 | pitch | 7.998 Hz at 60 BPM | 70 BPM | follows the tempo |
| 8-8 | pitch | 15.996 Hz at 60 BPM | 70 BPM | follows the tempo |
| 8-8 | brightness | 7.998 Hz at 60 BPM | 70 BPM | follows the tempo |
| 8-8 | brightness | 15.996 Hz at 60 BPM | 70 BPM | follows the tempo |
| 8-8 | even share | 7.998 Hz at 60 BPM | 70 BPM | follows the tempo |
| 8-8 | pitch | 9.331 Hz at 70 BPM | 60 BPM | follows the tempo |
| 8-8 | brightness | 9.331 Hz at 70 BPM | 60 BPM | follows the tempo |
| 8-8 | even share | 9.331 Hz at 70 BPM | 60 BPM | follows the tempo |
| 5-3 | even share | 0.826 Hz at 100 BPM | 60 BPM | follows the tempo |
| 5-3 | brightness | 0.500 Hz at 60 BPM | 100 BPM | follows the tempo |
| 5-3 | even share | 0.500 Hz at 60 BPM | 100 BPM | follows the tempo |
| 6-3 | brightness | 6.813 Hz at 100 BPM | 60 BPM | unclear |
| 6-3 | audio-rate component | 53.317 Hz at 100 BPM | 60 BPM | follows the tempo |
| 6-3 | even share | 3.855 Hz at 60 BPM | 100 BPM | unclear |
| 6-3 | audio-rate component | 31.991 Hz at 60 BPM | 100 BPM | follows the tempo |
| 8-2 | brightness steps | 1.251 Hz at 100 BPM | 60 BPM | follows the tempo |
| 8-2 | brightness steps | 0.751 Hz at 60 BPM | 100 BPM | follows the tempo |
| 3-6 | brightness | 1.670 Hz at 100 BPM | 60 BPM | follows the tempo |
| 5-8 | brightness steps | 0.562 Hz at 100 BPM | 60 BPM | follows the tempo |
| 7-2 | pitch | 2.500 Hz at 100 BPM | 60 BPM | follows the tempo |
| 7-2 | even share | 4.999 Hz at 100 BPM | 60 BPM | follows the tempo |
| 8-3 | brightness | 0.833 Hz at 100 BPM | 60 BPM | follows the tempo |
| 3-6 | brightness | 2.377 Hz at 60 BPM | 100 BPM | follows the tempo |
| 3-6 | brightness | 2.035 Hz at 60 BPM | 100 BPM | unclear |
| 5-8 | brightness | 0.333 Hz at 60 BPM | 100 BPM | follows the tempo |
| 7-2 | brightness | 3.249 Hz at 60 BPM | 100 BPM | unclear |
| 7-2 | even share | 2.997 Hz at 60 BPM | 100 BPM | follows the tempo |
| 8-3 | brightness steps | 5.481 Hz at 60 BPM | 100 BPM | unclear |

An "unclear" row is a modulation whose peaks at the other tempo decided
nothing (neither candidate 8 times the median and twice the other): 6-3's
beat, and secondary readings on 3-6, 7-2 and 8-3 beside their main LFOs.

**Chord test** (four notes held together; each voice read on its own
fundamental and second harmonic, which no other note shares):

| sound | measured on | rate (Hz) | phase agreement against the clock | against each note-on | verdict |
|---|---|---|---|---|---|
| 5-3 | level | 0.818 | 1.00 | 0.30 | inconclusive: chorus harmonic 2 x 0.454 Hz within the resolution |
| 6-3 | level | 1.807 | 0.06 | 0.48 | inconclusive: chorus harmonic 2 x 0.877 Hz within the resolution |
| 8-2 | level | 1.813 | 0.03 | 0.49 | inconclusive: chorus harmonic 2 x 0.879 Hz within the resolution |
| 6-5 | pitch | 5.000 | 1.00 | 0.42 | voices share one LFO phase |
| 5-6 | pitch | 4.444 | 1.00 | 0.36 | voices share one LFO phase; the phase is the one note 1 (onset 0.0 s) gives on its own, within 4 deg (others 44, 100, 116 deg) |

**Final pass, 8-2** (90 s notes at FILTER 251, 20 s notes at 140 and 100):

| take | measured on | rate (Hz) | note | swing | height (x median) |
|---|---|---|---|---|---|
| 100 BPM, FILTER 251 | brightness steps | 1.251 | 1/2T | - | 36 |
| 60 BPM, FILTER 251 | brightness steps | 0.751 | 1/2T | - | 34 |
| 100 BPM, FILTER 140 | pitch | 1.250 | 1/2T | 27.565 | 69 |
| 100 BPM, FILTER 140 | pitch | 3.749 | 1/8 | 14.614 | 34 |
| 100 BPM, FILTER 140 | pitch | 4.999 | 1/8T | 13.871 | 34 |
| 100 BPM, FILTER 140 | brightness | 1.250 | 1/2T | 0.675 | 144 |
| 100 BPM, FILTER 140 | even share | 1.250 | 1/2T | 0.432 | 98 |
| 100 BPM, FILTER 100 | pitch | 11.798 | 1/32 | 9.919 | 11 |
| 100 BPM, FILTER 100 | brightness | 1.250 | 1/2T | 1.768 | 277 |

**Final pass, jitter** (5-5 and 8-2 at several FILTER settings):

| sound | BPM | FILTER / RES | brightness jitter 5-45 Hz, both channels (oct) | between channels (oct) | harmonic fluctuation 1-45 Hz (oct rms) |
|---|---|---|---|---|---|
| 8-2 | 100 | 140 / 144 | 0.060 | 0.046 | 1.33 |
| 8-2 | 100 | 100 / 144 | 0.069 | 0.076 | 1.34 |
| 5-5 | 100 | 255 / 0 | 0.020 | 0.020 | 0.52 |
| 5-5 | 100 | 120 / 0 | 0.029 | 0.022 | 0.52 |
| 5-5 | 100 | 51 / 138 | 0.053 | 0.018 | 0.56 |
| 8-2 | 100 | 251 / 144 | 0.023 | 0.020 | 0.51 |
| 8-2 | 60 | 251 / 144 | 0.023 | 0.020 | 0.51 |

On 5-5 the harmonics fluctuate by 0.52 octave rms with the filter open, 0.52
at FILTER 120 and 0.56 at its defaults: the filter adds under a tenth of the
source's own fluctuation. On 8-2, revealing the filter LFO raises the same
measure from 0.51 (FILTER 251) to 1.33 (FILTER 140).

**Finalfinal pass** (5-8 on 8 s notes, measured from 1 s and fitted from 2 s
after each note-on; 8-1 and 5-6 as controls):

| sound | BPM | measured on | rate (Hz) | against the note-on | against the clock | verdict |
|---|---|---|---|---|---|---|
| 5-8 | 100 | brightness steps | 0.556 | 0.39 | 0.98 | free-running |
| 5-8 | 100 | brightness | 0.556 | 0.33 | 0.99 | free-running |
| 5-8 | 60 | brightness steps | 0.333 | 0.39 | 1.00 | free-running |
| 5-8 | 60 | brightness | 0.333 | 0.40 | 0.99 | free-running |
| 8-1 | 100 | brightness | 0.556 | 0.37 | 1.00 | free-running |
| 8-1 | 100 | pitch | 0.556 | 0.37 | 1.00 | free-running |
| 5-6 | 100 | brightness | 4.442 | 1.00 | 0.29 | restarts with each note |
| 5-6 | 100 | pitch | 4.443 | 1.00 | 0.26 | restarts with each note |
| 5-6 | 100 | even share | 4.440 | 1.00 | 0.29 | restarts with each note |

Replaying the old measurement on these notes reproduces the earlier false
restart: the first 3.5 s fitted from 1 s give 0.91 against the note-on,
while a 3.5 s window starting 2 s in gives 0.95 against the clock.

**Destinations** (swing at the LFO rate; "a / b" is the filter at the
sound's setting / fully open; plucks on the ENV 255 pass):

| sound | rate (Hz) | pitch (cents) | brightness (oct) | even share |
|---|---|---|---|---|
| 1-4 (ENV 255) | 0.556 | 0.9 | 0.23 | 0.07 |
| 1-6 (ENV 255) | 2.500 | 13.6 | 0.28 | 0.18 |
| 1-7 | 2.500 | 2.8 / 0.5 | 0.14 / 0.01 | 0.28 / 0.28 |
| 2-4 (ENV 255) | 2.222 | 10.8 | 0.30 | 0.17 |
| 2-6 | 2.500 | 1.7 / 0.8 | 0.42 / 0.04 | 0.32 / 0.30 |
| 2-7 | 3.333 | 9.9 / 1.9 | 0.13 / 0.08 | 0.08 / 0.03 |
| 2-8 | 4.444 | 24.5 / 0.9 | 0.29 / 0.08 | 0.03 / 0.02 |
| 3-6 | 1.667 | 0.5 / 0.3 | 0.25 / 0.16 | 0.10 / 0.13 |
| 3-8 | 4.444 | 6.8 / 6.5 | 0.01 / 0.01 | 0.00 / 0.00 |
| 4-1 | 1.250 | 8.1 / 7.9 | 0.38 / 0.38 | 0.07 / 0.07 |
| 4-3 | 0.556 | 10.9 / 10.7 | 0.71 / 0.68 | 0.22 / 0.25 |
| 4-4 | 5.000 | 145.6 / 145.5 | 0.14 / 0.13 | 0.10 / 0.09 |
| 5-1 | 2.500 | 7.3 / 7.5 | 0.06 / 0.10 | 0.09 / 0.09 |
| 5-2 | 4.444 | 9.8 / 9.9 | 0.00 / 0.01 | 0.00 / 0.00 |
| 5-3 | 0.833 | 4.6 / 2.8 | 0.23 / 0.55 | 0.32 / 0.11 |
| 5-4 | 3.333 | 5.9 / 5.7 | 0.18 / 0.16 | 0.41 / 0.41 |
| 5-6 | 4.442 | 78.8 / 80.5 | 0.47 / 0.57 | 0.50 / 0.48 |
| 5-7 | 5.000 | 32.0 / 3.5 | 0.10 / 0.01 | 0.06 / 0.00 |
| 5-8 | 0.556 | 6.7 / 3.2 | 0.21 / 0.30 | 0.04 / 0.04 |
| 6-2 | 5.000 | 38.5 / 38.0 | 0.01 / 0.01 | 0.00 / 0.00 |
| 6-4 | 4.444 | 8.0 / 0.0 | 0.04 / 0.00 | 0.01 / 0.00 |
| 6-5 | 5.000 | 13.3 / 0.0 | 0.23 / 0.02 | 0.04 / 0.00 |
| 6-7 | 5.000 | 13.3 / 13.4 | 0.00 / 0.00 | 0.00 / 0.00 |
| 6-8 | 3.333 | 42.8 / 75.3 | 0.03 / 0.07 | 0.00 / 0.16 |
| 7-1 | 2.222 | 11.3 / 11.4 | 0.45 / 0.44 | 0.22 / 0.21 |
| 7-2 | 2.500 | 6.4 / 6.6 | 0.07 / 0.10 | 0.22 / 0.21 |
| 7-3 | 4.444 | 15.6 / 15.8 | 0.48 / 0.44 | 0.29 / 0.32 |
| 7-4 | 2.222 | 6.8 / 7.1 | 0.38 / 0.35 | 0.17 / 0.16 |
| 7-5 | 8.889 | 21.7 / 21.6 | 0.02 / 0.03 | 0.03 / 0.02 |
| 7-6 | 2.500 | 10.2 / 10.4 | 0.30 / 0.05 | 0.04 / 0.04 |
| 7-7 | 3.333 | 4.0 / 2.4 | 0.35 / 0.09 | 0.10 / 0.04 |
| 7-8 | 0.625 | 4.3 / 0.7 | 0.66 / 0.20 | 0.04 / 0.04 |
| 8-1 | 0.556 | 10.8 / 10.8 | 0.93 / 0.51 | 0.00 / 0.00 |
| 8-2 | 1.250 | 1.5 / 2.8 | 0.28 / 0.42 | 0.08 / 0.08 |
| 8-3 | 0.833 | 14.3 / 14.6 | 0.90 / 0.61 | 0.22 / 0.14 |
| 8-4 | 0.625 | 12.0 / 10.1 | 0.46 / 0.03 | 0.06 / 0.00 |
| 8-6 | 5.000 | 21.5 / 21.2 | 0.10 / 0.06 | 0.03 / 0.02 |
| 8-8 | 13.333 | 23.1 / 2.1 | 0.30 / 0.04 | 0.18 / 0.00 |

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

| experiment | sound | built as | measured on | rate (Hz) | against the note-on | against the clock | verdict |
|---|---|---|---|---|---|---|---|
| keysync | 1-1 | restarts (5 Hz vibrato) | pitch | 4.999 | 1.00 | 0.24 | restarts with each note |
| keysync | 1-2 | free-running (4.444 Hz vibrato) | pitch | 4.444 | 0.35 | 1.00 | free-running |
| keysync | 1-3 | free-running (4.444 Hz sample and hold) | brightness steps | 4.444 | 0.34 | 1.00 | free-running |
| keysync | 1-4 | no LFO | - | - | - | - | no LFO found |
| keysync2 | 1-3 | free-running (2 Hz vibrato at 60 BPM) | pitch | 2.000 | 0.11 | 1.00 | free-running |
| keysync3 | 5-8 | free-running (0.556 Hz, envelope spike) | brightness | 0.556 | 0.37 | 1.00 | free-running |
| keysync3 | 5-6 | restarts (0.556 Hz, envelope spike) | brightness | 0.555 | 1.00 | 0.37 | restarts with each note |
| chord | 1-4 | one LFO shared by the voices (5 Hz) | level | 5.000 | 0.42 | 1.00 | voices share one LFO phase |
| chord | 1-5 | one LFO per voice, restarting (4.444 Hz) | level | 4.444 | 1.00 | 0.35 | each voice's LFO starts at its note-on |

| experiment | sound | built as | BPM | measured on | rate (Hz) | at the other tempo |
|---|---|---|---|---|---|---|
| longnote | 1-1 | vibrato on a 1/16., follows the tempo | 100 | pitch | 4.444 | follows the tempo |
| longnote | 1-1 | vibrato on a 1/16., follows the tempo | 60 | pitch | 2.667 | follows the tempo |
| longnote | 1-2 | filter LFO fixed at 6.81 Hz | 100 | brightness | 6.810 | fixed rate |
| longnote | 1-2 | filter LFO fixed at 6.81 Hz | 60 | brightness | 6.810 | fixed rate |
| verylong | 1-6 | filter LFO on 4/1, follows the tempo | 100 | brightness | 0.104 | follows the tempo |
| verylong | 1-6 | filter LFO on 4/1, follows the tempo | 60 | brightness | 0.062 | follows the tempo |

Filters, 3-5 (built with keyboard tracking 0.50, 1 kHz at A2 for FILTER 120 and 14.4 steps per octave): measured tracking 0.50, 1 kHz at A2 for FILTER 120, 14.4 steps per octave.

| longtail (1-3) | built as | -20 dB (s) | -40 dB (s) | -60 dB (s) | decay (dB/s) |
|---|---|---|---|---|---|
| ENV 238 | 4 dB/s | 5.01 | 9.98 | 14.99 | 4.00 |
| ENV 255 | 2 dB/s | 9.98 | 19.96 | 29.48 | 2.00 |

| longnote2 | built as | FILTER | brightness jitter 0.5-5 Hz, together / apart (oct) | harmonic fluctuation (oct rms) |
|---|---|---|---|---|
| 1-7 | noisy source, random filter movement | 120 | 0.150 / 0.005 | 0.771 |
| 1-7 | noisy source, random filter movement | 255 | 0.020 / 0.006 | 0.049 |
| 1-8 | noisy source, static filter | 120 | 0.006 / 0.005 | 0.066 |
| 1-8 | noisy source, static filter | 255 | 0.020 / 0.006 | 0.049 |

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
- A vibrato under 6 cents escapes the main analysis (4-5 shows 2-cent ripples
  that coincide with chorus harmonics); so does a filter movement under a
  tenth of a noisy source's jitter (5-5).
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
- F. J. Harris, "On the use of windows for harmonic analysis with the
  discrete Fourier transform", *Proceedings of the IEEE* 66 (1), 1978,
  pp. 51-83, [doi:10.1109/PROC.1978.10837](https://doi.org/10.1109/PROC.1978.10837).
- Wikipedia, [Directional statistics](https://en.wikipedia.org/wiki/Directional_statistics)
  (mean resultant length).
- Wikipedia, [Standing on the shoulders of giants](https://en.wikipedia.org/wiki/Standing_on_the_shoulders_of_giants).
