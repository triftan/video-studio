---
name: style-advisor
description: Help someone choose a look when they don't know which style, captions, effects, transitions, grade or voice to use. Asks a few plain questions (or reads their script or footage), recommends a matching style kit, and renders preview frames of two or three options to pick from. Use when the user is unsure, says "you choose", "make it look good", "what style should I use", or gives a video request with no style.
---

# Style advisor

Most people can't name a caption preset or a design style, but they know what they like when they see it. Your job: turn a vague idea into one coherent look, show it, and let them pick.

All styles live in the plugin's `styles/` folder (two folders up from this skill's base directory). Start from `styles/style-kits.json`: nine ready-made looks that already combine a design style, caption preset, templates, transitions, zoom, effects, color grade, voice and music direction.

## 1. Understand the video (ask at most three questions)

If the request or their files already answer something, don't ask it. Otherwise ask, in one message, with example answers they can tap or copy:

1. **What's it about, and who's watching?** (e.g. "photosynthesis for my biology class", "my bakery's new menu for Instagram")
2. **Where will it be posted?** TikTok / Reels / Shorts (9:16), YouTube (16:9), class or presentation (16:9), Instagram feed (4:5)
3. **How should it feel?** Pick one or two: calm · fun · energetic · professional · elegant · serious · techy · cozy

If they say "you choose" or "I don't know", infer from the topic and platform and say what you assumed. If they share a script or footage, read it: a talking-head clip points to `talking-head-pro`, a list of numbers to `business-report`, a product URL to `promo-ad` or `tech-product`.

## 2. Pick candidates

Score each kit in `style-kits.json` against their answers: `bestFor` (topic and format), `vibe` (feeling) and `platforms`. Choose:
- **Option A**: the best match.
- **Option B**: a clearly different but still suitable alternative (calmer or bolder, light or dark), so the choice is meaningful.
- **Option C** (optional): only when the brief is truly open.

Respect the kit's `avoid` note. For a school or kids audience, never pick effects that mock how someone looks (Ape Face, Big Mouth Monkey, Gaunt and similar) unless the student asks for them on their own footage.

## 3. Show, don't describe

Render one preview frame per option with the `StylePreview` composition in their Remotion workspace (default `~/video-studio`; the path is in `~/.video-studio/setup.json`). Use their real topic as the title and a real line from their script as the caption:

```bash
cd ~/video-studio
npx remotion still src/index.ts StylePreview out/option-a.png --frame=40 \
  --props='{"style":"edu-chalk","captionPreset":"plain","title":"The water cycle","subtitle":"How rain gets back to the sky","caption":"Water never really disappears, it just moves","tag":"Option A · Friendly lesson"}'
```

Use `StylePreviewVertical` for 9:16. Then show or open the images. If the workspace isn't set up, describe the options and suggest `/video-studio:setup`, or point them to the matching cards in the catalog (`/video-studio:catalog`).

Under each preview, give a short plain-language card:

> **Option A · Friendly lesson.** Chalkboard green with hand-drawn titles, simple white captions, gentle dissolves, a calm male narrator (Fish voice Ethan). Best for: explaining step by step without distractions.

Mention one or two templates they'll see (e.g. "a checklist that ticks off each step") and skip technical keys unless they ask.

## 4. Let them mix and match

Ask which they prefer, and offer simple tweaks in everyday words:
- "Bigger, bolder captions" → `yellow-impact` or `tiktok`; "more subtle" → `netflix` or `plain`
- "More energy" → faster pacing, `Whip Pan` / `Flash` transitions, `instant` zoom
- "More cinematic" → `editorial` or `warm-story`, `Dip to Black`, a grade such as `70s` or `TX3200`
- "Different voice" → another Fish voice from `styles/voices.json` (play the `sample_audio` from `search_voices` if they want to hear it)

Re-render a preview after a big change, not after every small one.

## 5. Lock it in and hand off

Write the choice to `style-choice.json` in their project folder so later steps stay consistent:

```json
{ "kit": "school-lesson", "designStyle": "edu-chalk", "captionPreset": "plain", "templates": ["ChapterCard", "Checklist", "Callout"],
  "transitions": ["Cross Dissolve"], "zoom": "slow-push", "grade": null, "voice": "fish:536d3a5e000945adb7038665781a4aca", "format": "16:9" }
```

Then continue with the right skill: `explainer-videos` for script-driven videos, `video-editing` for footage, `motion-graphics` for individual graphics. Those skills should read `style-choice.json` when it exists.

## Teaching moment (optional, one line)

When it helps, add one sentence on *why* the look fits, e.g. "Calm captions keep attention on the diagram, which matters more than flashiness in a lesson." Students learn design by hearing the reason.
