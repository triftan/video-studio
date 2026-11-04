---
name: setup
description: One-time setup for the video-studio plugin on this computer. Checks ffmpeg, Node and Python, prepares the Remotion workspace, connects the Fish Audio voiceover connector and opens the style catalog. Use when the user runs /video-studio:setup, asks to set up or repair video-studio, or a video task fails because a tool is missing.
---

# video-studio setup

Get this computer ready in one pass, then never again. Talk to the user like a friendly teaching assistant: short steps, one thing at a time, and say what each step is for. Many users are students who have never used a terminal.

Paths: this skill lives in `skills/setup/` inside the plugin, so the **plugin root** is two folders up from this file's base directory. Below, `<plugin>` means that absolute path.

## 1. Check the machine

Run:

```bash
node "<plugin>/scripts/doctor.mjs"
```

It prints JSON with `checks` (each has `ok`, `required`, `detail`, `fix`) and `missing_required`. Show the user a short checklist (✓ / ✗) instead of the raw JSON.

For each failed **required** check, offer to run its `fix` command, and wait for a yes before installing anything. Notes:
- macOS without Homebrew: install it first from https://brew.sh (the user runs the one-line installer; it asks for their password).
- Windows: after `winget` installs ffmpeg or Python, the user must open a **new** terminal or restart Claude Code before the new commands are found.
- If an install needs `sudo` or an admin prompt, explain that the computer will ask for their password.

Python packages go into a private environment at `~/.video-studio/venv` (the doctor's `python-venv` check), so nothing touches the system Python and macOS/Linux "externally managed environment" errors don't happen. Create it with the `python-venv` fix, then install the effect libraries with the `video-effects` fix (MediaPipe, OpenCV, NumPy, Pillow; about 2 minutes). From then on, run every plugin Python script with the doctor's `python` path.

Optional checks:
- `faster-whisper`: recommended (accurate word timings for captions). Offer to install it.
- `kokoro`: a free offline voice for when Fish Audio credits run out. Offer it, and mention it downloads about 350 MB of model files on first use.

Re-run the doctor after fixes until `missing_required` only contains `remotion-workspace`.

## 2. Create the Remotion workspace

Motion graphics and explainers render in a small Node project. Ask where to put it and default to `~/video-studio` (the doctor's `workspace` value). Then:

1. Copy `<plugin>/skills/motion-graphics/templates/` into that folder (skip `node_modules` if present). If the folder exists and already has a `package.json`, ask before overwriting.
2. Run `npm install` there (about 1 to 2 minutes).
3. Record the location: `node "<plugin>/scripts/doctor.mjs" --workspace=<absolute path>`.
4. Prove rendering works by rendering one still:
   ```bash
   cd <workspace> && npx remotion still src/index.ts KineticTitle out/setup-check.png --frame=45
   ```
   The first run downloads a headless Chrome automatically. Open or show the PNG so the user sees it worked.

### Check the effects engine

Run `"<python>" "<plugin>/skills/video-effects/scripts/apply_effects.py" --list` (where `<python>` is the doctor's `python` value). It should list 83 effects. Tracking models (about 37 MB) download automatically the first time an effect needs them.

## 3. Connect Fish Audio (voiceovers)

The plugin ships the Fish Audio connector (`fish-audio`, `https://api.fish.audio/mcp`). It signs in with a Fish Audio account through the browser; no API key.

1. Check whether Fish Audio tools are available to you (tool names containing `fish-audio` or `fish_audio`, such as `get_credit_balance`). If they are, call `get_credit_balance` and go to step 4.
2. If not, ask the user to:
   - create a free account at https://fish.audio if they don't have one,
   - type `/mcp` in Claude Code, choose **fish-audio**, then **Authenticate**, and finish the sign-in in the browser,
   - come back and say "done".
   If `fish-audio` is missing from `/mcp`, they can add it with `claude mcp add --transport http fish-audio https://api.fish.audio/mcp` and restart Claude Code. In the Claude desktop or web app, it can be added under Settings → Connectors → Add custom connector with the same URL.
3. When they're back, call `get_credit_balance`. If the tools still aren't visible, Claude Code may need a restart; say so plainly.
4. Tell them their plan and credits in plain words: speech costs about 1 credit per character of script, so 1,000 credits is roughly a minute of narration. On the free plan each request is limited to 500 characters, which the explainer skill handles by voicing one scene at a time. Free plans are usually for non-commercial use; point them to Fish Audio's terms for anything they sell.
5. Offer one short test line (about 60 credits) with an official voice, e.g. Sarah (`933563129e564b19a115bedd57b7406a`): "Hi! Your video studio is ready." Download the returned URL into the workspace and tell them where it is.

If they don't want Fish Audio, that's fine: Kokoro (free, offline) or the user's own recorded voice works too. Note the choice.

## 4. Finish and open the catalog

1. Mark setup complete (this silences the reminder at the start of each session):
   ```bash
   node "<plugin>/scripts/doctor.mjs" --mark-done --fish=<connected|skipped>
   ```
2. Open the catalog in their browser:
   - macOS: `open "<plugin>/catalog/index.html"`
   - Windows: `start "" "<plugin>\catalog\index.html"`
   - Linux: `xdg-open "<plugin>/catalog/index.html"`
   If that fails, give them the full path to open by double-clicking.
3. Close with a short summary: what's installed, where the workspace is, how many Fish credits they have, and three starter prompts, for example:
   - "Cut the silences from ~/Desktop/talk.mp4 and add tiktok captions."
   - "Make a 30-second 9:16 explainer about the water cycle in the edu-chalk style, voiced by Fish voice Ethan."
   - "Add a NumberCounter showing 12,400 subscribers to the top right of my video."
   - "Add Laser Eyes from 0:03 to 0:06 and a slow push zoom at the end of ~/Desktop/talk.mp4."

Remind them they can reopen the catalog any time with `/video-studio:catalog`.

## Repair mode

If setup already ran (`setup_done: true` in the doctor output), only fix what the doctor reports as failing, then re-open the catalog if they want it. Never delete their workspace.
