#!/usr/bin/env python3
"""Record the Roland J-6's sounds over USB, one pattern per take.

For each pattern, the script selects it with a MIDI Program Change, plays a
fixed set of test notes into the J-6 and records the J-6's USB audio with
arecord. Each take is saved as WAV (or FLAC) with a JSON sidecar stating what
was played and when, so the analysis can align notes and audio.

MIDI goes through the ALSA sequencer by default (aplaymidi playing a generated
MIDI file), which works while the desktop's MIDI bridge holds the J-6's raw
port. --midi raw writes to the raw port instead, when it is free.

Linux, Python >= 3.8, alsa-utils (arecord, aplaymidi). Optional: flac.
No Python packages.

Pilot, then full pass (already recorded takes are skipped):
  python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE \\
      --outdir captures/default --patterns 1..3
  python3 j6capture.py --pass-name default --prm-dir passes/default/RESTORE \\
      --outdir captures/default --patterns 1..64
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.1"

# Test notes: (name, MIDI note, velocity or None for --velocity, note-on time s, gate s).
# Roland numbering, C4 = 60: A2 = 45 (110 Hz), E3 = 52, A3 = 57, A4 = 69 (440 Hz).
STIMULI = {
    "full": [
        ("long_A2", 45, None, 0.00, 6.00),        # envelope, LFO, PWM, chorus; 3 s release tail
        ("staccato_A2", 45, None, 9.00, 0.15),    # behaviour with a short gate
        ("key_A4", 69, None, 11.50, 1.50),        # keyboard tracking, two octaves up
        ("glide_from_A2", 45, None, 15.00, 0.80), # glide: E3 starts 50 ms after A2 ends
        ("glide_to_E3", 52, None, 15.85, 1.20),
        ("velocity_40", 57, 40, 19.05, 0.80),     # velocity sensitivity, A3
        ("velocity_127", 57, 127, 21.05, 0.80),
    ],
    "short": [
        ("long_A2", 45, None, 0.00, 6.00),
        ("staccato_A2", 45, None, 9.00, 0.15),
    ],
}
TAIL = {"full": 2.00, "short": 2.35}  # recorded after the last note-off
PRE_ROLL = 0.8   # s between starting arecord and the first note (noise floor)
MARGIN = 0.5

BUSY_HINT = (
    "If arecord says 'Device or resource busy', the desktop sound server holds the J-6.\n"
    "Find it with:  pactl list short cards\n"
    "Release it with:  pactl set-card-profile <name of the J-6 card> off\n"
    "(or pavucontrol, Configuration tab), run this script, then set the profile back."
)


def label(i: int) -> str:
    """0-based pattern index -> label as on the panel (1-1 ... 8-8)."""
    return f"{i // 8 + 1}-{i % 8 + 1}"


def parse_patterns(spec: str) -> list[int]:
    """'1..3,2-5,64' -> [1, 2, 3, 13, 64]: numbers 1-64, ranges a..b, panel labels b-n."""
    out: list[int] = []
    for token in spec.split(","):
        token = token.strip()
        if re.fullmatch(r"[1-8]-[1-8]", token):
            bank, number = map(int, token.split("-"))
            out.append((bank - 1) * 8 + number)
        elif re.fullmatch(r"\d+\.\.\d+", token):
            first, last = map(int, token.split(".."))
            out.extend(range(first, last + 1))
        elif re.fullmatch(r"\d+", token):
            out.append(int(token))
        else:
            raise argparse.ArgumentTypeError(f"cannot read pattern list item {token!r}")
    bad = [n for n in out if not 1 <= n <= 64]
    if bad:
        raise argparse.ArgumentTypeError(f"pattern numbers must be 1-64, got {bad}")
    return list(dict.fromkeys(out))


def note_on(ch: int, note: int, vel: int) -> bytes:
    return bytes((0x90 | (ch - 1), note, vel))


def note_off(ch: int, note: int) -> bytes:
    return bytes((0x80 | (ch - 1), note, 64))


def control(ch: int, number: int, value: int) -> bytes:
    return bytes((0xB0 | (ch - 1), number, value))


def program(ch: int, number: int) -> bytes:
    return bytes((0xC0 | (ch - 1), number))


def silence(ch: int) -> list[bytes]:
    return [control(ch, 123, 0), control(ch, 120, 0)]  # All Notes Off, All Sound Off


def build_schedule(stimulus, velocity: int, ch: int):
    events = []
    for name, note, vel, on, gate in stimulus:
        events.append((on, note_on(ch, note, vel or velocity), name, "on"))
        events.append((on + gate, note_off(ch, note), name, "off"))
    events.sort(key=lambda e: (e[0], e[3] == "on"))  # note-off first at equal times
    return events


def vlq(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append(0x80 | (n & 0x7F))
        n >>= 7
    return bytes(reversed(out))


def smf(events) -> bytes:
    """Standard MIDI file, format 0, one tick = 1 ms (1000 ticks per quarter note,
    1 000 000 us per quarter). events: (seconds, one MIDI message), in time order."""
    track = bytearray(b"\x00\xff\x51\x03\x0f\x42\x40")
    now = 0
    for t, msg in events:
        tick = round(t * 1000)
        track += vlq(tick - now) + msg
        now = tick
    track += b"\x00\xff\x2f\x00"
    return (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big") + (1).to_bytes(2, "big")
            + (1000).to_bytes(2, "big") + b"MTrk" + len(track).to_bytes(4, "big") + bytes(track))


class RawMidi:
    """Writes to the raw MIDI device; times every message itself."""
    backend = "raw"

    def __init__(self, path: str):
        self.where = path
        self.fd = os.open(path, os.O_WRONLY)

    def send(self, messages: list[bytes]) -> None:
        for m in messages:
            os.write(self.fd, m)

    def play(self, events):
        """Send the events on time (sleep, then spin for the last 3 ms)."""
        t0 = time.perf_counter()
        sent = {}
        for t, msg, name, kind in events:
            target = t0 + t
            while True:
                dt = target - time.perf_counter()
                if dt <= 0:
                    break
                time.sleep(dt - 0.003 if dt > 0.004 else 0)
            os.write(self.fd, msg)
            sent[(name, kind)] = round(time.perf_counter() - t0, 4)
        return t0, sent

    def close(self) -> None:
        os.close(self.fd)


class SeqMidi:
    """Plays generated MIDI files with aplaymidi; the sequencer queue does the timing."""
    backend = "seq"

    def __init__(self, port: str, workdir: Path):
        self.where = port
        self.file = workdir / ".j6capture.mid"

    def _play_file(self, data: bytes, timeout: float) -> None:
        self.file.write_bytes(data)
        p = subprocess.run(["aplaymidi", "-p", self.where, str(self.file)],
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            raise RuntimeError(f"aplaymidi failed: {p.stderr.strip()}")

    def send(self, messages: list[bytes]) -> None:
        self._play_file(smf([(0.0, m) for m in messages]), 15)

    def play(self, events):
        data = smf([(t, msg) for t, msg, _, _ in events])
        t0 = time.perf_counter()
        self._play_file(data, events[-1][0] + 30)
        return t0, None

    def close(self) -> None:
        if self.file.exists():
            self.file.unlink()


def find_seq_port(client: str):
    p = subprocess.run(["aplaymidi", "-l"], capture_output=True, text=True, timeout=10)
    for line in p.stdout.splitlines():
        m = re.match(r"\s*(\d+:\d+)\s+(.+?)\s{2,}(.+?)\s*$", line)
        if m and m.group(2) == client:
            return m.group(1), p.stdout
    return None, p.stdout


def find_card(card_id: str):
    try:
        text = Path("/proc/asound/cards").read_text()
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+\[(\S+)\s*\]", line)
        if m and m.group(2) == card_id:
            return int(m.group(1))
    return None


def read_prm(path: Path) -> dict:
    values = {}
    for line in path.read_text(encoding="ascii").splitlines():
        key, sep, value = line.partition("\t= ")
        if sep and not key.startswith("BAR "):
            values[key] = value
    return values


def wav_peak_dbfs(path: Path):
    """Peak level from the most significant byte of each sample: coarse, but
    enough to flag a silent or clipping take. None means below -42 dBFS."""
    b = path.read_bytes()
    if b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        return None
    pos, width, data = 12, None, None
    while pos + 8 <= len(b):
        cid, size = b[pos:pos + 4], int.from_bytes(b[pos + 4:pos + 8], "little")
        if cid == b"fmt ":
            width = int.from_bytes(b[pos + 22:pos + 24], "little") // 8
        elif cid == b"data":
            data = b[pos + 8:pos + 8 + size]
            break
        pos += 8 + size + (size & 1)
    if not width or not data:
        return None
    msb = data[width - 1::width]
    peak = max(max((x for x in msb if x < 128), default=0),
               max((256 - x for x in msb if x >= 128), default=0))
    return None if peak == 0 else round(20 * math.log10(peak / 128), 1)


def arecord_cmd(args, device: str, seconds: int, path: str, filetype: str = "wav") -> list:
    return ["arecord", "-q", "-D", device, "-f", args.format, "-r", str(args.rate),
            "-c", str(args.channels), "-t", filetype, "-d", str(seconds), path]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pass-name", required=True,
                    help="name of this pass, e.g. default, open, env000, env255")
    ap.add_argument("--outdir", required=True, help="directory for this pass's takes")
    ap.add_argument("--patterns", type=parse_patterns, default=parse_patterns("1..64"),
                    help="e.g. 1..64 (default), 1..3, 2-5 (panel label), 1,9,17")
    ap.add_argument("--stimulus", choices=sorted(STIMULI), default="full",
                    help="full (about 26 s per take) or short (about 13 s)")
    ap.add_argument("--prm-dir", help="the RESTORE folder generated for this pass, "
                    "to store each pattern's settings with its take")
    ap.add_argument("--card", default="J6", help="ALSA card id for audio (default J6)")
    ap.add_argument("--midi", choices=("seq", "raw"), default="seq",
                    help="seq: ALSA sequencer via aplaymidi (default); raw: raw MIDI device")
    ap.add_argument("--midi-client", default="J-6",
                    help="sequencer client name to look up (default J-6)")
    ap.add_argument("--midi-port", help="sequencer port, e.g. 32:0, instead of the lookup")
    ap.add_argument("--midi-device", help="raw MIDI device, default /dev/snd/midiC<card>D0")
    ap.add_argument("--note-channel", type=int, default=1, help="J-6 menu CH (default 1)")
    ap.add_argument("--pc-channel", type=int, default=16, help="J-6 menu Pc.Ch (default 16)")
    ap.add_argument("--pc-offset", type=int, default=0,
                    help="Program Change number = pattern number - 1 + offset")
    ap.add_argument("--velocity", type=int, default=100)
    ap.add_argument("--settle", type=float, default=1.0,
                    help="seconds to wait after the Program Change")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--format", default="S24_3LE")
    ap.add_argument("--channels", type=int, default=2)
    ap.add_argument("--flac", action="store_true", help="compress each take with flac")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, touch nothing")
    args = ap.parse_args()

    stimulus = STIMULI[args.stimulus]
    events = build_schedule(stimulus, args.velocity, args.note_channel)
    end = max(on + gate for _, _, _, on, gate in stimulus) + TAIL[args.stimulus]
    seconds = math.ceil(PRE_ROLL + end + MARGIN)
    audio_dev = f"plughw:CARD={args.card},DEV=0"
    outdir = Path(args.outdir)
    prm_dir = Path(args.prm_dir) if args.prm_dir else None

    if args.dry_run:
        where = (args.midi_port or f"sequencer client '{args.midi_client}'") if args.midi == "seq" \
            else (args.midi_device or "raw device of the card")
        print(f"{len(args.patterns)} take(s) of {seconds} s, audio from {audio_dev}, "
              f"MIDI via {args.midi} to {where}")
        print("record: " + " ".join(arecord_cmd(args, audio_dev, seconds, "TAKE.wav")))
        print(f"select pattern n: Program Change n-1{args.pc_offset:+d} on channel "
              f"{args.pc_channel} = bytes {program(args.pc_channel, 0).hex(' ')} for pattern 1-1")
        for t, msg, name, kind in events:
            print(f"  {t:6.2f} s  {msg.hex(' ')}  {name} {kind}")
        for n in args.patterns:
            print(f"  {args.pass_name}_P{n:02d}_{label(n - 1)}")
        return

    tools = ["arecord"] + (["aplaymidi"] if args.midi == "seq" else []) + (["flac"] if args.flac else [])
    for tool in tools:
        if shutil.which(tool) is None:
            sys.exit(f"{tool} not found; install it (arecord and aplaymidi are in alsa-utils)")
    outdir.mkdir(parents=True, exist_ok=True)

    card = find_card(args.card)
    if args.midi == "seq":
        port = args.midi_port
        if port is None:
            port, listing = find_seq_port(args.midi_client)
            if port is None:
                sys.exit(f"no sequencer client named '{args.midi_client}'. aplaymidi -l says:\n"
                         f"{listing}\nconnect the J-6 and switch it on normally, "
                         "or name the port with --midi-port")
        midi = SeqMidi(port, outdir)
    else:
        if card is None and not args.midi_device:
            sys.exit(f"no ALSA card '{args.card}' in /proc/asound/cards: connect the J-6 "
                     "and switch it on normally (not in backup mode)")
        path = args.midi_device or f"/dev/snd/midiC{card}D0"
        try:
            midi = RawMidi(path)
        except OSError as e:
            sys.exit(f"cannot open {path}: {e}\nanother program holds the raw port; "
                     "use the default --midi seq")

    hw = outdir / "hw_params.txt"
    if not hw.exists():
        p = subprocess.run(["arecord", "-D", f"hw:CARD={args.card},DEV=0", "--dump-hw-params",
                            "-d", "1", "-f", args.format, "-r", str(args.rate),
                            "-c", str(args.channels), "-t", "raw", "/dev/null"],
                           capture_output=True, text=True, timeout=20)
        hw.write_text(p.stdout + p.stderr)
    p = subprocess.run(arecord_cmd(args, audio_dev, 1, "/dev/null", "raw"),
                       capture_output=True, text=True, timeout=20)
    if p.returncode != 0:
        midi.close()
        sys.exit(f"arecord cannot record from {audio_dev}:\n{p.stderr.strip()}\n\n{BUSY_HINT}")

    session_path = outdir / "session.json"
    session = json.loads(session_path.read_text()) if session_path.exists() else {"runs": []}
    run = {"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "script_version": VERSION, "argv": sys.argv[1:], "card": card,
           "midi_backend": midi.backend, "midi_target": midi.where,
           "audio_device": audio_dev, "recorded": []}
    session["runs"].append(run)

    print(f"pass '{args.pass_name}': {len(args.patterns)} take(s) of {seconds} s, "
          f"MIDI via {midi.backend} to {midi.where}. J-6 menu: CH {args.note_channel}, "
          f"Pc.Ch {args.pc_channel}, rxPc On. Sequencer stopped, knobs untouched. "
          "Ctrl-C stops cleanly.")
    rec, tmp, exit_code = None, None, 0
    try:
        for k, n in enumerate(args.patterns, 1):
            stem = f"{args.pass_name}_P{n:02d}_{label(n - 1)}"
            done = [outdir / f"{stem}.{ext}" for ext in ("wav", "flac")]
            if (outdir / f"{stem}.json").exists() and any(f.exists() for f in done):
                print(f"[{k}/{len(args.patterns)}] {stem}: already recorded, skipped")
                continue
            settings = {}
            if prm_dir:
                prm = prm_dir / f"J6_PTN{n:02d}.PRM"
                settings = read_prm(prm) if prm.exists() else {}
                if settings and int(settings["SOUND"]) != n - 1:
                    print(f"  warning: {prm.name} holds sound {label(int(settings['SOUND']))}")

            midi.send(silence(args.note_channel))
            time.sleep(0.2)
            pc = n - 1 + args.pc_offset
            midi.send([program(args.pc_channel, pc)])
            print(f"[{k}/{len(args.patterns)}] {stem}: pattern {label(n - 1)} selected, recording")
            time.sleep(args.settle)

            tmp = outdir / f"{stem}.part.wav"
            rec = subprocess.Popen(arecord_cmd(args, audio_dev, seconds, str(tmp)),
                                   stderr=subprocess.PIPE, text=True)
            t_spawn = time.perf_counter()
            time.sleep(PRE_ROLL)
            if rec.poll() is not None:
                raise RuntimeError(f"arecord stopped: {rec.stderr.read().strip()}\n{BUSY_HINT}")
            t0, sent = midi.play(events)
            rec.wait(timeout=seconds + 15)
            if rec.returncode != 0:
                raise RuntimeError(f"arecord failed: {rec.stderr.read().strip()}")
            rec = None
            peak = wav_peak_dbfs(tmp)
            final = outdir / f"{stem}.wav"
            tmp.rename(final)
            tmp = None
            if args.flac:
                flac_path = outdir / f"{stem}.flac"
                subprocess.run(["flac", "-s", "--best", "--delete-input-file",
                                "-o", str(flac_path), str(final)], check=True)
                final = flac_path

            event_log = []
            for name, note, vel, on, gate in stimulus:
                entry = {"name": name, "note": note, "velocity": vel or args.velocity,
                         "on": on, "off": round(on + gate, 4)}
                if sent:
                    entry.update(on_sent=sent[(name, "on")], off_sent=sent[(name, "off")])
                event_log.append(entry)
            sidecar = {
                "pass": args.pass_name, "stimulus": args.stimulus,
                "pattern": {"number": n, "label": label(n - 1), "program_change": pc},
                "prm": settings,
                "events": event_log,
                "recording": {"file": final.name, "seconds": seconds, "rate": args.rate,
                              "format": args.format, "channels": args.channels,
                              "midi_started_after_arecord_start_s": round(t0 - t_spawn, 4),
                              "peak_dbfs": peak},
                "midi": {"backend": midi.backend, "target": midi.where,
                         "note_channel": args.note_channel, "pc_channel": args.pc_channel},
                "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "script_version": VERSION,
            }
            (outdir / f"{stem}.json").write_text(json.dumps(sidecar, indent=1))
            run["recorded"].append(stem)
            level = "SILENT (below -42 dBFS)" if peak is None else f"peak {peak} dBFS"
            warn = "  <- check MIDI channel and volume" if peak is None else (
                "  <- near full scale" if peak > -0.5 else "")
            print(f"    {level}{warn}")
    except KeyboardInterrupt:
        print("\ninterrupted; completed takes are kept, rerun the same command to resume")
        exit_code = 130
    except (RuntimeError, subprocess.SubprocessError, OSError) as e:
        print(f"error: {e}\ncompleted takes are kept, rerun the same command to resume",
              file=sys.stderr)
        exit_code = 1
    finally:
        if rec is not None and rec.poll() is None:
            rec.terminate()
            rec.wait(timeout=5)
        if tmp is not None and tmp.exists():
            tmp.unlink()
        try:
            midi.send(silence(args.note_channel))
        except (RuntimeError, subprocess.SubprocessError, OSError):
            pass
        midi.close()
        run["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        session_path.write_text(json.dumps(session, indent=1))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
