#!/usr/bin/env python3
"""Apply named audio effects from styles/audio-effects.json with ffmpeg.

Usage
  python audio_fx.py --list
  python audio_fx.py in.mp4 -o out.mp4 --effect "Dialogue Clarity" --effect "Dialogue Level"
  python audio_fx.py in.wav -o out.wav --effect "Telephone@2-5"     (only between 2 s and 5 s)

Effects run in the order given. Video (if any) is copied untouched.
"""
import argparse
import json
import subprocess
from pathlib import Path

STYLES = Path(__file__).resolve().parents[3] / "styles"

# Every catalog audio effect -> an ffmpeg filter chain with sensible defaults.
CHAINS = {
    "Chorus": "chorus=0.6:0.9:50|60:0.4|0.32:0.25|0.4:2|1.3",
    "Compressor": "acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=3",
    "De-esser": "deesser=i=0.5:m=0.5:f=0.5",
    "Delay / Echo": "aecho=0.8:0.75:320:0.35",
    "Dialogue Clarity": "highpass=f=90,afftdn=nf=-25,equalizer=f=300:t=q:w=1:g=-3,equalizer=f=3500:t=q:w=1:g=3",
    "Dialogue Level": "loudnorm=I=-16:TP=-1.5:LRA=11",
    "Saturation / Distortion": "volume=2.5,asoftclip=type=tanh,volume=0.6",
    "Dynamic EQ": "adynamicequalizer=dfrequency=6000:dqfactor=2:tfrequency=6000:tqfactor=2:threshold=20:ratio=3:mode=cut",
    "Equalizer": "equalizer=f=120:t=q:w=1:g=2,equalizer=f=400:t=q:w=1:g=-2,equalizer=f=4000:t=q:w=1:g=2",
    "Flanger": "flanger=delay=2:depth=3:regen=20:speed=0.4",
    "Gain": "volume=3dB",
    "Noise Gate": "agate=threshold=0.02:ratio=3:attack=5:release=120",
    "Hall": "aecho=0.8:0.85:60|120|180|260:0.4|0.3|0.22|0.15",
    "High-pass Filter": "highpass=f=120",
    "Limiter": "alimiter=limit=0.89:attack=5:release=50",
    "Low-pass Filter": "lowpass=f=4000",
    "Pan": "stereotools=balance_out=-0.4",
    "Phaser": "aphaser=type=t:speed=0.5:decay=0.5",
    "Reverb": "aecho=0.8:0.8:40|80|130:0.35|0.25|0.18",
    "Small Room": "aecho=0.8:0.6:15|28:0.25|0.15",
    "Subtle Echo": "aecho=0.8:0.5:250:0.15",
    "Telephone": "highpass=f=300,lowpass=f=3400,volume=2,asoftclip=type=atan,volume=0.7",
}


def find(name):
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    table = {norm(k): k for k in CHAINS}
    if norm(name) not in table:
        raise SystemExit(f'Unknown audio effect "{name}". Options: {", ".join(CHAINS)}')
    return table[norm(name)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--effect", action="append", default=[], help='name, optionally "Name@start-end" in seconds')
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        cat = {e["name"]: e.get("description", "") for e in json.load(open(STYLES / "audio-effects.json"))["effects"]}
        for k, v in CHAINS.items():
            print(f"{k:24s} {cat.get(k, '')[:90]}")
        print("\nCrossfades between clips: see transitions.py --list")
        return
    if not (a.input and a.output and a.effect):
        ap.error("give input, -o and at least one --effect (or --list)")

    parts = []
    for spec in a.effect:
        name, rng = (spec.rsplit("@", 1) + [None])[:2] if "@" in spec else (spec, None)
        chain = CHAINS[find(name)]
        if rng:
            s, e = rng.split("-", 1)
            # apply only inside the range: every filter in the chain gets ffmpeg timeline 'enable'
            en = f"between(t\\,{float(s or 0)}\\,{e})" if e not in ("", "end") else f"gte(t\\,{float(s or 0)})"
            chain = ",".join(f"{f}:enable='{en}'" if "=" in f else f"{f}=enable='{en}'" for f in chain.split(","))
        parts.append(chain)
        print(f"audio: {find(name)}{' @ ' + rng if rng else ''}")
    af = ",".join(parts)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-af", af]
    if Path(a.output).suffix.lower() in (".mp4", ".mov", ".mkv", ".m4v"):
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"]
    subprocess.run(cmd + [a.output], check=True)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
