# Style library

Everything here is plain JSON, so any skill, script or tool can read it. Browse it visually in `catalog/index.html` (`/video-studio:catalog`).

## Caption presets (`caption-presets.json`)

| Key | Name | Font | Weight | Text | Active word | Box | Animated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `mg-kinetic-focus` | Kinetic Focus · MG (legacy) | Inter | 800 | `#ffffff` | `#ffffff` | - | - |
| `mg-editorial-reveal` | Editorial Reveal · MG (legacy) | Inter | 800 | `#ffffff` | `#ffffff` | - | - |
| `mg-neon-pulse` | Neon Pulse · MG (legacy) | Inter | 800 | `#ffffff` | `#ffffff` | - | - |
| `xin-qingnian` | Xin Qingnian (legacy) | Xinqingnian Ti | 800 | `#FFFFFF` | off | - | - |
| `serif-band` | Serif Band | Noto Serif SC | 500 | `#FFFFFF` | off | line box | - |
| `golden-band` | Golden Band (legacy) | Noto Sans SC | 300 | `#E7C982` | off | line box | - |
| `fresh-handwriting` | Sage Script | Qingsong Shouxie Ti Yi | 400 | `#FFF9EE` | off | line box | - |
| `orange-echo` | Orange Shadow | Noto Serif SC | 900 | `#FFB313` | off | - | - |
| `clean-heavy` | Heavy Sans | HarmonyOS Sans | 900 | `#F7F7F7` | off | - | - |
| `yellow-impact` | Yellow Outline | Xinqingnian Ti | 800 | `#FFE20A` | off | - | - |
| `white-impact` | White Outline | Xinqingnian Ti | 800 | `#FFFFFF` | off | - | - |
| `atelier` | Atelier Cut | Fraunces | 800 | `#24120A` | `#FFF1DA` on `#B64A3B` | highlight box + line box | yes |
| `bili` | Bili Clean | Noto Sans SC | 800 | `#F8FAFC` | `#07121F` on `#6EE7F9` | highlight box + line box | yes |
| `bubble-pop` | Bubble Pop | Bangers | 400 | `#FFFFFF` | `#FFEC1A` | - | yes |
| `luxe` | Gold Serif | Playfair Display | 800 | `#F8E8C6` | off | line box | - |
| `boyz-n-the-hood` | Boyz n the Hood | Bowlby One | 400 | `#FFFFFF` | `#FFF200` | - | yes |
| `dogme` | Dogme | Archivo Black | 900 | `#FCFCFA` | `#FCFCFA` | - | yes |
| `netflix` | Netflix | Roboto | 400 | `#ffffff` | `#ffffff` | - | yes |
| `noir` | Noir Glass | Cormorant Garamond | 700 | `#F5EFE3` | `#FFF8EA` on `#8E263B` | highlight box + line box | yes |
| `plain` | Plain | Inter | 400 | `#ffffff` | off | - | - |
| `persona` | Persona | Mulish | 900 | `#9C928A` | `#1F1B17` | line box | yes |
| `product` | Product Beam | Sora | 800 | `#F7FFF9` | `#071007` on `#A3FF12` | highlight box + line box | yes |
| `the-french-dispatch` | The French Dispatch | Newsreader | 500 | `#0F0F0F` | `#0F0F0F` on `#F6C239` | highlight box + line box | yes |
| `signal` | Signal Flux | Unbounded | 800 | `#EAFBFF` | `#061016` on `#4DFFDF` | highlight box + line box | yes |
| `off-the-wall` | Paper Stack | Bangers | 400 | `#000000` | off | highlight box + line box | - |
| `studio` | Studio Clean | Inter Tight | 800 | `#F8F7F2` | `#111111` on `rgba(255, 255, 255, 0.94)` | highlight box + line box | yes |
| `white-card` | White Card | Inter Tight | 800 | `#ABABAB` | `#040404` | line box | yes |
| `bold-outline` | Bold Outline (legacy) | Inter Tight | 800 | `#FFFFFF` | off | - | - |
| `deyi-card` | Deyi Card | Smiley Sans | 400 | `#FFFFFF` | off | line box | - |
| `story` | Story Yellow | DM Sans | 800 | `#FFFFFF` | `#FFD84A` on `rgba(255, 255, 255, 0)` | highlight box | yes |
| `submagic` | Submagic | Mulish | 800 | `#FFFFFF` | `#0A0A0A` on `#00E83C` | highlight box + line box | - |
| `tiktok` | TikTok Pop | Noto Sans SC | 900 | `#FFFDF7` | `#ffffff` on `#FF2E63` | highlight box | yes |

