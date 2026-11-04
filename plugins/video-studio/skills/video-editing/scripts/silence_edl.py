#!/usr/bin/env python3
"""Detect silences with ffmpeg and write an EDL that keeps the speech.

Usage:
  silence_edl.py input.mp4 [--noise -35] [--min-silence 0.6] [--pad 0.12] [-o edl.json]

Output: [{"src": "input.mp4", "in": 0.0, "out": 4.21, "note": "speech"}, ...]
"""
import os
from pathlib import Path
import argparse
import json
import re
import subprocess

# Tools installed by the plugin's bootstrap live in ~/.video-studio/bin (ffmpeg on Linux) and ~/.local/bin (uv).
os.environ["PATH"] = os.pathsep.join([str(Path.home() / ".video-studio" / "bin"), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])


def media_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def detect_silences(path, noise_db, min_silence):
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn",
         "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", proc.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", proc.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--noise", type=float, default=-35, help="silence threshold in dB")
    ap.add_argument("--min-silence", type=float, default=0.6, help="seconds")
    ap.add_argument("--pad", type=float, default=0.12, help="air kept around speech, seconds")
    ap.add_argument("--min-keep", type=float, default=0.25, help="drop kept pieces shorter than this")
    ap.add_argument("-o", "--output", default="edl.json")
    a = ap.parse_args()

    total = media_duration(a.input)
    silences = detect_silences(a.input, a.noise, a.min_silence)

    keep, cursor = [], 0.0
    for s, e in silences:
        e = total if e is None else e
        seg_in, seg_out = max(0.0, cursor - a.pad if cursor else 0.0), min(total, s + a.pad)
        if seg_out - seg_in >= a.min_keep:
            keep.append([seg_in, seg_out])
        cursor = e
    if cursor < total:
        keep.append([max(0.0, cursor - a.pad), total])

    merged = []
    for seg in keep:  # merge pieces that overlap after padding
        if merged and seg[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], seg[1])
        else:
            merged.append(seg)

    edl = [{"src": a.input, "in": round(i, 3), "out": round(o, 3), "note": "speech"} for i, o in merged]
    json.dump(edl, open(a.output, "w", encoding="utf-8"), indent=2)
    kept = sum(o - i for i, o in merged)
    print(f"{len(edl)} segments, kept {kept:.1f}s of {total:.1f}s ({100 * kept / total:.0f}%) -> {a.output}")


if __name__ == "__main__":
    main()
