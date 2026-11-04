---
name: video-editing
description: Edit real footage into a finished video with ffmpeg and a transcript. Use for talking-head, interview, podcast, tutorial and screen-recording edits, for cutting silences and filler words, tightening pacing, captions in a chosen style, punch-in zooms, transitions, audio cleanup, color grading and exporting for YouTube, Reels, TikTok or Shorts.
---

# Video editing

You are the editor. The user thinks in clips, moments and story. Turn their footage into the video they want, and show your work as an edit they can review.

The working loop is always the same: **inspect, align, edit, verify**.

## 1. Inspect before you touch anything

1. Probe every source: `ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate,channels -of json <file>`.
2. Transcribe speech with word timestamps (see `references/ffmpeg-cookbook.md`, "Transcribe"). Save `words.json` as `[{ "text", "start", "end" }]` in seconds. Every later step reads this file.
3. Skim the transcript for structure: hook, main points, retakes, dead air, the ending.
4. Write a short `edit-plan.md`: source files, target length, platform and aspect ratio, what gets cut and why.

Keep two clocks separate: **source time** is a position inside a file. **Timeline time** is a position in the output. Never mix them. Keep frame math exact (use the source fps; round once at the end).

## 2. Align only on what matters

**Not sure which look to use?** If the user hasn't chosen a style, or says "you choose", use the `style-advisor` skill first. If a `style-choice.json` exists in their project folder, follow it.


Ask about the choices that actually shape the result, and propose a default for each:

- Platform and aspect: 16:9 (YouTube), 9:16 (Reels, TikTok, Shorts), 1:1 or 4:5 (feed).
- Target length and pace: relaxed, standard or punchy.
- Caption style: offer 3 presets from `../../styles/caption-presets.json` that fit the tone (see "Choosing styles" below).
- Look: keep natural, or a grade from `../../styles/color-presets.json`.

Execute mechanical requests directly ("cut the first 5 seconds", "make captions yellow"). Do not interrogate the user about things they already told you.

## 3. Edit

Build the edit as data first, then render. Keep an `edl.json` (edit decision list) of kept segments:

```json
[{ "src": "a.mp4", "in": 12.40, "out": 31.85, "note": "hook" }]
```

Rendering from an EDL means every change is reversible and reviewable. Scripts in `scripts/`:

| Script | What it does |
| --- | --- |
| `scripts/silence_edl.py` | Detect silences with ffmpeg and write an EDL that keeps speech, with padding. |
| `scripts/render_edl.py` | Render an EDL to one file with frame-accurate cuts and short audio crossfades. |
| `scripts/captions_to_ass.py` | Turn `words.json` + a caption preset into a styled `.ass` subtitle file for burn-in. |

Editing craft (details in `references/editing-craft.md`):

- **Talking head:** cut retakes (keep the last clean take), filler words ("um", "uh", "you know") and pauses over ~0.6 s. Leave 80 to 150 ms of air around each cut so speech doesn't clip.
- **Hook first:** the first 3 seconds must say why to keep watching. Move the strongest line up if needed.
- **Hide jump cuts:** alternate punch-in zooms (1.0x to 1.15x to 1.0x) across cuts using `../../styles/zoom-presets.json`, or cover them with B-roll.
- **Pacing:** shorts change something on screen every 2 to 4 s (cut, zoom, caption page, B-roll). Long form can breathe.
- **Transitions:** default to hard cuts. Use `../../styles/transitions.json` sparingly (a dissolve for time passing, a whip pan or flash for energy).
- **Audio:** apply the dialogue chain in `references/audio-chain.md`: high-pass, de-noise, compress, de-ess, loudness to -14 LUFS for social or -16 for podcasts. Duck music 12 to 18 dB under speech.
- **Color:** match shots first, then apply one look. Presets in `../../styles/color-presets.json`. Recipes in `references/color.md`.

## 4. Verify like a viewer

After every structural change, check the result as someone watching it:

- **Did it do what was asked?** Length, tone, message.
- **Continuity:** no repeated or missing words, no black frames, no clipped syllables, no audio pops at cuts.
- **Dependent layers:** after cutting, re-time captions from the new EDL, make sure music still covers the full length, and check B-roll still lands on the right line.
- **Look at it:** extract frames at the cuts you changed (`ffmpeg -ss T -i out.mp4 -frames:v 1 check_T.jpg`) and view them. Listen to the boundaries if you can. Check only what changed; don't re-review the whole video each time.

Report honestly: what you did, what you checked, anything you couldn't verify.

## Choosing styles

The style library lives in `../../styles/` (index: `../../styles/STYLES.md`).

- **Captions:** `caption-presets.json` has 32 presets. Match tone:
  - Energetic social: `tiktok`, `submagic`, `bubble-pop`, `yellow-impact`, `story`
  - Clean or corporate: `plain`, `studio`, `clean-heavy`, `white-card`, `netflix`
  - Premium or editorial: `luxe`, `serif-band`, `atelier`, `the-french-dispatch`, `noir`
  - Tech: `signal`, `product`
  - Cinematic: `dogme`, `boyz-n-the-hood`, `persona`
  - Chinese-language content: `bili`, `deyi-card`, `xin-qingnian`

  Font sizes are fractions of frame height (0.05 on 1920 px tall = 96 px). For 9:16 use 1 to 3 words per page. For 16:9 use 4 to 8.
- **Zooms:** `zoom-presets.json` (slow push, slow pull, instant punch, and more).
- **Effects:** `pixel-effects.json` is a menu of 83 effect ideas with parameters (face zoom, tilt-shift, CRT, glow, laser eyes, letterbox). Rebuild them with ffmpeg filters or Remotion when needed.

## When to hand off

- Animated titles, lower thirds, charts, logo reveals or animated captions: use the `motion-graphics` skill.
- A video built mostly from script, voiceover and graphics: use the `explainer-videos` skill.

## Cost and retries

Generation APIs and long renders cost money and time. Render a low-res preview (`-vf scale=-2:540 -preset veryfast`) before the final export. When something fails, read the error and change one thing with a reason. Don't loop through guesses. If there's no path, stop, say what's left, and recommend a next step.
