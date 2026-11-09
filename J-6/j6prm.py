#!/usr/bin/env python3
"""Inspect, harvest and generate Roland J-6 pattern files (J6_PTNnn.PRM).

The J-6 (system program 1.02) backs up each of its 64 patterns as an ASCII
file J6_PTN01.PRM ... J6_PTN64.PRM: 23 header lines "KEY<TAB>= value", then
64 "BAR n<TAB>= ..." lines, LF line endings. Files are copied off the unit in
backup mode and loaded back through its RESTORE folder.

  inspect  BACKUP_DIR
      Print the sound-related fields of the 64 patterns.
  defaults HARVEST_DIR -o defaults.csv [--before ORIGINAL_DIR]
      Read the per-sound defaults from a "harvest" backup, in which pattern n
      was given sound n on the unit (1-1 -> 1-1 ... 8-8 -> 8-8).
  generate --template FILE --out DIR [--defaults defaults.csv] [options]
      Write a complete set of 64 patterns for RESTORE, pattern n = sound n,
      with chosen control values and the delay and reverb levels at 0.

Standard library only, Python >= 3.8.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

N = 64
KNOBS = ("FILTER", "RESONANCE", "ENV", "ATTACK")
NEUTRAL = {"ENV": 128, "ATTACK": 0}  # values found in freshly initialised patterns
# Values the J-6 writes when it initialises a pattern (menu "init"): no phrase
# style, so notes arriving over MIDI are not shaped by STYLE / VARIATION.
INIT_STYLE = {"STYLE": -1, "VARIATION": -1, "STYLE_SW": 0}
LINE = re.compile(r"^(?P<key>[A-Z_]+(?: \d+)?)\t= (?P<value>.*)$")


def label(i: int) -> str:
    """0-based pattern or sound index -> label as on the panel (1-1 ... 8-8)."""
    return f"{i // 8 + 1}-{i % 8 + 1}"


class Prm:
    """One J6_PTNnn.PRM file, parsed so that it can be re-written byte for byte."""

    def __init__(self, path):
        self.path = Path(path)
        raw = self.path.read_bytes()
        text = raw.decode("ascii")  # anything else means the format is not understood
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.final_newline = text.endswith(self.newline)
        lines = text.split(self.newline)
        if self.final_newline:
            lines.pop()
        self.keys: list[str] = []
        self.values: dict[str, str] = {}
        for no, line in enumerate(lines, 1):
            m = LINE.match(line)
            if m is None:
                raise ValueError(f"{self.path}:{no}: unexpected line {line!r}")
            key = m["key"]
            if key in self.values:
                raise ValueError(f"{self.path}:{no}: duplicate key {key}")
            self.keys.append(key)
            self.values[key] = m["value"]
        if self.render() != raw:
            raise ValueError(f"{self.path}: cannot reproduce the file byte for byte")

    def __getitem__(self, key: str) -> int:
        return int(self.values[key])

    def bars_empty(self) -> bool:
        for key in self.keys:
            if key.startswith("BAR "):
                fields = dict(f.split("=", 1) for f in self.values[key].split())
                if any(fields.get(f"NOTE{i}", "-1") != "-1" for i in range(1, 5)):
                    return False
        return True

    def render(self, overrides: dict | None = None) -> bytes:
        overrides = overrides or {}
        unknown = set(overrides) - set(self.values)
        if unknown:
            raise KeyError(f"{self.path}: no such keys {sorted(unknown)}")
        lines = [f"{k}\t= {overrides.get(k, self.values[k])}" for k in self.keys]
        text = self.newline.join(lines) + (self.newline if self.final_newline else "")
        return text.encode("ascii")


def load_backup(directory) -> list[Prm]:
    """The 64 patterns of a backup folder (the BACKUP folder or its parent)."""
    directory = Path(directory)
    if not (directory / "J6_PTN01.PRM").exists() and (directory / "BACKUP").is_dir():
        directory = directory / "BACKUP"
    missing = [n for n in range(1, N + 1) if not (directory / f"J6_PTN{n:02d}.PRM").is_file()]
    if missing:
        sys.exit(f"{directory}: {len(missing)} pattern file(s) missing, "
                 f"first one J6_PTN{missing[0]:02d}.PRM")
    return [Prm(directory / f"J6_PTN{n:02d}.PRM") for n in range(1, N + 1)]


def cmd_inspect(args) -> None:
    patterns = load_backup(args.dir)
    cols = ("FILTER", "RESONANCE", "ENV", "ATTACK", "LEVEL", "TEMPO",
            "DELAY", "REVERB", "TRANSPOSE", "STYLE_SW")
    print(f"{'pattern':<8}{'sound':>6}" + "".join(f"{c[:9]:>10}" for c in cols) + "  bars")
    for i, p in enumerate(patterns):
        print(f"{label(i):<8}{label(p['SOUND']):>6}"
              + "".join(f"{p.values[c]:>10}" for c in cols)
              + ("  empty" if p.bars_empty() else "  notes"))


def cmd_defaults(args) -> None:
    after = load_backup(args.dir)
    rows, wrong = [], []
    for i, p in enumerate(after):
        valid = p["SOUND"] == i
        if not valid:
            wrong.append(f"pattern {label(i)} holds sound {label(p['SOUND'])}")
        rows.append({"sound": label(i), "sound_index": i,
                     **{k: p[k] for k in KNOBS}, "valid": int(valid)})
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sound", "sound_index", *KNOBS, "valid"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.output}: defaults for {N - len(wrong)} of {N} sounds")
    for msg in wrong:
        print(f"  not usable: {msg} instead of its own number")
    for k in ("ENV", "ATTACK"):
        counts = Counter(r[k] for r in rows if r["valid"])
        print(f"{k} values found: " + ", ".join(f"{v} (x{n})" for v, n in sorted(counts.items())))

    if args.before:
        before = load_backup(args.before)
        already = [label(i) for i, b in enumerate(before) if b["SOUND"] == i]
        if already:
            print("warning: these patterns already held their own sound before the harvest, "
                  "so their defaults may not have been reloaded: " + ", ".join(already))
        # Did choosing a sound reset ENV / ATTACK ? Only patterns that held
        # another sound and a non-neutral value beforehand can tell.
        for k in ("ENV", "ATTACK"):
            kept, changed = [], []
            for i, (b, a) in enumerate(zip(before, after)):
                if a["SOUND"] != i or b["SOUND"] == i or b[k] == NEUTRAL[k]:
                    continue
                (kept if a[k] == b[k] else changed).append(f"{label(i)}: {b[k]}->{a[k]}")
            if not kept and not changed:
                print(f"{k}: no pattern held a non-neutral value before, so no conclusion")
            else:
                print(f"{k}: choosing a sound kept the old value in {len(kept)} pattern(s), "
                      f"changed it in {len(changed)}")
                for line in changed:
                    print(f"  changed {line}")


def knob_value(text: str):
    if text == "default":
        return text
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected 0-255 or 'default'")
    if not 0 <= value <= 255:
        raise argparse.ArgumentTypeError("expected 0-255 or 'default'")
    return value


def read_defaults(path) -> dict[int, dict[str, int]]:
    table = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if int(row["valid"]):
                table[int(row["sound_index"])] = {k: int(row[k]) for k in KNOBS}
    return table


def cmd_generate(args) -> None:
    template = Prm(args.template)
    if not template.bars_empty():
        sys.exit(f"{args.template} has notes in its bars: use a freshly initialised pattern")
    wants_default = [k for k in KNOBS if getattr(args, k.lower()) == "default"]
    if wants_default and not args.defaults:
        sys.exit(f"'default' for {', '.join(wants_default)} needs --defaults "
                 "(a CSV written by the 'defaults' subcommand), or give numbers")
    defaults = read_defaults(args.defaults) if args.defaults else {}

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} exists and is not empty; choose a new directory")
    restore = out / "RESTORE"
    restore.mkdir(parents=True)

    manifest = []
    for i in range(N):
        values = {"SOUND": i, "DELAY": 0, "REVERB": 0, "TRANSPOSE": 0, **INIT_STYLE}
        for k in KNOBS:
            value = getattr(args, k.lower())
            if value == "default":
                if i not in defaults:
                    sys.exit(f"{args.defaults} has no valid default {k} for sound {label(i)}")
                value = defaults[i][k]
            values[k] = value
        if args.bpm is not None:
            values["TEMPO"] = round(args.bpm * 100)
        if args.level is not None:
            values["LEVEL"] = args.level
        path = restore / f"J6_PTN{i + 1:02d}.PRM"
        path.write_bytes(template.render(values))
        check = Prm(path)  # re-read: same keys in the same order, intended values
        if check.keys != template.keys or any(check[k] != int(v) for k, v in values.items()):
            sys.exit(f"{path}: verification failed")
        manifest.append({"pattern": label(i), "program_change": i, "sound": label(i),
                         **{k: check[k] for k in (*KNOBS, "TEMPO", "LEVEL")}})

    with open(out / "manifest.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"wrote {N} patterns to {restore}/ and {out / 'manifest.csv'}")
    print("copy the 64 .PRM files into the RESTORE folder of the J-6 drive, eject, press [CHORD]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect", help="list the sound-related fields of a backup")
    p.add_argument("dir", help="BACKUP folder (or its parent)")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("defaults", help="per-sound defaults from a harvest backup")
    p.add_argument("dir", help="BACKUP folder taken after the harvest pass")
    p.add_argument("-o", "--output", required=True, help="CSV file to write")
    p.add_argument("--before", help="BACKUP folder taken before the harvest pass")
    p.set_defaults(func=cmd_defaults)

    p = sub.add_parser("generate", help="write 64 patterns for RESTORE (pattern n = sound n)")
    p.add_argument("--template", required=True,
                   help="a freshly initialised pattern file from your own backup")
    p.add_argument("--out", required=True, help="new directory to create")
    p.add_argument("--defaults", help="CSV from the 'defaults' subcommand")
    p.add_argument("--filter", type=knob_value, default="default", help="0-255 or 'default'")
    p.add_argument("--resonance", type=knob_value, default="default", help="0-255 or 'default'")
    p.add_argument("--env", type=knob_value, default=128, help="0-255 or 'default' (128)")
    p.add_argument("--attack", type=knob_value, default=0, help="0-255 or 'default' (0)")
    p.add_argument("--bpm", type=float, help="pattern tempo, default: as in the template")
    p.add_argument("--level", type=int, help="pattern level, default: as in the template")
    p.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
