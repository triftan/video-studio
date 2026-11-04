#!/usr/bin/env python3
"""Render an EDL (list of kept segments) into one video with frame-accurate cuts.

Usage:
  render_edl.py edl.json -o out.mp4 [--fade 0.015] [--preview] [--zoom-alternate 1.12]
  [--size 1920x1080] [--fps 30]

EDL entries: {"src": "a.mp4", "in": 1.2, "out": 5.8, "zoom": 1.0 (optional), "note": "..."}
--zoom-alternate punches every other segment in by that factor to hide jump cuts.
Audio gets a short fade at every cut so there are no clicks.
"""
import os
from pathlib import Path
import argparse
import json
import subprocess

# Tools installed by the plugin's bootstrap live in ~/.video-studio/bin (ffmpeg on Linux) and ~/.local/bin (uv).
os.environ["PATH"] = os.pathsep.join([str(Path.home() / ".video-studio" / "bin"), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edl")
    ap.add_argument("-o", "--output", default="out.mp4")
    ap.add_argument("--fade", type=float, default=0.015, help="audio fade at each cut, seconds")
    ap.add_argument("--zoom-alternate", type=float, default=None)
    ap.add_argument("--size", default="1920x1080", help="output WxH; sources are scaled+cropped to fill")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--preview", action="store_true", help="fast low-res render")
    a = ap.parse_args()

    edl = json.load(open(a.edl))
    if not edl:
        raise SystemExit("empty EDL")
    w, h = (int(x) for x in a.size.lower().split("x"))
    if a.preview:
        w, h = (w * 540 // h) // 2 * 2, 540

    inputs, chains, concat = [], [], []
    for i, seg in enumerate(edl):
        dur = seg["out"] - seg["in"]
        inputs += ["-ss", f"{seg['in']:.3f}", "-t", f"{dur:.3f}", "-i", seg["src"]]
        zoom = seg.get("zoom") or (a.zoom_alternate if a.zoom_alternate and i % 2 else 1.0)
        zw, zh = int(w * zoom) // 2 * 2, int(h * zoom) // 2 * 2
        fade_out = max(0.0, dur - a.fade)
        chains.append(
            f"[{i}:v]scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"fps={a.fps},setsar=1,setpts=PTS-STARTPTS[v{i}];"
            f"[{i}:a]aresample=48000,afade=t=in:d={a.fade},afade=t=out:st={fade_out:.3f}:d={a.fade},"
            f"asetpts=PTS-STARTPTS[a{i}]"
        )
        concat.append(f"[v{i}][a{i}]")

    graph = ";".join(chains) + ";" + "".join(concat) + f"concat=n={len(edl)}:v=1:a=1[v][a]"
    enc = ["-c:v", "libx264", "-crf", "28" if a.preview else "18",
           "-preset", "veryfast" if a.preview else "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", graph, "-map", "[v]", "-map", "[a]", *enc, a.output]
    subprocess.run(cmd, check=True)
    total = sum(s["out"] - s["in"] for s in edl)
    print(f"rendered {len(edl)} segments, {total:.1f}s -> {a.output}")


if __name__ == "__main__":
    main()
