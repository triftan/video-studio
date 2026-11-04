#!/usr/bin/env python3
"""Make a labelled reel that shows every effect (or a chosen few) on one clip.

Usage
  python effects_reel.py clip.mp4 -o reel.mp4                     # all 83 effects, 2 s each
  python effects_reel.py clip.mp4 -o reel.mp4 --only "Laser Eyes" --only "Stone" --seconds 3
  python effects_reel.py clip.mp4 -o reel.mp4 --music bed.wav

Best with a clip of one person facing the camera, with hands visible for a few seconds.
"""
import os
import argparse
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fxlib  # noqa: E402
from apply_effects import Ctx, Tracker, effect_catalog, find  # noqa: E402

# Tools installed by the plugin's bootstrap live in ~/.video-studio/bin (ffmpeg on Linux) and ~/.local/bin (uv).
os.environ["PATH"] = os.pathsep.join([str(Path.home() / ".video-studio" / "bin"), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])

CAT_COL = {"effect": (255, 196, 61), "zoom": (95, 205, 255), "mask": (120, 240, 160), "lut": (255, 140, 200)}


def label_layer(W, H, i, total, name, info):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = min(W, H) / 720
    d.rectangle([0, 0, W, int(150 * u)], fill=(8, 8, 12, 175))
    d.text((32 * u, 30 * u), f"{i:02d} / {total}", font=fxlib.font(fxlib.FONT_BOLD, int(24 * u)), fill=(255, 255, 255, 170))
    size = int((54 if len(name) < 18 else 42 if len(name) < 24 else 34) * u)
    d.text((32 * u, 66 * u), name, font=fxlib.font(fxlib.FONT_BOLD, size), fill=(255, 255, 255, 255))
    cat = info["category"]
    f = fxlib.font(fxlib.FONT_BOLD, int(20 * u))
    tw = d.textlength(cat.upper(), font=f)
    d.rounded_rectangle([W - 32 * u - tw - 28 * u, 32 * u, W - 32 * u, 70 * u], radius=int(19 * u), fill=CAT_COL.get(cat, (255, 255, 255)) + (255,))
    d.text((W - 32 * u - tw - 14 * u, 51 * u), cat.upper(), font=f, fill=(15, 15, 15, 255), anchor="lm")
    desc = "".join(ch for ch in info["description"].split(" (")[0] if ord(ch) < 0x2E80).strip()
    lines = textwrap.wrap(desc, int(46 * W / max(W, H) * (16 / 9 if W > H else 1)))[:3]
    if lines:
        hh = int((36 + 34 * len(lines)) * u)
        d.rectangle([0, H - hh - 20 * u, W, H], fill=(8, 8, 12, 165))
        for j, ln in enumerate(lines):
            d.text((32 * u, H - hh + j * 34 * u), ln, font=fxlib.font(fxlib.FONT_BOLD, int(23 * u)), fill=(235, 235, 240, 255))
    return np.asarray(im).astype(np.float32) / 255


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--music", default=None)
    a = ap.parse_args()

    cat = effect_catalog()
    names = [find(n, list(cat)) for n in a.only] or list(cat)
    cap = cv2.VideoCapture(a.clip)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    if not frames:
        raise SystemExit("could not read the clip")
    H0, W0 = frames[0].shape[:2]
    s = min(1.0, 720 / min(W0, H0))
    W, H = int(round(W0 * s / 2) * 2), int(round(H0 * s / 2) * 2)
    frames = [cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA) for f in frames] if s < 1 else frames
    fxlib.FRAME_W, fxlib.FRAME_H = W, H
    fxlib.SAFE_TOP = int(175 * min(W, H) / 720)  # keep stickers below the label

    needs = set().union(*(cat[n]["needs"] for n in names))
    print(f"tracking {len(frames)} frames ({', '.join(sorted(needs)) or 'none needed'})...", flush=True)
    tracker = Tracker(needs) if needs else None
    track = [tracker.analyze(f, i, fps) if tracker else {} for i, f in enumerate(frames)]
    if tracker:
        tracker.close()

    seg = int(round(a.seconds * fps))
    if seg >= len(frames):
        raise SystemExit(f"the clip must be longer than {a.seconds} s")
    has_hands = np.array([len(t.get("hands", [])) > 0 for t in track])
    silent = str(Path(a.output).with_suffix(".silent.mp4"))
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps:.6f}",
                            "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i, name in enumerate(names, 1):
        info = cat[name]
        lab = label_layer(W, H, i, len(names), name, info)
        start = int(np.argmax([has_hands[k:k + seg].sum() for k in range(len(frames) - seg)])) if "hands" in info["needs"] \
            else (i * 53) % (len(frames) - seg)
        for k in range(seg):
            g = start + k
            t = track[g]
            out = frames[g].copy()
            if "face" not in info["needs"] or t.get("face") is not None:
                c = Ctx()
                c.g, c.k, c.t, c.p = g, k, k / fps, k / max(1, seg - 1)
                c.face = fxlib.Face(t["face"], t.get("fmat")) if t.get("face") is not None else None
                c.hands = t.get("hands", [])
                c.pose = t["pose"] if t.get("pose") is not None else np.zeros((33, 3), np.float32)
                c.cat = cv2.resize(t["cat"], (W, H), interpolation=cv2.INTER_NEAREST) if t.get("cat") is not None else np.zeros((H, W), np.uint8)
                c.person = cv2.resize(t["person"], (W, H)) if t.get("person") is not None else np.zeros((H, W), np.float32)
                out = info["fn"](out, c)
            al = lab[..., 3:4] * min(1, (k + 1) / 6)
            out = np.clip(out * (1 - al) + lab[..., :3][..., ::-1] * 255 * al, 0, 255).astype(np.uint8)
            enc.stdin.write(out.tobytes())
        print(f"{i:02d} {name}", flush=True)
    enc.stdin.close()
    enc.wait()
    if a.music:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", a.music, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-shortest", "-movflags", "+faststart", a.output], check=True)
        Path(silent).unlink()
    else:
        Path(silent).replace(a.output)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
