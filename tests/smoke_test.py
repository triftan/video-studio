#!/usr/bin/env python3
"""End-to-end smoke test: runs the plugin the way a student would, after bootstrap.

Run with the plugin's Python:  ~/.video-studio/venv/bin/python tests/smoke_test.py
(Windows: %USERPROFILE%\\.video-studio\\venv\\Scripts\\python.exe tests\\smoke_test.py)
Exits non-zero on the first failure and prints which step failed.
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "video-studio"
VS = Path.home() / ".video-studio"
WIN = platform.system() == "Windows"
os.environ["PATH"] = os.pathsep.join([str(VS / "bin"), str(VS / "node" / ("" if WIN else "bin")), str(Path.home() / ".local" / "bin"),
                                      os.environ.get("PATH", "")])
PY = sys.executable
OUT = ROOT / "tests" / "out"
OUT.mkdir(parents=True, exist_ok=True)
FACE_URL = "https://assets.mixkit.co/videos/42323/42323-720.mp4"  # Mixkit free license
results = []


def run(name, cmd, cwd=None, timeout=900, shell=False):
    t = time.time()
    print(f"\n=== {name}\n$ {cmd if isinstance(cmd, str) else ' '.join(map(str, cmd))}", flush=True)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, shell=shell,
                       encoding="utf-8", errors="replace")
    tail = (p.stdout + p.stderr).strip().splitlines()[-15:]
    print("\n".join(tail))
    ok = p.returncode == 0
    results.append((name, ok, round(time.time() - t, 1)))
    if not ok:
        print(f"FAILED: {name} (exit {p.returncode})")
        summary()
        sys.exit(1)
    return p


def expect_file(name, path, min_bytes=1000):
    ok = Path(path).exists() and Path(path).stat().st_size >= min_bytes
    results.append((f"{name} output", ok, 0))
    print(f"{'ok' if ok else 'MISSING'}: {path} ({Path(path).stat().st_size if Path(path).exists() else 0} bytes)")
    if not ok:
        summary()
        sys.exit(1)


def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", str(path)],
                       capture_output=True, text=True)
    return json.loads(p.stdout or "{}")


def summary():
    print("\n==== SUMMARY ({})".format(platform.platform()))
    for n, ok, s in results:
        print(f"{'PASS' if ok else 'FAIL'}  {n}  {s}s")


def main():
    os.chdir(OUT)
    # 0. doctor (Node) reports nothing required missing
    node = shutil.which("node") or str(VS / "node" / ("node.exe" if WIN else "bin/node"))
    d = run("doctor", [node, str(PLUGIN / "scripts" / "doctor.mjs")])
    rep = json.loads(d.stdout)
    print("missing_required:", rep["missing_required"])
    if rep["missing_required"]:
        results.append(("doctor: nothing missing", False, 0)); summary(); sys.exit(1)

    # 1. test clips: synthetic talk with silences + a real face clip
    run("make synthetic clip", ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=8", "-f", "lavfi",
                                "-i", "sine=f=330:d=8", "-filter_complex",
                                "[1:a]volume='if(between(t,2,3.2)+between(t,5,6),0,1)':eval=frame[a]", "-map", "0:v", "-map", "[a]",
                                "-shortest", "-c:v", "libx264", "-c:a", "aac", "talk.mp4"])
    if not Path("face.mp4").exists():
        print("downloading face clip...")
        req = urllib.request.Request(FACE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open("face.mp4", "wb") as f:
            f.write(r.read())
    run("trim face clip", ["ffmpeg", "-y", "-loglevel", "error", "-i", "face.mp4", "-t", "6", "-c", "copy", "face6.mp4"])

    ve = PLUGIN / "skills" / "video-editing" / "scripts"
    fx = PLUGIN / "skills" / "video-effects" / "scripts"

    # 2. video-editing: silences -> EDL -> render -> captions burn-in (relative and absolute ass paths)
    run("silence_edl", [PY, str(ve / "silence_edl.py"), "talk.mp4", "-o", "edl.json"])
    run("render_edl", [PY, str(ve / "render_edl.py"), "edl.json", "-o", "cut.mp4", "--zoom-alternate", "1.12", "--size", "1080x1920"])
    expect_file("render_edl", "cut.mp4")
    words = [{"text": w, "start": i * 0.4, "end": i * 0.4 + 0.35} for i, w in enumerate("this is a caption test on every platform".split())]
    Path("words.json").write_text(json.dumps(words))
    for preset in ("tiktok", "submagic", "luxe"):
        run(f"captions_to_ass {preset}", [PY, str(ve / "captions_to_ass.py"), "words.json", "--preset", preset, "--size", "1080x1920",
                                          "-o", f"cap-{preset}.ass"])
    run("burn captions (relative path)", ["ffmpeg", "-y", "-loglevel", "error", "-i", "cut.mp4", "-vf", "ass=cap-tiktok.ass", "-c:a", "copy",
                                          "captioned.mp4"])
    expect_file("burn captions", "captioned.mp4")

    # 3. video-effects: tracking effects, grade, LUT, zoom; transitions; audio; reel
    run("apply_effects --list", [PY, str(fx / "apply_effects.py"), "--list"])
    run("apply_effects face+grade+lut+zoom", [PY, str(fx / "apply_effects.py"), "face6.mp4", "-o", "fx.mp4",
                                             "--fx", "Laser Eyes@0-1.5", "--fx", "Hair Regions@1.5-3", "--fx", "Hand Landmarks@3-4",
                                             "--zoom", "quick-in@4-6", "--grade", "AG200@0-end:0.8",
                                             "--lut", str(PLUGIN / "styles" / "luts" / "blue-tint.cube") + "@5-6:0.5"], timeout=1800)
    expect_file("apply_effects", "fx.mp4")
    run("effects_reel", [PY, str(fx / "effects_reel.py"), "face6.mp4", "-o", "reel.mp4", "--only", "Question Marks", "--only", "Lost",
                         "--only", "Stone", "--seconds", "1"], timeout=1800)
    expect_file("effects_reel", "reel.mp4")
    run("transitions", [PY, str(fx / "transitions.py"), "cut.mp4", "fx.mp4", "talk.mp4", "-o", "joined.mp4",
                        "--transition", "Whip Pan", "--transition", "Dip to Black"])
    expect_file("transitions", "joined.mp4")
    run("audio_fx", [PY, str(fx / "audio_fx.py"), "talk.mp4", "-o", "audio.mp4", "--effect", "Dialogue Clarity", "--effect", "Telephone@1-3",
                     "--effect", "Dialogue Level"])
    expect_file("audio_fx", "audio.mp4")
    for name in ("fx.mp4", "joined.mp4", "captioned.mp4"):
        print(name, probe(name))

    # 4. motion graphics in the Remotion workspace made by bootstrap
    ws = Path(json.loads((VS / "setup.json").read_text())["workspace"]) if (VS / "setup.json").exists() else Path.home() / "video-studio"
    npx = shutil.which("npx") or str(VS / "node" / ("npx.cmd" if WIN else "bin/npx"))
    run("remotion still KineticTitle", [npx, "remotion", "still", "src/index.ts", "KineticTitle", str(OUT / "title.png"), "--frame=45"],
        cwd=ws, timeout=1200, shell=WIN)
    expect_file("remotion still", OUT / "title.png")
    run("remotion still PresetCaptions", [npx, "remotion", "still", "src/index.ts", "PresetCaptions", str(OUT / "captions.png"), "--frame=12",
                                          "--props={\"preset\":\"submagic\",\"wordsUrl\":\"words.json\"}"], cwd=ws, timeout=1200, shell=WIN)
    expect_file("remotion PresetCaptions", OUT / "captions.png")
    run("remotion render LowerThird (alpha)", [npx, "remotion", "render", "src/index.ts", "LowerThird", str(OUT / "lower.mov"), "--codec=prores",
                                               "--prores-profile=4444", "--pixel-format=yuva444p10le", "--image-format=png", "--frames=0-29"],
        cwd=ws, timeout=1200, shell=WIN)
    expect_file("remotion LowerThird", OUT / "lower.mov")

    # 5. mark setup done; hook goes quiet
    run("doctor --mark-done", [node, str(PLUGIN / "scripts" / "doctor.mjs"), "--mark-done", "--fish=skipped"])
    summary()
    print("ALL PASSED")


if __name__ == "__main__":
    main()
