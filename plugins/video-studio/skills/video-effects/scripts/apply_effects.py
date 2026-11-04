#!/usr/bin/env python3
"""Apply video effects, zoom presets, color grades and LUTs to time ranges of a video.

Examples
  python apply_effects.py --list
  python apply_effects.py in.mp4 -o out.mp4 --fx "Laser Eyes@3-6"
  python apply_effects.py in.mp4 -o out.mp4 --fx "Big Head@0-2.5" --zoom "slow-push@5-9" --grade "70s"
  python apply_effects.py in.mp4 -o out.mp4 --lut ../../../styles/luts/blue-tint.cube@0-end:0.6
  python apply_effects.py in.mp4 -o out.mp4 --plan plan.json

Range syntax: NAME@START-END[:STRENGTH]  (seconds; END may be "end"; no @ means the whole video).
A plan file is a JSON list: [{"type": "fx"|"zoom"|"grade"|"lut", "name": "...", "start": 0, "end": 2.5, "strength": 1}]

Face, hand, body and segmentation tracking (MediaPipe) runs only on frames inside the ranges of effects that need it.
Models download once to ~/.video-studio/models. Original audio is kept.
"""
import argparse
import inspect
import json
import math
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fxlib  # noqa: E402
import looks  # noqa: E402

MODEL_DIR = Path.home() / ".video-studio" / "models"
MODELS = {
    "face": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
    "hands": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "pose": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task",
    "seg": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
}
WORK_SHORT_SIDE = 720  # effects are tuned for this; larger video is processed at this size inside effect ranges


# ---------------------------------------------------------------- catalog
def effect_catalog():
    meta = {e["name"]: e for e in json.load(open(looks.STYLES / "pixel-effects.json"))["effects"]}
    out = {}
    for name, fn in fxlib.EFFECTS.items():
        src = inspect.getsource(fn)
        # helpers called by the effect also count (e.g. eye_beams uses the face)
        for helper in ("eye_beams",):
            if helper in src:
                src += inspect.getsource(getattr(fxlib, helper))
        needs = sorted({k for k, tok in (("face", "c.face"), ("hands", "c.hands"), ("pose", "c.pose"),
                                        ("seg", "c.cat"), ("seg", "c.person")) if tok in src})
        m = meta.get(name, {})
        out[name] = {"fn": fn, "needs": needs, "category": m.get("category", "effect"), "description": m.get("description", "")}
    return out


def find(name, names):
    """Case/space-insensitive lookup with a helpful error."""
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    table = {norm(n): n for n in names}
    if norm(name) in table:
        return table[norm(name)]
    close = [n for n in names if norm(name)[:4] in norm(n)]
    raise SystemExit(f'Unknown name "{name}". Did you mean: {", ".join(close[:6]) or "see --list"}?')


# ---------------------------------------------------------------- tracking
def ensure_models(kinds):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for k in kinds:
        url = MODELS[k]
        dest = MODEL_DIR / url.rsplit("/", 1)[1]
        if not dest.exists():
            print(f"downloading {dest.name} (one time)...", flush=True)
            urllib.request.urlretrieve(url, dest)
        paths[k] = str(dest)
    return paths


