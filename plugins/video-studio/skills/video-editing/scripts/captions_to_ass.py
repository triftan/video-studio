#!/usr/bin/env python3
"""Turn word timestamps + a caption preset into a styled .ass subtitle file.

Usage:
  captions_to_ass.py words.json --preset tiktok -o captions.ass
      [--size 1080x1920] [--words-per-page 3] [--edl edl.json] [--y 0.72]

words.json: [{"text": "Hello", "start": 0.12, "end": 0.40}, ...]  (seconds, source time)
--edl remaps source times onto the edited timeline and drops words that were cut.
Presets come from styles/caption-presets.json. The active word gets the preset's
highlight color (or a highlight box), so it reads like animated social captions.
Burn in with: ffmpeg -i in.mp4 -vf "ass=captions.ass:fontsdir=fonts" out.mp4
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = os.path.join(HERE, "..", "..", "..", "styles", "caption-presets.json")


def ass_color(css, default="&H00FFFFFF"):
    """CSS hex/rgba -> ASS &HAABBGGRR (AA: 00 opaque, FF transparent)."""
    if not css:
        return default
    css = css.strip()
    m = re.match(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", css)
    if m:
        h = m.group(1)
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        r, g, b = h[0:2], h[2:4], h[4:6]
        return f"&H00{b}{g}{r}".upper()
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)", css)
    if m:
        r, g, b = (int(m.group(i)) for i in (1, 2, 3))
        alpha = float(m.group(4)) if m.group(4) else 1.0
        return f"&H{int(round((1 - alpha) * 255)):02X}{b:02X}{g:02X}{r:02X}"
    return default


def ts(t):
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def remap(words, edl):
    """Map source-time words onto the output timeline defined by an EDL."""
    out, offset = [], 0.0
    for seg in edl:
        for w in words:
            if w["start"] >= seg["in"] and w["end"] <= seg["out"] + 0.05:
                out.append({**w, "start": w["start"] - seg["in"] + offset,
                            "end": min(w["end"], seg["out"]) - seg["in"] + offset})
        offset += seg["out"] - seg["in"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("--preset", default="plain")
    ap.add_argument("--presets-file", default=PRESETS)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--words-per-page", type=int, default=None)
    ap.add_argument("--edl", default=None)
    ap.add_argument("--y", type=float, default=None, help="vertical center, 0-1 of height")
    ap.add_argument("-o", "--output", default="captions.ass")
    a = ap.parse_args()

    presets = json.load(open(a.presets_file))["presets"]
    if a.preset not in presets:
        raise SystemExit(f"unknown preset {a.preset}. Options: {', '.join(presets)}")
    p = presets[a.preset]
    w, h = (int(x) for x in a.size.lower().split("x"))
    vertical = h > w
    words = json.load(open(a.words))
    if a.edl:
        words = remap(words, json.load(open(a.edl)))

    font_px = round(p.get("fontSize", 0.05) * h * (1.0 if vertical else 1.15))
    per_page = a.words_per_page or p.get("wordsPerPage") or (3 if vertical else 6)
    upper = p.get("textTransform") == "uppercase"
    bold = -1 if int(str(p.get("fontWeight", "400"))[:3] or 400) >= 600 else 0
    primary = ass_color(p.get("color"))
    hi_color = ass_color(p.get("highlightColor") or p.get("color"))
    outline_c = ass_color(p.get("strokeColor"), "&H00000000")
    outline_w = round(p.get("strokeWidth", 0) * h / 1080, 1)
    shadow = 0 if p.get("textShadow") in (None, "none") else 2
    ls_raw = p.get("letterSpacing", 0) or 0
    # presets mostly use em (|x| <= 0.1); a few store small pixel values
    spacing = round(ls_raw * font_px if abs(ls_raw) <= 0.1 else ls_raw * h / 1080, 1)
    bg = p.get("normalBackground")
    hi_bg = p.get("highlightBackground")
    border_style = 3 if bg else 1  # 3 = opaque box behind the line
    back = ass_color(bg["color"]) if bg else "&H80000000"
    if bg:
        outline_c = back
        outline_w = max(4, round(bg.get("paddingY", 6) * h / 1080))
    y = a.y if a.y is not None else (0.72 if vertical else 0.86)
    margin_v = round(h * (1 - y))
    align = {"left": 1, "right": 3}.get(p.get("align"), 2)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{p.get('fontFamily', 'Inter')},{font_px},{primary},{hi_color},{outline_c},{back},{bold},0,0,0,100,100,{spacing},0,{border_style},{outline_w},{shadow},{align},{round(w * 0.08)},{round(w * 0.08)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    pages = [words[i:i + per_page] for i in range(0, len(words), per_page)]
    for page in pages:
        if not page:
            continue
        for k, cur in enumerate(page):
            start = cur["start"]
            end = page[k + 1]["start"] if k + 1 < len(page) else cur["end"] + 0.15
            parts = []
            for j, wd in enumerate(page):
                t = wd["text"].upper() if upper else wd["text"]
                t = t.replace("{", "(").replace("}", ")")
                if j == k:
                    if hi_bg:  # emulate a highlight box with a thick colored outline
                        box = ass_color(hi_bg["color"])
                        t = f"{{\\c{hi_color}\\3c{box}\\bord{max(6, round(font_px * 0.12))}\\fscx108\\fscy108}}{t}{{\\r}}"
                    else:
                        t = f"{{\\c{hi_color}\\fscx108\\fscy108}}{t}{{\\r}}"
                parts.append(t)
            pop = "{\\fad(60,0)}" if k == 0 else ""
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{pop}{' '.join(parts)}")

    with open(a.output, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")
    print(f"{len(words)} words, {len(pages)} pages, preset {a.preset} ({p.get('label')}), font "
          f"{p.get('fontFamily')} {font_px}px -> {a.output}")


if __name__ == "__main__":
    main()
