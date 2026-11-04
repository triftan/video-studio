---
name: explainer-videos
description: Make explainer videos from an idea, script, product URL or document. Covers script writing, storyboarding, design style, AI voiceover, scene animation in Remotion, music, captions and final render. Use for product explainers, app promos, tutorials, educational animations, how-it-works videos and social explainers in 16:9 or 9:16.
---

# Explainer videos

An explainer turns one idea into a short, clear video: **script, then storyboard, then voice, then scenes, then polish**. The voiceover is the spine. Scenes are timed to it.

## 1. Brief (align first)

**Not sure which look to use?** If the user hasn't chosen a style, or says "you choose", use the `style-advisor` skill first. If a `style-choice.json` exists in their project folder, follow it.


Settle these before writing, proposing defaults where the user is vague:

- **Audience and goal:** who watches, and what they should know or do after.
- **Length:** 30 s (social), 60 to 90 s (product), 2 to 4 min (tutorial).
- **Format:** 16:9 or 9:16.
- **Design style:** pick from `../../styles/design-styles.json` (clean-saas, dark-tech, editorial, playful-pop, corporate-trust, warm-story, bold-creator, edu-chalk) or the user's brand.
- **Voice:** default to Fish Audio through the bundled `fish-audio` connector. Official picks are in `../../styles/voices.json` under `fish` (Sarah, Ethan, Adrian, Selene); `search_voices` finds more. Alternatives: ElevenLabs IDs (needs `ELEVENLABS_API_KEY`), Kokoro (free, offline) or the user's own recording.
- **Source material:** product URL, docs, screenshots, data. Only state facts the sources support. Never invent numbers, features, customers or quotes.

## 2. Script

Structure (see `references/script-and-storyboard.md` for templates):

1. **Hook** (0 to 5 s): the problem or a surprising fact.
2. **Problem** (why it matters).
3. **Solution** (what it is, in one sentence).
4. **How it works** (3 steps max).
5. **Proof** (a real stat, a demo or a testimonial, only if supported).
6. **Call to action.**

Rules: about 150 spoken words per minute. Short sentences. One idea per sentence. Write for the ear, not the eye. Read it aloud mentally. If a sentence needs a breath in the middle, split it.

## 3. Storyboard

Write `storyboard.json`, one entry per scene, each tied to a script line:

```json
{
  "style": "clean-saas",
  "format": "16:9",
  "voice": "fish:536d3a5e000945adb7038665781a4aca",
  "scenes": [
    { "id": "hook", "type": "title", "vo": "Editing a 10 minute video takes 4 hours.", "title": "4 hours", "subtitle": "to edit 10 minutes of footage" },
    { "id": "steps", "type": "steps", "vo": "Upload, describe the edit, review.", "items": ["Upload", "Describe the edit", "Review"] }
  ]
}
```

Scene types supported by the `Explainer` template: `title`, `bullets`, `steps`, `stat`, `quote`, `image`, `chart`, `cta`. Show the storyboard to the user before generating paid assets.

## 4. Voiceover and timing

Voice each scene separately: it gives exact timing per scene and stays under the free plan's 500-character limit.

**Fish Audio (default).** Use the `fish-audio` connector's tools:

1. Check credits first with `get_credit_balance`. Speech costs about 1 credit per character (UTF-8 byte). Add up the script, tell the user the total, and confirm before generating if it is more than about a third of their balance. `text_to_speech` with `dry_run: true` gives a free exact quote.
2. For each scene call `text_to_speech` with `voice_id` and the scene's `vo` text. The default model `s2.1-pro` is the steady narrator. For expressive reads use `model: "drama-3"` and tags such as `[excited]`, `[pause]` or `<emphasis>word</emphasis>`; keep tags out of on-screen captions.
3. Download each returned audio URL into the workspace: `curl -L -o public/vo/<scene-id>.mp3 "<url>"`.
4. A failed call is refunded, and an identical retry within 5 minutes is free, so retry once after a timeout. Never loop on paid calls.
5. If credits run out, say so and offer Kokoro (free, offline) for the remaining scenes, or ask the user to top up at https://fish.audio/go-premium/.

**Other voices.** ElevenLabs:
```bash
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE_ID/with-timestamps" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" \
  -d '{"text": "...", "model_id": "eleven_multilingual_v2"}' > scene.json
```
Kokoro (free, offline; `af_heart` is its most natural voice): see `../motion-graphics/templates/showcase/build_showcase.py` for a working example.

**Timing.**
1. Measure each clip with `ffprobe` and set the scene's `durationInFrames = ceil((voDuration + 0.8) * fps)` (0.35 s lead-in plus a short tail).
2. Reference the clip in the storyboard: `"audio": "vo/hook.mp3"` (files live in the workspace's `public/` folder).
3. For captions, transcribe each clip for word timings (`../video-editing/references/ffmpeg-cookbook.md`, "Transcribe"), then keep the timings but use the script's spelling. Speech recognition mishears brand names.

## 5. Build scenes

Use the Remotion workspace created by `/video-studio:setup` (default `~/video-studio`; the path is in `~/.video-studio/setup.json`). If setup hasn't run, suggest it, or copy `../motion-graphics/templates/` and run `npm install`. It has an `Explainer` composition that reads a storyboard and a design style and renders every scene type with consistent motion.

```bash
cd ~/video-studio
# put storyboard.json in public/, voice clips in public/vo/
npx remotion studio
npx remotion render src/index.ts Explainer out/explainer.mp4 --props='{"storyboardUrl":"storyboard.json"}'
```

For anything the template doesn't cover (custom diagrams, product UI animations, character scenes), write a new scene component following `../motion-graphics/references/animation-principles.md`, or generate footage:

- **AI video (Seedance, Kling, Veo) or AI images (gpt-image, Gemini, Flux):** good for B-roll and illustrations. Write prompts that match the design style's palette and mood. Generate one test first, then batch.
- **Screen recordings:** zoom into the active area, speed up waiting, add cursor highlights.

## 6. Polish

- **Music:** low-key, steady, ducked under the voice (see `../video-editing/references/audio-chain.md`).
- **Captions:** use the design style's `captionPreset` with `PresetCaptions` or `captions_to_ass.py`.
- **Sound design:** soft whooshes on transitions, a click on UI interactions, a riser before the reveal. Keep them subtle.
- **Loudness:** -14 LUFS for social, -16 for YouTube.

## 7. Verify

- Render stills at the midpoint of every scene and look at them: text fits, hierarchy is clear, style is consistent.
- Watch the whole thing once with sound. Does every visual match the line being spoken at that moment?
- Check facts against the sources once more.
- Report what was generated, what it cost, and anything unverified.

## Cost discipline

Paid generation (voice, video, images) adds up. Lock the script and storyboard first. Estimate the cost, and confirm with the user before large batches. Regenerate only with a specific fix in the prompt, not by rolling the dice.