class Tracker:
    """Runs only the MediaPipe models that the requested effects need, in video mode, with light smoothing."""

    def __init__(self, kinds):
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
        self.mp, self.kinds = mp, set(kinds)
        paths = ensure_models(self.kinds)
        VM = vision.RunningMode.VIDEO
        self.face = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=paths["face"]), running_mode=VM, num_faces=1,
            output_facial_transformation_matrixes=True)) if "face" in self.kinds else None
        self.hands = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=paths["hands"]), running_mode=VM, num_hands=2)) if "hands" in self.kinds else None
        self.pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=paths["pose"]), running_mode=VM)) if "pose" in self.kinds else None
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=paths["seg"]), running_mode=VM, output_category_mask=True,
            output_confidence_masks=True)) if "seg" in self.kinds else None
        self.prev_face, self.prev_pose, self.last_index = None, None, -10

    def close(self):
        for m in (self.face, self.hands, self.pose, self.seg):
            if m is not None:
                m.close()
        self.face = self.hands = self.pose = self.seg = None

    def analyze(self, frame, index, fps):
        H, W = frame.shape[:2]
        ts = int(index * 1000 / fps)
        img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        contiguous = index == self.last_index + 1
        self.last_index = index
        r = {"face": None, "fmat": None, "hands": [], "pose": None, "cat": None, "person": None}
        if self.face:
            res = self.face.detect_for_video(img, ts)
            if res.face_landmarks:
                pts = np.array([(p.x * W, p.y * H) for p in res.face_landmarks[0]], np.float32)
                if contiguous and self.prev_face is not None:
                    pts = self.prev_face * 0.45 + pts * 0.55
                self.prev_face = pts
                r["face"] = pts
                if res.facial_transformation_matrixes:
                    r["fmat"] = np.array(res.facial_transformation_matrixes[0])
            else:
                self.prev_face = None
        if self.hands:
            res = self.hands.detect_for_video(img, ts)
            r["hands"] = [np.array([(p.x * W, p.y * H) for p in h], np.float32) for h in res.hand_landmarks[:2]]
        if self.pose:
            res = self.pose.detect_for_video(img, ts)
            if res.pose_landmarks:
                P = np.array([(p.x * W, p.y * H, p.visibility) for p in res.pose_landmarks[0]], np.float32)
                if contiguous and self.prev_pose is not None:
                    P[:, :2] = self.prev_pose[:, :2] * 0.45 + P[:, :2] * 0.55
                self.prev_pose = P
                r["pose"] = P
        if self.seg:
            res = self.seg.segment_for_video(img, ts)
            r["cat"] = res.category_mask.numpy_view().copy()
            r["person"] = np.clip(1 - res.confidence_masks[0].numpy_view(), 0, 1).astype(np.float32)
        return r


class Ctx:
    pass


