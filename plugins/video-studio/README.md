# video-studio

A Claude Code plugin for making videos with an AI agent: edit real footage, add motion graphics, and produce narrated explainer videos. It comes with a one-time setup, Fish Audio voiceovers and an offline catalog of every style.

| Skill | What it does |
| --- | --- |
| `setup` | One-time setup: checks the computer, creates the Remotion workspace, connects Fish Audio, opens the catalog. Run `/video-studio:setup`. |
| `catalog` | Opens the style catalog, or answers "which styles can I use?". Run `/video-studio:catalog`. |
| `style-advisor` | For when you don't know what look to use: asks up to three questions, recommends a style kit and renders preview frames to pick from. Just say "help me pick a style". |
| `video-editing` | Edits footage with ffmpeg: cuts silences and filler words, punch-in zooms, audio cleanup, color, styled captions, exports for each platform. |
| `motion-graphics` | 24 Remotion templates: titles, lower thirds, checklists, counters, charts, countdowns, social overlays, callouts, app promos, end cards and preset-styled captions. |
| `video-effects` | Applies any of the 83 video effects, 6 zoom presets, 3 film grades or a LUT to time ranges of your own footage, joins clips with the 30 named transitions, and runs the 22 audio effects. Face, hand and body effects use on-device tracking. Also makes labelled effects reels. |
| `explainer-videos` | Script, storyboard, Fish Audio voiceover and scene-by-scene explainers in a design style. |

The plugin also bundles the **Fish Audio connector** (`https://api.fish.audio/mcp`), so voiceovers work after a one-time browser sign-in. No API key is needed.

## For students: get started

1. **Install the prerequisites** (once per computer). Setup checks these and tells you exactly what's missing:
   - [Claude Code](https://code.claude.com) with a Claude Pro or Max plan, or an API key
   - [Node.js](https://nodejs.org) 18 or newer (LTS)
   - [Python](https://www.python.org/downloads/) 3.9 or newer
   - ffmpeg: `brew install ffmpeg` (macOS), `winget install --id Gyan.FFmpeg -e` (Windows) or `sudo apt install ffmpeg` (Linux)
   - A free [Fish Audio](https://fish.audio) account for voiceovers
   - About 1 GB of disk space for the Remotion workspace, Python packages and tracking models
2. **Install the plugin** in Claude Code:
   ```
   /plugin marketplace add triftan/video-studio
   /plugin install video-studio@video-studio
   ```
3. **Restart Claude Code.** You'll get a reminder to run setup. Run:
   ```
   /video-studio:setup
   ```
   Setup takes about 5 to 10 minutes. It installs what's missing (asking first), creates a private Python environment in `~/.video-studio/venv` with the effect libraries, creates a workspace in `~/video-studio`, test-renders a frame, walks you through signing in to Fish Audio (`/mcp` → **fish-audio** → **Authenticate**) and opens the catalog. The reminder stops once setup is done.
4. **Ask for a video.** For example:
   - "Cut the silences from ~/Desktop/talk.mp4 and add tiktok captions."
   - "Make a 30-second 9:16 explainer about the water cycle in the edu-chalk style, voiced by Fish voice Ethan."
   - "Add a NumberCounter showing 12,400 subscribers to the top right of my video."
   - "Add Laser Eyes from 0:03 to 0:06 and give the whole video the AG200 film look."
   - Not sure what it should look like? "Help me pick a style for a video about my bakery."

### Credits and costs

- Fish Audio speech costs about 1 credit per character of script; 1,000 credits is roughly a minute of narration. The free plan has a monthly credit allowance and a 500-character limit per request, which the explainer skill works around by voicing one scene at a time. Free plans are generally for non-commercial use; check Fish Audio's terms before selling anything you make.
- Out of credits? Kokoro is a free offline voice that setup can install, or record your own voice.
- Rendering with ffmpeg and Remotion is free and runs on your computer. Remotion is free for individuals and small teams; larger companies need a [company license](https://www.remotion.dev/license).

## The catalog

`catalog/index.html` is an offline page listing every template (with preview frame and copy-ready render command), all 32 caption presets rendered live, the 8 design styles, color grades, zooms, effects, transitions, voices and four showcase videos (including all 83 effects on one clip). Open it with `/video-studio:catalog`. After editing anything in `styles/` or the template library, rebuild it with `python3 catalog/build_catalog.py`.

## Style library (`styles/`)

Full index: [`styles/STYLES.md`](styles/STYLES.md).

- 9 style kits: ready-made looks (friendly lesson, viral short, clean talking head, tech demo, brand story, documentary, business report, playful, promo ad)
- 32 caption presets (TikTok Pop, Submagic, Netflix, Gold Serif, Signal Flux, Bubble Pop and more)
- 8 design styles for explainers (palette, font pairing, style guide, matching caption preset)
- 3 film-emulation color grades plus a CC0 blue tint LUT
- 6 zoom presets, 30 transitions, 83 video effects, 22 audio effects, all applicable by name with the `video-effects` skill
- 43 voices: official Fish Audio voices (default), ElevenLabs voice-library IDs and Volcano Engine speakers

Some caption presets use fonts that aren't on Google Fonts (Xinqingnian Ti, HarmonyOS Sans, Qingsong Shouxie Ti). The renderer substitutes a similar Google font automatically.

## How setup state works

- `scripts/doctor.mjs` checks the computer and prints a JSON report. `--workspace=<path>` records the workspace, and `--mark-done` records that setup finished.
- State lives in `~/.video-studio/setup.json`. Delete it to see the setup reminder again, or create an empty `~/.video-studio/skip` to silence it without running setup.
- `hooks/check-setup.mjs` runs at session start and only speaks up while setup is unfinished.
