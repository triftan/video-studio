# Scripts and storyboards

## Word budgets (about 150 wpm)

| Length | Words | Scenes |
| --- | --- | --- |
| 15 s | 35 | 3 to 4 |
| 30 s | 75 | 5 to 7 |
| 60 s | 150 | 8 to 12 |
| 90 s | 225 | 12 to 16 |
| 3 min | 450 | 20 to 30 |

Scene length: 3 to 8 s. Longer scenes need movement inside them (a build, a zoom, a highlight).

## Script templates

**Product explainer (60 s)**
1. Hook: "[Audience] spend [real cost] on [painful task]."
2. Problem: why the old way fails (one concrete detail).
3. Solution: "[Product] [does X] so you can [outcome]."
4. How: three steps, verb first.
5. Proof: one real number or a customer line (only if sourced).
6. CTA: one action, with a URL on screen.

**Concept explainer (educational)**
1. Question the viewer already has.
2. Everyday analogy.
3. The real mechanism in 2 to 3 steps, with a diagram.
4. A common misconception, corrected.
5. One-sentence recap.

**App promo (30 s, 9:16)**
1. Hook on the outcome (show the result first).
2. Three fast feature beats, each a screen recording with a zoom.
3. Social proof or rating (if real).
4. CTA with app store badge.

**Tutorial**
1. What you'll make (show the result).
2. Steps, each: say it, show it, then the result.
3. Common mistake.
4. Recap plus next step.

## Writing for voice

- Contractions ("you'll", "it's") sound human.
- Numbers: write them how they're said ("four hours", "ninety percent").
- Avoid lists of more than 3 in one sentence.
- Put the key word at the end of the sentence. That's where emphasis lands.

## Storyboard schema

```json
{
  "style": "clean-saas",          // key in styles/design-styles.json, or an inline style object
  "format": "16:9",               // or "9:16"
  "fps": 30,
  "music": "music/bed.mp3",       // optional, in public/
  "scenes": [
    {
      "id": "hook",
      "type": "title",            // title | bullets | steps | stat | quote | image | chart | cta
      "vo": "spoken line",        // the script line for this scene
      "audio": "vo/hook.mp3",     // optional voice clip in public/
      "durationInFrames": 120,    // set from the voice length + ~0.4 s
      "title": "...", "subtitle": "...",
      "items": ["..."],           // bullets / steps
      "value": 81, "unit": "%", "label": "...",   // stat
      "quote": "...", "author": "...",            // quote
      "src": "img/shot.png",      // image (in public/)
      "bars": [{ "label": "...", "value": 10 }],  // chart
      "url": "example.com"        // cta
    }
  ]
}
```

## Visual rules per scene

- One message per scene. If you need "and", split it.
- Show the noun being said: product UI when naming a feature, a number when citing a stat.
- Keep a consistent layout grid across scenes. Change content, not structure.
- Transitions: a matching cut or a short push between related scenes; a dip or wipe between sections.
