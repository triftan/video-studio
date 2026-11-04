---
name: catalog
description: Open the video-studio style catalog (templates, caption presets, design styles, color grades, effects, transitions, voices and showcase videos), or answer "which styles/templates can I use". Use when the user runs /video-studio:catalog or asks what styles, templates, captions, voices or looks are available.
---

# video-studio catalog

The catalog is a single offline page at `<plugin>/catalog/index.html`, where `<plugin>` is two folders up from this skill's base directory. It shows every template with a preview frame and a copy-ready render command, all 32 caption presets rendered live, the 8 design styles, color grades, zooms, effects, transitions, voices and the three showcase videos.

1. Open it:
   - macOS: `open "<plugin>/catalog/index.html"`
   - Windows: `start "" "<plugin>\catalog\index.html"`
   - Linux: `xdg-open "<plugin>/catalog/index.html"`
   If opening fails (for example in a remote session), give the full file path to open by hand.
2. If the user asked a question ("which caption styles are good for TikTok?"), answer it directly from the data files instead of only pointing at the page:
   - templates: `<plugin>/skills/motion-graphics/templates/src/library/catalog.json` plus the core templates listed in `<plugin>/skills/motion-graphics/SKILL.md`
   - caption presets, design styles, grades, zooms, effects, transitions, audio, voices: `<plugin>/styles/*.json` (index in `<plugin>/styles/STYLES.md`)
   Quote the exact keys (e.g. `submagic`, `dark-tech`, `NumberCounter`) so they can use them in prompts.

If the style files change, rebuild the page with `python3 "<plugin>/catalog/build_catalog.py"`.
