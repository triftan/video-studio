# Animation principles for motion graphics

## Timing at 30 fps

| Action | Frames | Seconds |
| --- | --- | --- |
| Micro (word pop, icon bounce) | 4 to 8 | 0.13 to 0.27 |
| Element entrance | 8 to 15 | 0.27 to 0.5 |
| Full-screen title in | 12 to 24 | 0.4 to 0.8 |
| Exit | 6 to 12 | 0.2 to 0.4 |
| Stagger between siblings | 2 to 4 | 0.07 to 0.13 |
| Minimum readable hold | 45 | 1.5 |

Reading time: about 0.3 s per word plus 0.5 s. A 6-word title needs at least 2.3 s on screen.

## Easing

```ts
import { Easing, interpolate, spring } from "remotion";

// ease-out entrance (fast start, soft landing)
interpolate(frame, [0, 12], [0, 1], { easing: Easing.bezier(0.2, 0.8, 0.2, 1), extrapolateRight: "clamp" });

// ease-in exit
interpolate(frame, [end - 8, end], [1, 0], { easing: Easing.bezier(0.4, 0, 1, 1), extrapolateLeft: "clamp" });

// springy pop (overshoot)
spring({ frame, fps, config: { damping: 12, stiffness: 180, mass: 0.6 } });

// calm settle (no overshoot)
spring({ frame, fps, config: { damping: 200 } });
```

These easing curves also appear in the caption presets' `wordAnimation` blocks (e.g. `cubic-bezier(0.2, 0.8, 0.2, 1)` for TikTok-style word pops).

## Motion vocabulary

- **Pop:** scale 0.8 to 1.04 to 1.0, opacity 0 to 1 over 5 to 8 frames. Energetic captions, stickers.
- **Slide and fade:** translate 20 to 40 px plus opacity. Calm, corporate.
- **Mask wipe:** reveal with `clip-path: inset(0 X% 0 0)`. Editorial, premium.
- **Focus pull:** blur 8 px to 0 with opacity. Cinematic titles.
- **Draw on:** SVG `strokeDashoffset` from length to 0. Lines, underlines, icons, charts.
- **Count up:** interpolate the number and format it each frame. Stats.
- **Parallax:** background moves at 0.3x, foreground at 1x. Depth on still images.
- **Kinetic type:** one word at a time, size and weight varying with emphasis.

## Layout

- Grid with 5 to 8% outer margins. Align to edges and baselines, not to visual guesses.
- Max line length ~30 characters for titles (fewer in 9:16).
- Hierarchy through size (1.6 to 2x per level), weight, then color. Don't use all three at once.
- Contrast: text on footage needs a scrim, a box or a strong shadow. Test on the brightest frame.

## Color

- At most 1 accent color plus neutrals. Use the brand accent for the thing to look at.
- Dark backgrounds: avoid pure #000 (use #0B0B0F). Light backgrounds: avoid pure #FFF for large areas.

## Common mistakes

- Animating everything at once.
- Exits as slow as entrances (feels sluggish).
- Text that's readable on desktop but tiny on a phone.
- Non-deterministic code (random without a seed, Date.now(), CSS transitions) causing flicker between frames.
- Fonts not loaded before render: use `@remotion/google-fonts` or `staticFile` with `loadFont`.
