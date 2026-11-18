#!/usr/bin/env bash
# Record the J-6 passes that need their own pattern set: generate every set,
# then for each pass copy its patterns into the J-6's RESTORE folder and record
# it. The script pauses only for what needs hands on the J-6: starting backup
# mode, pressing [CHORD], switching off and on.
#
#   bash j6passes.sh                  # open, env000 and env255
#   bash j6passes.sh env000 env255    # chosen passes only
#
# Run it from the folder holding Factory_backup/ and Harvest_backup/, or set
# TEMPLATE and DEFAULTS. J6_MOUNT is where the desktop mounts the J-6 drive.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TEMPLATE=${TEMPLATE:-Factory_backup/BACKUP/J6_PTN17.PRM}
DEFAULTS=${DEFAULTS:-Harvest_backup/defaults.csv}
MNT=${J6_MOUNT:-/media/${USER:-$(id -un)}/J-6}
CARDS=${J6_CARDS:-/proc/asound/cards}
PATTERNS=${J6_PATTERNS:-1..64}  # e.g. J6_PATTERNS=1..3 for a pilot

declare -A GEN=([open]="--filter 255 --resonance 0" [env000]="--env 0" [env255]="--env 255")
declare -A STIM=([open]=full [env000]=short [env255]=short)
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
  echo "Chord mode can be on after a restore: make sure [CHORD] is unlit, otherwise every"
  echo "test note plays a chord."
  read -r -p "[CHORD] unlit? press Enter to record "
  until grep -q '\[J6 ' "$CARDS"; do sleep 1; done
  sleep 3  # let the MIDI and audio devices settle
  python3 "$HERE/j6capture.py" --pass-name "$p" --prm-dir "passes/$p/RESTORE" \
    --outdir "captures/$p" --stimulus "${STIM[$p]}" --patterns "$PATTERNS" --flac
done
echo
echo "passes recorded: ${PASSES[*]}. Restore your production backup when you are done."
