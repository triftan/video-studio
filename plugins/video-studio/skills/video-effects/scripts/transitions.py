#!/usr/bin/env python3
"""Join clips with named transitions from styles/transitions.json (rendered with ffmpeg xfade).

Usage
  python transitions.py --list
  python transitions.py a.mp4 b.mp4 -o out.mp4 --transition "Whip Pan" --duration 0.4
  python transitions.py a.mp4 b.mp4 c.mp4 -o out.mp4 --transition "Cross Dissolve" --transition "Flash"
  (one --transition per join; the last one repeats if there are more joins than names)

Audio is crossfaded with the matching audio transition (default "Constant Power"); use --audio-transition to choose.
Clips are scaled/padded to the first clip's size and frame rate.
"""
import os
import argparse
import json
import subprocess
from pathlib import Path

# Tools installed by the plugin's bootstrap live in ~/.video-studio/bin (ffmpeg on Linux) and ~/.local/bin (uv).
os.environ["PATH"] = os.pathsep.join([str(Path.home() / ".video-studio" / "bin"), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])

STYLES = Path(__file__).resolve().parents[3] / "styles"

# Every catalog transition -> the closest ffmpeg xfade transition.
XFADE = {
    "Anticipation Zoom": "zoomin", "Clean Line Wipe": "wipeleft", "Cross Dissolve": "fade", "Dip to Black": "fadeblack",
    "Flash": "fadewhite", "blend": "dissolve", "push-down": "slidedown", "push-left": "slideleft", "push-right": "slideright",
    "push-up": "slideup", "slide-down": "coverdown", "slide-left": "coverleft", "slide-right": "coverright", "slide-up": "coverup",
    "wipe-barn-door-h": "horzopen", "wipe-barn-door-v": "vertopen", "wipe-circle": "circleopen", "wipe-down": "wipedown",
    "wipe-left": "wipeleft", "wipe-rect": "rectcrop", "wipe-right": "wiperight", "wipe-up": "wipeup", "xfade0r": "fade",
    "Impact Shake": "squeezeh", "Luma Blend": "fadegrays", "Organic Light Dissolve": "dissolve", "Page Curl": "diagtl",
    "Rack Focus": "hblur", "Soft Wipe": "smoothleft", "Whip Pan": "hlwind",
}
DEFAULT_SECONDS = {"Flash": 0.25, "Impact Shake": 0.25, "Whip Pan": 0.35, "Anticipation Zoom": 0.4, "Dip to Black": 0.8,
                   "Organic Light Dissolve": 0.9, "Rack Focus": 0.7}
# Audio crossfade curves (acrossfade c1/c2)
ACURVE = {"Constant Power": ("qsin", "qsin"), "Constant Gain": ("tri", "tri"), "Exponential Fade": ("exp", "exp"),
          "Fade Through Silence": ("losi", "losi")}


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    return float(d["format"]["duration"]), v["width"], v["height"], num / den, any(s["codec_type"] == "audio" for s in d["streams"])


def find(name):
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    table = {norm(k): k for k in XFADE}
    if norm(name) not in table:
        raise SystemExit(f'Unknown transition "{name}". Options: {", ".join(XFADE)}')
    return table[norm(name)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*")
    ap.add_argument("-o", "--output")
    ap.add_argument("--transition", action="append", default=[])
    ap.add_argument("--duration", type=float, default=None, help="seconds; default depends on the transition")
    ap.add_argument("--audio-transition", default="Constant Power", choices=list(ACURVE))
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        cat = {t["name"]: t.get("description", "") for t in json.load(open(STYLES / "transitions.json"))["transitions"]}
        for k, v in XFADE.items():
            print(f"{k:24s} ffmpeg:{v:11s} {cat.get(k, '')[:80]}")
        print("\naudio crossfades:", ", ".join(ACURVE))
        return
    if len(a.clips) < 2 or not a.output:
        ap.error("give at least two clips and -o (or --list)")
    names = [find(n) for n in (a.transition or ["Cross Dissolve"])]
    info = [probe(c) for c in a.clips]
    W, H, fps = info[0][1], info[0][2], info[0][3]

    inputs, chains = [], []
    for i, c in enumerate(a.clips):
        inputs += ["-i", c]
        chains.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:-1:-1,fps={fps:.6f},format=yuv420p,setsar=1[v{i}]")
        if info[i][4]:
            chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:
            chains.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{info[i][0]:.3f}[a{i}]")
    vlab, alab, offset = "v0", "a0", info[0][0]
    c1, c2 = ACURVE[a.audio_transition]
    for j in range(1, len(a.clips)):
        name = names[min(j - 1, len(names) - 1)]
        d = a.duration or DEFAULT_SECONDS.get(name, 0.5)
        d = min(d, info[j - 1][0] / 2, info[j][0] / 2)
        offset -= d
        chains.append(f"[{vlab}][v{j}]xfade=transition={XFADE[name]}:duration={d:.3f}:offset={offset:.3f}[vx{j}]")
        chains.append(f"[{alab}][a{j}]acrossfade=d={d:.3f}:c1={c1}:c2={c2}[ax{j}]")
        vlab, alab = f"vx{j}", f"ax{j}"
        offset += info[j][0]
        print(f"join {j}: {name} ({XFADE[name]}), {d:.2f}s")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains), "-map", f"[{vlab}]",
                    "-map", f"[{alab}]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", a.output], check=True)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
