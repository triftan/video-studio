---
name: video-effects
description: Apply named effects, zooms, color grades, LUTs, transitions and audio effects to the user's own footage. Covers all 83 video effects (Laser Eyes, Big Head, Question Marks, Stone, Glow, CRT Retro, Tilt-Shift, Hand/Body Landmarks, Portrait Matte and more), 6 zoom presets, 3 film grades, 30 transitions and 22 audio effects. Use when the user asks to add an effect, filter, look, zoom, transition or audio effect by name or description, or to make an effects reel.
---

# Video effects

Everything in the catalog's effects, grades, zooms, transitions and audio sections can be applied with three scripts in `scripts/`. Names are case- and space-insensitive. The full list with what each effect needs is in `references/effects-guide.md`, or run `--list`.

Use the Python environment from `/video-studio:setup` (it installs `requirements.txt`: MediaPipe, OpenCV, NumPy, Pillow). Tracking models (about 37 MB) download once to `~/.video-studio/models`.

## Video effects, zooms, grades and LUTs: `apply_effects.py`

```bash
python scripts/apply_effects.py --list
python scripts/apply_effects.py talk.mp4 -o talk-fx.mp4 --fx "Laser Eyes@3-5.5"
python scripts/apply_effects.py talk.mp4 -o talk-fx.mp4 \
  --fx "Question Marks@8-10.5" --zoom "quick-in@12-15" --grade "AG200" --lut look.cube@0-end:0.6
```

- Range syntax: `NAME@START-END[:STRENGTH]` in seconds. `END` can be `end`. No `@` means the whole video. Strength 0 to 1 blends with the original.
- Several operations can overlap; they apply in the order given (put grades last).
- For many edits, write a plan file: `[{"type": "fx", "name": "Big Head", "start": 2, "end": 4}, {"type": "grade", "name": "70s"}]` and pass `--plan plan.json`.
- Original audio is kept. Frames outside every range are copied untouched. Inside a range, footage larger than 720p is processed at 720p and scaled back, which slightly softens just those frames.
- Tracking runs only where an effect needs it: `face`, `hands`, `pose` or `seg` (segmentation). If a face effect hits frames with no face (someone turns away, a cutaway), those frames are left unchanged and the script reports how many.

## Transitions between clips: `transitions.py`

```bash
python scripts/transitions.py --list
python scripts/transitions.py a.mp4 b.mp4 c.mp4 -o joined.mp4 --transition "Whip Pan" --transition "Cross Dissolve"
```

One `--transition` per join (the last repeats). Each name maps to the closest ffmpeg `xfade` look, and audio crossfades with `--audio-transition` (`Constant Power` by default). Clips are matched to the first clip's size and frame rate.

## Audio effects: `audio_fx.py`

```bash
python scripts/audio_fx.py --list
python scripts/audio_fx.py talk.mp4 -o talk-clean.mp4 --effect "Dialogue Clarity" --effect "Dialogue Level"
python scripts/audio_fx.py talk.mp4 -o phone.mp4 --effect "Telephone@4-7"
```

## Effects reel: `effects_reel.py`

`python scripts/effects_reel.py clip.mp4 -o reel.mp4 [--only "Laser Eyes" --only "Stone"] [--seconds 2] [--music bed.wav]` labels each effect with its number, name, category and description. The catalog's 83-effects video was made this way.

## Choosing effects (help the user decide)

If the user is vague ("make it fun", "something dramatic"), suggest two or three effects and preview them before rendering everything:
`python scripts/effects_reel.py their-clip.mp4 -o preview.mp4 --only "A" --only "B" --only "C" --seconds 2`

Good matches:
- **Reactions and comedy:** Question Marks, Doubt, Surprise, Big Head, Awkward, Brain Confusion, Lost, Sad, Red Hot Face
- **Hype and gaming:** Laser Eyes, Lightning Eyes, Cool Red Eye, Camera Shake, Inspiration, Glow, rgbsplit0r
- **Retro:** CRT Retro, scanline0r, nosync0r, dither, colorhalftone, posterize, plus the `70s` grade
- **Cinematic:** LetterB0xed, Tilt-Shift, softglow, Person Focus, the `TX3200` or `AG200` grades, slow-push zoom
- **Explaining and teaching:** Magnifying Glass, Dome Magnifier, Local Mosaic (hide details), Highlight, Hand Landmarks, Body Landmarks
- **Masks and compositing:** AI Portrait Matte, Circle/Rectangle/Linear Mask, Mask, Person Regions, Hair Regions

Respect the `style-choice.json` from the style advisor when there is one (e.g. no cartoon face effects in a corporate look).

## Good practice

- Face effects work best for 1.5 to 3 seconds, timed to a line or reaction in the transcript. Longer becomes tiring.
- Use effects sparingly: one or two per 30 seconds in talking-head videos.
- Don't apply effects that mock someone's appearance (Ape Face, Big Mouth Monkey, Gaunt and similar) to footage of other people without their consent.
- After rendering, extract a frame from the middle of each effect range and look at it before handing over the video.

## How these relate to the catalog

Effect names, categories and descriptions come from the plugin's style library (`styles/pixel-effects.json`). The rendering code is this plugin's own implementation. It follows each description closely, but the artwork and exact motion are not identical to any other editor's version of the same effect. "AI Smart Object Matte" selects clothing; point it at other objects by editing `fx_smart_object` in `scripts/fxlib.py`.
