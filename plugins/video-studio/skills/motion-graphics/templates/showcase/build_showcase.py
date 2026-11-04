#!/usr/bin/env python3
"""Generate voiceover, word timings and music for the showcase videos.

Needs: kokoro-onnx, soundfile, faster-whisper, numpy (pip), plus ffmpeg.
Usage (from the templates/ folder):
  python showcase/build_showcase.py --kokoro-dir /path/to/kokoro-files [--fps 30]

The Kokoro folder must contain kokoro-v1.0.onnx and voices-v1.0.bin from
https://github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0).
Writes public/showcase/vo/*.wav, public/showcase/music.wav and public/showcase/<video>.json.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf

# Tools installed by the plugin's bootstrap live in ~/.video-studio/bin (ffmpeg on Linux) and ~/.local/bin (uv).
os.environ["PATH"] = os.pathsep.join([str(Path.home() / ".video-studio" / "bin"), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "public", "showcase")
LEAD_IN = 0.35   # seconds of air before the voice starts in each scene
TAIL = 0.45      # seconds after the voice ends


def transcribe(model, path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = model.transcribe(np.frombuffer(raw, np.float32), word_timestamps=True, language="en")
    return [{"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for s in segs for w in s.words]


def snap_to_script(words, script_text):
    """Whisper can mishear brand words; keep its timings but use the script's spelling when the counts line up."""
    tokens = script_text.replace("A.I.", "AI").split()
    if not words:
        return words
    if len(tokens) == len(words):
        return [{**w, "text": t} for w, t in zip(words, tokens)]
    # counts differ: place script words along the heard timeline by character position
    heard = "".join(w["text"] for w in words)
    total_h = max(1, len(heard))
    def time_at(frac):  # map a 0-1 position in the heard text to seconds
        pos, acc = frac * total_h, 0
        for w in words:
            n = max(1, len(w["text"]))
            if pos <= acc + n:
                return w["start"] + (w["end"] - w["start"]) * (pos - acc) / n
            acc += n
        return words[-1]["end"]
    total_s = max(1, sum(len(t) for t in tokens))
    out, acc = [], 0
    for t in tokens:
        a, acc = acc, acc + len(t)
        out.append({"text": t, "start": round(time_at(a / total_s), 3), "end": round(time_at(acc / total_s), 3)})
    return out


def make_music(path, seconds):
    """Soft synth pad (Cmaj7 - Am7 - Fmaj7 - G6), 4 bars looped, gentle and royalty free."""
    chords = [[261.63, 329.63, 392.0, 493.88], [220.0, 261.63, 329.63, 392.0],
              [174.61, 220.0, 261.63, 329.63], [196.0, 246.94, 293.66, 329.63]]
    sr, bar = 48000, 4.0
    t = np.arange(int(sr * bar)) / sr
    env = np.minimum(1, t / 0.8) * np.minimum(1, (bar - t) / 0.8)
    bars = []
    for ch in chords:
        x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t + 0.5) for f in ch)
        x += 0.5 * np.sin(2 * np.pi * ch[0] / 2 * t)  # bass
        bars.append(x * env * (1 + 0.08 * np.sin(2 * np.pi * 0.25 * t)))
    loop = np.concatenate(bars)
    reps = math.ceil(seconds * sr / len(loop))
    y = np.tile(loop, reps)[: int(seconds * sr)]
    y = y / np.max(np.abs(y)) * 0.5
    fade = int(sr * 2)
    y[-fade:] *= np.linspace(1, 0, fade)
    tmp = path + ".raw.wav"
    sf.write(tmp, np.stack([y, y], 1).astype(np.float32), sr)
    # soften: low-pass + a little room
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af",
                    "lowpass=f=2200,aecho=0.8:0.6:60|120:0.25|0.18,volume=0.9", path], check=True)
    os.remove(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kokoro-dir", required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--only", default=None, help="build just one video id")
    a = ap.parse_args()

    from faster_whisper import WhisperModel
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(os.path.join(a.kokoro_dir, "kokoro-v1.0.onnx"), os.path.join(a.kokoro_dir, "voices-v1.0.bin"))
    whisper = WhisperModel("base.en", compute_type="int8")
    script = json.load(open(os.path.join(HERE, "script.json")))["videos"]
    os.makedirs(os.path.join(OUT, "vo"), exist_ok=True)

    for vid, spec in script.items():
        if a.only and vid != a.only:
            continue
        scenes, start = [], 0
        for sc in spec["scenes"]:
            wav = os.path.join(OUT, "vo", f"{vid}-{sc['id']}.wav")
            samples, sr = kokoro.create(sc["vo"], voice=spec["voice"], speed=spec.get("speed", 1.0), lang="en-us")
            sf.write(wav, samples, sr)
            vo_len = len(samples) / sr
            seconds = max(sc.get("minSeconds", 0), LEAD_IN + vo_len + TAIL)
            frames = math.ceil(seconds * a.fps)
            words = [{**w, "start": w["start"] + LEAD_IN, "end": w["end"] + LEAD_IN}
                     for w in snap_to_script(transcribe(whisper, wav), sc["vo"])]
            extra = {k: v for k, v in sc.items() if k not in ("vo", "minSeconds")}
            scenes.append({**extra, "vo": sc["vo"], "audio": f"showcase/vo/{vid}-{sc['id']}.wav",
                           "voStartFrame": round(LEAD_IN * a.fps), "durationInFrames": frames,
                           "startFrame": start, "words": words})
            start += frames
            print(f"{vid}/{sc['id']}: vo {vo_len:.2f}s -> scene {frames / a.fps:.2f}s")
        music = f"showcase/music-{vid}.wav"
        make_music(os.path.join(ROOT, "public", music), start / a.fps + 1)
        json.dump({"fps": a.fps, "durationInFrames": start, "music": music, "scenes": scenes},
                  open(os.path.join(OUT, f"{vid}.json"), "w"), indent=1)
        print(f"== {vid}: {start / a.fps:.1f}s, {len(scenes)} scenes")


if __name__ == "__main__":
    main()