## Design styles (`design-styles.json`)

| Key | Name | Fonts | Accent | Captions | Feel |
| --- | --- | --- | --- | --- | --- |
| `clean-saas` | Clean SaaS | Inter / Inter | `#3D7BFF` | `studio` | Lots of white space, rounded 16px cards with soft shadows, UI screenshots in device frames. |
| `dark-tech` | Dark Tech | Unbounded / Inter | `#4DFFDF` | `signal` | Near-black backgrounds, glowing accent lines, grid textures at 4% opacity, monospace labels for numbers. |
| `editorial` | Editorial | Playfair Display / Inter | `#C8A96A` | `the-french-dispatch` | Magazine layout: serif headlines, small uppercase kickers with wide tracking, thin rules, photos with generous margins. |
| `playful-pop` | Playful Pop | Rubik / Rubik | `#FF4D8D` | `bubble-pop` | Chunky shapes, thick 4px outlines, flat colors, stickers and emoji-style icons. |
| `corporate-trust` | Corporate Trust | Montserrat / Open Sans | `#1360E2` | `white-card` | Navy and blue, clean icons, charts with clear labels and sources. |
| `warm-story` | Warm Story | Fraunces / Nunito | `#FF9F5A` | `orange-echo` | Documentary feel: warm grade, film grain, hand-drawn underlines, archival photos with slow Ken Burns. |
| `bold-creator` | Bold Creator | Anton / Inter | `#FFE100` | `yellow-impact` | Huge condensed uppercase type, yellow highlights, hard cuts, punch-in zooms on key words. |
| `edu-chalk` | Edu Chalk | Patrick Hand / Nunito | `#FFD166` | `plain` | Chalkboard teaching style: hand-drawn diagrams that draw on, arrows and circles for emphasis, step numbering. |

## Color grades (`color-presets.json`, `luts/`)

| Name | Temperature | Saturation | Richness | Grain | Vignette |
| --- | --- | --- | --- | --- | --- |
| 70s | 6500 K | 0.53 | 0.63 | 0.75 | - |
| AG200 | 6500 K | 1 | 0 | 0.55 | - |
| TX3200 | 6500 K | 0 | 0 | 0.75 | - |

`luts/blue-tint.cube`: cool blue tint (CC0, from Kdenlive).

## Zoom presets (`zoom-presets.json`)

- **Slow Push** (`slow-push`): Move in at a constant speed across the effect interval.
- **Slow Pull** (`slow-pull`): Move out at a constant speed across the effect interval.
- **Instant** (`instant`): Immediately magnify the picture without an animated transition.
- **Quick In** (`quick-in`): Quick spring zoom in with speed-dependent motion blur.
- **Quick Out** (`quick-out`): Quick spring zoom out with speed-dependent motion blur.
- **Zoom In + Out** (`in-out`): Spring zoom in, hold, then zoom out; adjust each movement independently.

## Transitions (`transitions.json`)

Anticipation Zoom, Clean Line Wipe, Cross Dissolve, Dip to Black, Flash, blend, push-down, push-left, push-right, push-up, slide-down, slide-left, slide-right, slide-up, wipe-barn-door-h, wipe-barn-door-v, wipe-circle, wipe-down, wipe-left, wipe-rect, wipe-right, wipe-up, xfade0r, Impact Shake, Luma Blend, Organic Light Dissolve, Page Curl, Rack Focus, Soft Wipe, Whip Pan

## Video effects (`pixel-effects.json`)

- **mask** (3): AI Portrait Matte, AI Smart Object Matte, Mask
- **effect** (74): Ape Face, ASCII Rain, Awkward, Big Mouth Monkey, Brain Confusion, Circle Mask, Color Wheels, Cool Red Eye, CRT Retro, Custom Curves, Dome Magnifier, Doubt, Loading…, Face Laser Eyes, autothreshold, c0rners, Camera Shake Ultimate, Cartoon, Color Distance, colorhalftone, Defish0r, dither, Edgeglow, Elastic scale filter, emboss, Flippo, Glow, heatmap0r, Lens Correction, LetterB0xed, NDVI filter, nosync0r, Perspective, pixeliz0r, posterize, primaries, rgbsplit0r, scanline0r, Sharpness, sigmoidaltransfer, Sobel, softglow, Squareblur, threelay0r, Threshold0r, Twolay0r, Gaunt, Gaussian Blur, Graffiti Ghost, Hair Regions, Hand Landmarks, Highlight, Inspiration, Laser Eyes, Lightning Eyes, Linear Mask, Local Mosaic, Lost, Black Overlay (Screen), Magnifying Glass, Person Focus, Person Regions, Body Landmarks, Question Marks, Rectangle Mask, Red Hot Face, Sad, Camera Shake, Gloomy, Stone, Surprise, Really Thanks, Tilt-Shift, Is Something Wrong
- **zoom** (3): Big Head, Face Tracking Zoom, Zoom
- **lut** (3): Canon Log3 to Canon 709, LUT, Sony S-Log3 s709

