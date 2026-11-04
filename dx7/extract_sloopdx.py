#!/usr/bin/env python3
"""Extract the sloopDX factory DX7 voices (github.com/zvenson/dxsloop, GPL-3.0-only)
from firmware/src/dx7_bank.h into DX7 32-voice bulk dumps (.syx, 4104 bytes).

    python3 extract_sloopdx.py path/to/dxsloop/firmware/src/dx7_bank.h [outdir]

The header holds unpacked voices (156 bytes, VCED order); they are packed to the
128-byte VMEM format exactly as the firmware's dx_pack() (firmware/src/eng_dx7.c) does.
Unused slots are filled with INIT VOICE.
"""
import re
import sys
from pathlib import Path


def arrays(src, name):
    """rows '{b0, b1, ...},   /* NAME */' of the C array `name` -> [(label, bytes)]"""
    start = src.index(name)
    end = src.index("\n};", start)
    return [(m.group(2).strip(), [int(x) for x in m.group(1).split(",")])
            for m in re.finditer(r"\{([0-9, ]+)\},\s*/\* (.*?) \*/", src[start:end])]


def pack(u):
    assert len(u) >= 155
    b = []
    for op in range(6):                       # OP6 first, as stored
        o = u[op * 21:(op + 1) * 21]
        b += o[0:11]                          # EG rates, EG levels, breakpoint, L/R depth
        b.append(o[11] | o[12] << 2)          # left | right curve
        b.append(o[13] | o[20] << 3)          # rate scaling | detune
        b.append(o[14] | o[15] << 2)          # AMS | key velocity sensitivity
        b.append(o[16])                       # output level
        b.append(o[17] | o[18] << 1)          # osc mode | coarse
        b.append(o[19])                       # fine
    b += u[126:134]                           # pitch EG rates, levels
    b.append(u[134])                          # algorithm
    b.append(u[135] | u[136] << 3)            # feedback | osc key sync
    b += u[137:141]                           # LFO speed, delay, PMD, AMD
    b.append(u[141] | u[142] << 1 | u[143] << 4)   # LFO sync | wave | PMS
    b.append(u[144])                          # transpose
    b += u[145:155]                           # name
    assert len(b) == 128 and all(0 <= x < 128 for x in b)
    return b


def bulk(voices, init):
    voices = list(voices) + [init] * (32 - len(voices))
    data = [x for v in voices[:32] for x in pack(v)]
    return bytes([0xF0, 0x43, 0x00, 0x09, 0x20, 0x00, *data, (-sum(data)) & 0x7F, 0xF7])


def main(hdr, outdir="."):
    src = Path(hdr).read_text()
    synth = arrays(src, "DX_SYNTH[DX_NSYNTH][156]")
    drums = arrays(src, "DX_DRUM_VOICE[DX_NDRUM][156]")
    init = dict(synth)["INIT VOICE"]
    out = Path(outdir)
    for fn, vs in (("sloopdx-factory.syx", synth), ("sloopdx-dxkit-drums.syx", drums)):
        s = bulk([v for _, v in vs], init)
        assert len(s) == 4104
        (out / fn).write_bytes(s)
        print(f"{fn}: {len(vs)} voices ({', '.join(n for n, _ in vs)})")


if __name__ == "__main__":
    main(*sys.argv[1:])