# ---------------------------------------------------------------- plan
def parse_spec(spec, kind, duration):
    name, rng, strength = spec, None, 1.0
    if "@" in spec:
        name, rng = spec.rsplit("@", 1)
    if rng and ":" in rng:
        rng, st = rng.rsplit(":", 1)
        strength = float(st)
    start, end = 0.0, duration
    if rng:
        a, b = rng.split("-", 1)
        start = float(a) if a else 0.0
        end = duration if b in ("", "end") else float(b)
    return {"type": kind, "name": name.strip(), "start": start, "end": min(end, duration), "strength": strength}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--fx", action="append", default=[], help='effect, e.g. "Laser Eyes@3-6"')
    ap.add_argument("--zoom", action="append", default=[], help='zoom preset, e.g. "slow-push@0-4"')
    ap.add_argument("--grade", action="append", default=[], help='color preset, e.g. "70s" or "AG200@2-8:0.7"')
    ap.add_argument("--lut", action="append", default=[], help="path to a .cube LUT, e.g. look.cube@0-end:0.8")
    ap.add_argument("--plan", help="JSON list of operations")
    ap.add_argument("--list", action="store_true", help="list every effect, zoom preset and color grade")
    ap.add_argument("--json", action="store_true", help="with --list, print JSON")
    ap.add_argument("--crf", type=int, default=18)
    a = ap.parse_args()

    cat = effect_catalog()
    if a.list:
        data = {"effects": {k: {kk: v[kk] for kk in ("category", "needs", "description")} for k, v in cat.items()},
                "zoom_presets": list(looks.zoom_presets()), "color_grades": list(looks.color_presets())}
        if a.json:
            print(json.dumps(data, indent=1, ensure_ascii=False))
        else:
            for k, v in data["effects"].items():
                print(f"{k:28s} {v['category']:7s} needs: {', '.join(v['needs']) or '-':18s} {v['description'][:70]}")
            print("\nzoom presets:", ", ".join(data["zoom_presets"]))
            print("color grades:", ", ".join(data["color_grades"]), "(or --lut any .cube file)")
        return
    if not a.input or not a.output:
        ap.error("input and -o/--output are required (or use --list)")

    cap = cv2.VideoCapture(a.input)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {a.input}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = n_frames / fps

    ops = []
    for kind, specs in (("fx", a.fx), ("zoom", a.zoom), ("grade", a.grade), ("lut", a.lut)):
        ops += [parse_spec(s, kind, duration) for s in specs]
    if a.plan:
        for o in json.load(open(a.plan)):
            o.setdefault("start", 0)
            o["end"] = duration if o.get("end") in (None, "end") else min(float(o["end"]), duration)
            o.setdefault("strength", 1.0)
            ops.append(o)
    if not ops:
        ap.error("nothing to apply: add --fx, --zoom, --grade, --lut or --plan")

    zooms, grades = looks.zoom_presets(), looks.color_presets()
    needs = set()
    for o in ops:
        if o["type"] == "fx":
            o["name"] = find(o["name"], list(cat))
            needs |= set(cat[o["name"]]["needs"])
        elif o["type"] == "zoom":
            o["name"] = find(o["name"], list(zooms))
        elif o["type"] == "grade":
            o["name"] = find(o["name"], list(grades))
        elif o["type"] == "lut":
            o["lut"] = looks.load_cube(o["name"])
        print(f'{o["type"]:5s} {o["name"]}  {o["start"]:.2f}s - {o["end"]:.2f}s', flush=True)

    tracker = Tracker(needs) if needs else None
    scale = min(1.0, WORK_SHORT_SIDE / min(W, H))
    ww, wh = int(round(W * scale / 2) * 2), int(round(H * scale / 2) * 2)
    fxlib.FRAME_W, fxlib.FRAME_H = ww, wh

    tmp = str(Path(a.output).with_suffix(".video-only.mp4"))
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", f"{fps:.6f}", "-i", "-", "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium",
                            "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    skipped = {}
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = i / fps
        active = [o for o in ops if o["start"] <= t < o["end"]]
        if active:
            work = cv2.resize(frame, (ww, wh), interpolation=cv2.INTER_AREA) if scale < 1 else frame
            track = tracker.analyze(work, i, fps) if tracker and any(o["type"] == "fx" and cat[o["name"]]["needs"] for o in active) else {}
            out = work.copy()
            for o in active:
                lt = t - o["start"]
                if o["type"] == "fx":
                    info = cat[o["name"]]
                    if "face" in info["needs"] and track.get("face") is None:
                        skipped[o["name"]] = skipped.get(o["name"], 0) + 1
                        continue
                    c = Ctx()
                    c.g, c.k, c.t = i, int(round(lt * fps)), lt
                    c.p = lt / max(1e-6, o["end"] - o["start"])
                    c.face = fxlib.Face(track["face"], track.get("fmat")) if track.get("face") is not None else None
                    c.hands = track.get("hands", [])
                    c.pose = track.get("pose") if track.get("pose") is not None else np.zeros((33, 3), np.float32)
                    c.cat = cv2.resize(track["cat"], (ww, wh), interpolation=cv2.INTER_NEAREST) if track.get("cat") is not None else np.zeros((wh, ww), np.uint8)
                    c.person = cv2.resize(track["person"], (ww, wh)) if track.get("person") is not None else np.zeros((wh, ww), np.float32)
                    res = info["fn"](out, c)
                    if o["strength"] < 1:
                        res = cv2.addWeighted(out, 1 - o["strength"], res, o["strength"], 0)
                    out = res
                elif o["type"] == "zoom":
                    z = zooms[o["name"]]
                    s = looks.zoom_scale(z, lt, o["end"] - o["start"])
                    out = looks.apply_zoom(out, 1 + (s - 1) * o["strength"], 0.5, z["propertyOverrides"].get("focalPointY", 0.37))
                elif o["type"] == "grade":
                    out = looks.grade(out, grades[o["name"]], i, o["strength"])
                elif o["type"] == "lut":
                    out = looks.apply_lut(out, o["lut"], o["strength"])
            frame = cv2.resize(out, (W, H), interpolation=cv2.INTER_LANCZOS4) if scale < 1 else out
        enc.stdin.write(np.ascontiguousarray(frame).tobytes())
        i += 1
        if i % 120 == 0:
            print(f"  {i}/{n_frames} frames", flush=True)
    enc.stdin.close()
    enc.wait()
    if tracker:
        tracker.close()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", a.input, "-map", "0:v", "-map", "1:a?",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.output], check=True)
    os.remove(tmp)
    for name, n in skipped.items():
        print(f'note: "{name}" skipped {n} frames where no face was found')
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
