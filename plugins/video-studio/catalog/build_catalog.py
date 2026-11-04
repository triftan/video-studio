#!/usr/bin/env python3
"""Rebuild catalog/index.html from the plugin's style files and template catalog.

Usage: python3 catalog/build_catalog.py [--artifact OUT.html]
  --artifact also writes a copy without the <!doctype>/<head> wrapper, for publishing as a claude.ai artifact.
Images in catalog/img/ and videos in catalog/video/ are referenced by relative path.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)


def st(f):
    return json.load(open(os.path.join(P, "styles", f), encoding="utf-8"))


CORE = [
    dict(id="KineticTitle", category="Titles", overlay=False, seconds=3, desc="Word-by-word title that springs up out of a blur; the last word takes the accent color. Hooks and section titles.", props={"text": "Make every frame count", "accent": "#FF4D2E", "background": "#0B0B0F"}),
    dict(id="EditorialReveal", category="Titles", overlay=False, seconds=4, desc="Serif headline with a mask-wipe reveal, uppercase kicker and an underline that draws on. Premium, editorial tone.", props={"kicker": "Chapter one", "headline": "The quiet art of the cut", "accent": "#C8A96A", "background": "#F4F1EA"}),
    dict(id="NeonPulse", category="Titles", overlay=False, seconds=3, desc="Glowing uppercase text on a dark glass card with a breathing pulse and scanline sweep. Tech, gaming, nightlife.", props={"text": "Level up your edits", "glow": "#4DFFDF"}),
    dict(id="LowerThird", category="Lower thirds", overlay=True, seconds=5, desc="Accent bar grows, name slides in, role follows; reverses on exit. Interviews and podcasts.", props={"name": "Alex Rivera", "role": "Founder, Northwind", "accent": "#3D7BFF"}),
    dict(id="BarChart", category="Data", overlay=False, seconds=4, desc="Horizontal bars grow in sequence while numbers count up; highlight the max or the min bar.", props={"title": "Watch time after editing", "unit": "%", "bars": [{"label": "Raw", "value": 31}, {"label": "Cut silences", "value": 52}], "accent": "#3D7BFF", "highlight": "max"}),
    dict(id="LogoReveal", category="Promo", overlay=False, seconds=3, desc="Logo or wordmark scales in with a light sweep, then the tagline rises. Takes a logo image via logoSrc.", props={"brand": "NORTHWIND", "tagline": "Built for creators", "accent": "#FF4D2E"}),
    dict(id="PresetCaptions", category="Captions", overlay=True, seconds=3.5, desc="Word-highlight captions styled by any of the 32 caption presets, timed from words.json. Transparent.", props={"preset": "tiktok", "wordsUrl": "words.json"}),
    dict(id="Explainer", category="Explainers", overlay=False, seconds=0, desc="Renders a whole storyboard (title, bullets, steps, stat, chart, quote, image, CTA) in a design style; length follows the storyboard.", props={"storyboardUrl": "storyboard.json"}),
]


def effect_needs():
    """What each effect tracks, read from the effect engine's source (no imports needed)."""
    import re
    src = open(os.path.join(P, "skills", "video-effects", "scripts", "fxlib.py"), encoding="utf-8").read()
    bodies = {m.group(1): m.group(2) for m in re.finditer(r"^def (\w+)\(.*?\):\n(.*?)(?=^def |^[A-Z_]+ = |\Z)", src, re.S | re.M)}
    table = dict(re.findall(r'"([^"]+)": (fx_\w+)', src[src.index("EFFECTS = {"):]))
    out = {}
    for name, fn in table.items():
        body = bodies.get(fn, "") + (bodies.get("eye_beams", "") if "eye_beams" in bodies.get(fn, "") else "")
        needs = [k for k, toks in (("face", ("c.face",)), ("hands", ("c.hands",)), ("pose", ("c.pose",)), ("seg", ("c.cat", "c.person"))) if any(t in body for t in toks)]
        out[name] = needs
    return out


def build_data():
    lib = json.load(open(os.path.join(P, "skills", "motion-graphics", "templates", "src", "library", "catalog.json"), encoding="utf-8"))["templates"]
    core = [dict(c, core=True) for c in CORE]
    lib = [{k: v for k, v in dict(c, core=False).items() if k != "file"} for c in lib]
    needs = effect_needs()
    eff = [{"name": e["name"], "category": e.get("category"), "description": e.get("description"), "params": len(e.get("properties") or []), "needs": needs.get(e["name"], [])}
           for e in st("pixel-effects.json")["effects"]]
    tr = [{"name": t["name"], "description": t.get("description") or ""} for t in st("transitions.json")["transitions"]]
    au = st("audio-effects.json")
    aud = {"effects": [{"name": e["name"], "description": e.get("description") or "", "params": len(e.get("properties") or [])} for e in au["effects"]],
           "transitions": [{"name": e["name"], "description": e.get("description") or ""} for e in au["transitions"]]}
    keys = ["temperature", "tint", "saturation", "richness", "contrast", "fade", "bleachBypass", "splitEnabled", "splitHue", "splitAmount",
            "grainEnabled", "grainAmount", "vignetteEnabled", "vignetteAmount", "flickerEnabled", "damageEnabled", "filmGateEnabled"]
    grades = {k: {x: v.get(x) for x in keys} for k, v in st("color-presets.json")["presets"].items()}
    return dict(templates=core + lib, captions=st("caption-presets.json")["presets"], designStyles=st("design-styles.json")["styles"],
                grades=grades, zoom=st("zoom-presets.json")["presets"], transitions=tr, effects=eff, audio=aud, voices=st("voices.json")["voices"], kits=st("style-kits.json")["kits"])


def main():
    page = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    data = "window.CATALOG=" + json.dumps(build_data(), ensure_ascii=False, separators=(",", ":")) + ";"
    body = page.replace("/*__DATA__*/", data)
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n'
            + body + "\n</body>\n</html>\n")
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(full)
    print("wrote", os.path.join(HERE, "index.html"))
    if "--artifact" in sys.argv:
        out = sys.argv[sys.argv.index("--artifact") + 1]
        open(out, "w", encoding="utf-8").write(body)
        print("wrote", out)


if __name__ == "__main__":
    main()