## Audio effects (`audio-effects.json`)

Chorus, Compressor, De-esser, Delay / Echo, Dialogue Clarity, Dialogue Level, Saturation / Distortion, Dynamic EQ, Equalizer, Flanger, Gain, Noise Gate, Hall, High-pass Filter, Limiter, Low-pass Filter, Pan, Phaser, Reverb, Small Room, Subtle Echo, Telephone

Crossfades: Constant Gain, Exponential Fade, Fade Through Silence, Constant Power

## Voices (`voices.json`)

Fish Audio (default, via the bundled connector; use `voiceId` with `text_to_speech`):

- **Sarah** (`933563129e564b19a115bedd57b7406a`): Soft, sincere young female narrator. Explainers, tutorials, calm social videos.
- **Ethan** (`536d3a5e000945adb7038665781a4aca`): Clear, calm, authoritative male narrator. Educational and documentary explainers.
- **Adrian** (`bf322df2096a46f18c579d0baa36f41d`): Deep, slow, dramatic male storyteller. Trailers, stories, cinematic intros.
- **Selene** (`b347db033a6549378b48d00acb0d06cd`): Calm, intimate female voice. Meditative, wellness and slow-paced content.

ElevenLabs (use `voiceId` with the ElevenLabs API):

- **Amelia**: Best for clear story reads, podcast intros, reels, and ads that need enthusiastic delivery. English-source accent: British.
- **Brittney**: Best for creator videos, celebrity/news recaps, hot-topic commentary, and how-to clips with a lively presenter feel. English-source accent: American.
- **Hope**: Best for crisp short-form narration, quick explainers, and social reads where clarity matters more than drama. English-source accent: American.
- **Jessica**: Best when a VO needs to feel composed and direct: narration, story reads, and confident product copy. English-source accent: American.
- **Arabella**: Best for fantasy, romance, wellness, and atmospheric stories that need mystery and feeling. English-source accent: American.
- **Jane**: Best for long-form book pacing, classic narration, and steady story delivery. English-source accent: British.
- **Maria**: Best for grandmother-style narration, gentle mature characters, and calm reflective story delivery. English-source accent: American.
- **Mark**: Best for dialogue, assistant-style replies, and informal scripts where back-and-forth flow matters more than announcer polish. English-source accent: American.
- **Frederick**: Best for history, science, mystery, and factual films that need a measured, well-spoken read. English-source accent: British.
- **Peter**: Best for trustworthy narration, explainers, and brand reads where reliability matters more than theatrical delivery. English-source accent: American.
- **James**: Best for controlled, direct reads with a heavier texture: audiobooks, story narration, and professional voiceover. English-source accent: American.
- **Jon**: Best for clear messaging, commercials, and narration where the speaker should feel anchored and trustworthy. English-source accent: American.
- **Sully**: Best for deep elderly narration, reflective storytelling, and warm authoritative reads with a seasoned feel. English-source accent: American.
- **David**: Best for deep old-male story narration, classic audiobook passages, and grounded dramatic reads. English-source accent: British.
- **Alex**: Best for YouTube, shorts, and entertainment clips that need pleasant presenter energy without sounding formal. English-source accent: American.

Doubao / Volcano Engine (Chinese and Japanese): Vivi, Xiaohe, Yunzhou, Xiaotian, Childlike · Masculine, Cherry Voice, Warm · Feminine, Thoughtful · Feminine, Dayi, Inspirational · Feminine, Smooth · Feminine, Yichen, Morgan, Qingcang, Gentle · Feminine, Grandmotherly · Feminine, Thoughtful · Masculine, Confident · Masculine, Cheerful · Masculine, Xiong Er, Silang, Straight-Talking Yingzi, Monkey King, Tang Seng.
