#!/usr/bin/env bash
# Record the J-6 passes that need their own pattern set: generate every set,
# then for each pass copy its patterns into the J-6's RESTORE folder and record
# it. The script pauses only for what needs hands on the J-6: starting backup
# mode, pressing [CHORD], switching off and on.
#
#   bash j6passes.sh                  # open, env000 and env255
#   bash j6passes.sh default env255   # chosen passes: default, open, env000, env255,
#                                     # tempo150 (defaults at 150 BPM, plus velocity
#                                     # and polyphony tests), sweep (knob sweeps),
#                                     # keysync (do LFOs restart with each note),
#                                     # filters (cutoff per sound, long releases),
#                                     # closing (the questions those left open),
#                                     # final (8-2's and 5-5's filter modulation)
#
# Run it from the experiment folder, which holds the scripts,
# Factory_backup/ and Harvest_backup/; it creates passes/ and captures/ there.
# J6_MOUNT is where the desktop mounts the J-6 drive.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TEMPLATE=${TEMPLATE:-Factory_backup/BACKUP/J6_PTN17.PRM}
DEFAULTS=${DEFAULTS:-Harvest_backup/defaults.csv}
MNT=${J6_MOUNT:-/media/${USER:-$(id -un)}/J-6}
CARDS=${J6_CARDS:-/proc/asound/cards}
PATTERNS=${J6_PATTERNS:-1..64}  # e.g. J6_PATTERNS=1..3 for a pilot

declare -A GEN=([default]="" [open]="--filter 255 --resonance 0" [env000]="--env 0" [env255]="--env 255"
                [tempo150]="--bpm 150" [sweep]="--plan sweep" [keysync]="--plan keysync" [filters]="--plan filters"
                [closing]="--plan closing" [final]="--plan final")
# the sounds with an LFO (or 8-7's sample and hold) that sustain at their defaults
LFO_SOUNDS=1-7,2-6,2-7,2-8,3-6,3-8,4-1,4-3,4-4,5-1,5-2,5-3,5-4,5-5,5-6,5-7,5-8,6-2,6-3,6-4,6-5,6-7,6-8,7-1,7-2,7-3,7-4,7-5,7-6,7-7,7-8,8-1,8-2,8-3,8-4,8-6,8-7,8-8
# Recordings after each restore: "name|patterns|stimulus|settle", into captures/name.
# Settle is the pause between patterns: with [ENVELOPE] high a note rings for
# seconds after its note-off, and the J-6 ignores All Sound Off.
declare -A RUNS=([default]="default|$PATTERNS|full|1" [open]="open|$PATTERNS|full|1"
                 [env000]="env000|$PATTERNS|short|1" [env255]="env255|$PATTERNS|short|10"
                 [tempo150]="tempo150|$PATTERNS|full|1 velocity|1-3,2-7,4-4,6-8|velocity|1 poly|2-7,4-7,7-2|poly|1"
                 [sweep]="sweep|1..48|full|1 sweep|49..64|envelope|10"
                 [keysync]="keysync|$LFO_SOUNDS|retrig|1"
                 [filters]="filters|1..60|filter|1 longtail|61..63|longtail|5"
                 [closing]="longnote|1..13,16..20|longnote|1 keysync2|1..13|retrig8|1 chord|3,5,7,14,15|chord|1"
                 [final]="verylong|1..2|verylong|1 longnote2|3..7|longnote|1")
if [ $# -gt 0 ]; then PASSES=("$@"); else PASSES=(open env000 env255); fi
for p in "${PASSES[@]}"; do
  [ -n "${GEN[$p]+set}" ] || { echo "unknown pass '$p' (known: ${!GEN[*]})"; exit 1; }
done

for p in "${PASSES[@]}"; do
  if [ -d "passes/$p" ]; then
    echo "passes/$p exists, reusing it"
  else
    # shellcheck disable=SC2086  # GEN holds several options on purpose
    python3 "$HERE/j6prm.py" generate --template "$TEMPLATE" --defaults "$DEFAULTS" \
      ${GEN[$p]} --out "passes/$p"
  fi
done

for p in "${PASSES[@]}"; do
  echo
  echo "== pass $p: switch the J-6 off, then on while holding [PLAY]; waiting for $MNT"
  until [ -d "$MNT/RESTORE" ]; do sleep 2; done
  cp "passes/$p/RESTORE/"*.PRM "$MNT/RESTORE/"
  sync
  if udisksctl unmount --block-device "$(findmnt -no SOURCE "$MNT")" >/dev/null; then
    echo "64 patterns copied, drive unmounted"
  else
    read -r -p "unmount failed: eject the J-6 drive from the file manager, then press Enter "
  fi
  echo "press [CHORD] to restore and wait until the LEDs stop blinking, then switch off and on normally."
  echo "[CHORD] is on after every power-on: press it so that it is unlit, otherwise every"
  echo "test note plays a chord."
  read -r -p "[CHORD] unlit? press Enter to record "
  until grep -q '\[J6 ' "$CARDS"; do sleep 1; done
  sleep 3  # let the MIDI and audio devices settle
  for run in ${RUNS[$p]}; do
    IFS='|' read -r name pats stim settle <<< "$run"
    echo "-- recording $name: patterns $pats, stimulus $stim"
    python3 "$HERE/j6capture.py" --pass-name "$name" --prm-dir "passes/$p/RESTORE" \
      --outdir "captures/$name" --stimulus "$stim" --settle "$settle" --patterns "$pats" --flac
  done
done
echo
echo "passes recorded: ${PASSES[*]}. Restore your production backup when you are done."
