---
name: setup
description: One-time setup for the video-studio plugin on this computer. Automatically installs every missing dependency (Node.js, ffmpeg, Python packages, Remotion workspace) after one confirmation, connects the Fish Audio voiceover connector and opens the style catalog. Use when the user runs /video-studio:setup, asks to set up or repair video-studio, or a video task fails because a tool is missing.
---

# video-studio setup

Get this computer ready in one pass, then never again. Talk to the user like a friendly teaching assistant: short steps, one thing at a time, and say what each step is for. Many users are students who have never used a terminal.

Paths: this skill lives in `skills/setup/` inside the plugin, so the **plugin root** is two folders up from this file's base directory. Below, `<plugin>` means that absolute path.

## 1. Install every dependency (one confirmation)

Nothing else in the plugin works until this is done, so do it first, before any video request.

1. **Check.** Run the bootstrap in check mode. It needs only `sh` and `curl` (macOS/Linux) or PowerShell (Windows), so it works on a brand-new computer with no Node.js or Python:
   - macOS / Linux: `sh "<plugin>/scripts/bootstrap.sh"`
   - Windows: `powershell -ExecutionPolicy Bypass -File "<plugin>\scripts\bootstrap.ps1"`
   It prints ✓/✗ for Node.js, ffmpeg, the Python environment and the Remotion workspace. Exit 0 means all present: skip to step 2.
2. **Ask once.** Show the missing items as a short list in plain words, say it installs them in the user's home folder (about 5 to 10 minutes, roughly 1 GB), and ask a single question: "Shall I install these now?" Default the Remotion workspace to `~/video-studio`; mention they can choose another folder.
3. **Install everything in one go** after a yes. Run the same script with `--install` (Windows: `-Install`). Add `--workspace=<dir>` (Windows: `-Workspace <dir>`) if they chose another folder, and `--with-kokoro` (`-WithKokoro`) only if they want the free offline voice. If they chose another folder, record it afterwards with `node "<plugin>/scripts/doctor.mjs" --workspace=<absolute path>`. Use a generous timeout (15 minutes). Tell them what is happening while it runs ("Installing Node.js... ffmpeg... Python packages...").
4. **Exit code 2 = one manual step.** The script prints it. Usually it's Homebrew on a Mac without it (needs the Mac password, so the student pastes the printed command into the Terminal app), or a Windows prompt they need to click Yes on. Explain it simply, wait for "done", then run `--install` again. It skips anything already installed.
5. **Confirm.** Run the check again; everything should show ✓. If something still fails, read the script's output, fix that one item and rerun. Don't loop more than twice; tell the user what's left and how to get help.

Notes: a freshly installed Node.js is not on this session's PATH until Claude Code restarts. Until then call it by full path: `~/.video-studio/node/bin/node` and `~/.video-studio/node/bin/npx` (Windows: winget's Node is found after the script refreshes PATH, else restart). Node.js and ffmpeg (Linux) go into `~/.video-studio`, Python is managed by `uv` in `~/.video-studio/venv`, and the script adds those folders to the PATH for future sessions. Run every plugin Python script with the venv's Python (`~/.video-studio/venv/bin/python`; Windows `%USERPROFILE%\.video-studio\venv\Scripts\python.exe`).

## 2. Verify

1. Run `node "<plugin>/scripts/doctor.mjs"` (Node is installed now). Show a short ✓/✗ checklist instead of the raw JSON; `missing_required` should be empty.
2. Prove rendering works with one still:
   ```bash
   cd ~/video-studio && npx remotion still src/index.ts KineticTitle out/setup-check.png --frame=45
   ```
   The first run downloads a headless Chrome automatically. Show the PNG so they see it worked.
3. Check the effects engine: `"<venv python>" "<plugin>/skills/video-effects/scripts/apply_effects.py" --list` should list 83 effects. Tracking models (37 MB) download the first time an effect needs them.

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

If setup already ran (`setup_done: true` in the doctor output), rerun the bootstrap with `--install` to fix anything missing (it skips what is installed), then re-open the catalog if they want it. Never delete their workspace.
