# Effects guide

Generated from the code (`scripts/fxlib.py`, `looks.py`, `transitions.py`, `audio_fx.py`). Names are case- and space-insensitive in every command.

**Needs** says what the effect tracks. `face`: one visible face (frames without a face are left untouched). `hands`: hands in view. `pose`: upper body. `seg`: person/hair/skin/clothes segmentation. `-`: works on any footage, including screen recordings.

| # | Effect | Category | Needs | Good length | What it does |
| --- | --- | --- | --- | --- | --- |
| 1 | AI Portrait Matte | mask | seg | any | Extracts a portrait as transparency using a cached AI matte. |
| 2 | AI Smart Object Matte | mask | seg | any | Select objects in the preview and track their alpha matte. |
| 3 | Ape Face | effect | face | 1.5-3 s | A broad muzzle with plump lips and nose plus visibly enlarged eyes |
| 4 | ASCII Rain | effect | - | any | Blue glowing ASCII characters rain down over the bright areas of the video. |
| 5 | Awkward | effect | face | 1.5-3 s | A cartoon pear-shaped face with a stretched rubber mouth, tall worried eyes and tiny sweat drops |
| 6 | Big Head | zoom | face | 2-4 s | Enlarge the head with a continuous face-following warp that smoothly deforms nearby background pixels. |
| 7 | Big Mouth Monkey | effect | face | 1.5-3 s | An oversized rubbery mouth and round magnified eyes follow the face and preserve speech motion |
| 8 | Brain Confusion | effect | face | 1.5-3 s | A hand-drawn thought bubble with changing tangled lines follows the face |
| 9 | Canon Log3 to Canon 709 | lut | - | whole clip | Canon Cinema Gamut / Canon Log 3 to Canon 709 |
| 10 | Circle Mask | effect | face | 1.5-3 s | Masks the layer with a soft-edged circle, with adjustable center, radius, feathering, and invert. |
| 11 | Color Wheels | effect | - | any | Balance shadows, midtones, and highlights with Lift, Gamma, and Gain color wheels. |
| 12 | Cool Red Eye | effect | face | 1.5-3 s | A red-white eye glint with a long red lens flare attached to one eye |
| 13 | CRT Retro | effect | - | any | Simulates a retro CRT tube monitor with scanlines, screen curvature, RGB shift, noise, and vignette. |
| 14 | Custom Curves | effect | - | any | Shape RGB and luminance, or selectively adjust hue, saturation and luminance with editable hue curves. |
| 15 | Dome Magnifier | effect | - | any | Magnifies a circular region with a smooth dome-shaped lens distortion and no visible border. |
| 16 | Doubt | effect | face | 1.5-3 s | Two flat angular question marks attach to the head in 3D and project with its pose |
| 17 | Loading… | effect | face | 1.5-3 s | A grey loading spinner follows a forehead attachment while remaining a screen-facing circle |
| 18 | Face Laser Eyes | effect | face | 1.5-3 s | Laser beams attached to source face landmarks |
| 19 | Face Tracking Zoom | zoom | face | 2-4 s | Timeline zoom animation focused on detected faces |
| 20 | autothreshold | effect | - | any | Automatically threshold moving pictures |
| 21 | c0rners | effect | - | any | Four corners geometry engine |
| 22 | Camera Shake Ultimate | effect | - | any | Camera movement effect with rotation, opacity, and blur. |
| 23 | Cartoon | effect | - | any | Cartoonify video, do a form of edge detect |
| 24 | Color Distance | effect | - | any | Calculates the distance between the selected color and the current pixel and uses that value as new pixel value |
| 25 | colorhalftone | effect | - | any | Filters image to resemble a halftone print in which tones are represented as variable sized dots |
| 26 | Defish0r | effect | - | any | Non rectilinear lens mappings |
| 27 | dither | effect | - | any | Dithers the image and reduces the number of available colors |
| 28 | Edgeglow | effect | - | any | Edgeglow filter |
| 29 | Elastic scale filter | effect | - | any | This is a frei0r filter which allows one to scale video footage non-linearly. |
| 30 | emboss | effect | - | any | Creates embossed relief image of source image |
| 31 | Flippo | effect | - | any | Flipping in x and y axis |
| 32 | Glow | effect | - | any | Creates a Glamorous Glow |
| 33 | heatmap0r | effect | - | any | Performs a continuous trichromatic tinting |
| 34 | Lens Correction | effect | - | any | Allows compensation of lens distortion |
| 35 | LetterB0xed | effect | - | any | Adds Black Borders at top and bottom for Cinema Look |
| 36 | NDVI filter | effect | - | any | This filter creates a false image from a visible + infrared source. |
| 37 | nosync0r | effect | - | any | broken tv |
| 38 | Perspective | effect | - | any | Distorts the image for a pseudo perspective |
| 39 | pixeliz0r | effect | - | any | Pixelize input image. |
| 40 | posterize | effect | - | any | Posterizes image by reducing the number of colors used in image |
| 41 | primaries | effect | - | any | Reduce image to primary colors |
| 42 | rgbsplit0r | effect | - | any | RGB splitting and shifting |
| 43 | scanline0r | effect | - | any | interlaced dark lines |
| 44 | Sharpness | effect | - | any | Unsharp masking |
| 45 | sigmoidaltransfer | effect | - | any | Desaturates image and creates a particular look that could be called Stamp, Newspaper or Photocopy |
| 46 | Sobel | effect | - | any | Sobel filter |
| 47 | softglow | effect | - | any | Does softglow effect on highlights |
| 48 | Squareblur | effect | - | any | Variable-size square blur |
| 49 | threelay0r | effect | - | any | dynamic 3 level thresholding |
| 50 | Threshold0r | effect | - | any | Thresholds a source image |
| 51 | Twolay0r | effect | - | any | dynamic thresholding |
| 52 | Gaunt | effect | face | 1.5-3 s | Two heavy blue comic stickers |
| 53 | Gaussian Blur | effect | - | any | Applies an adjustable Gaussian blur in all directions or along a chosen angle, with an opacity mix. |
| 54 | Graffiti Ghost | effect | face, seg | 1.5-3 s | A black portrait silhouette wears a glowing green razor-toothed grin, star eyes and head-attached horns |
| 55 | Hair Regions | effect | seg | any | Tint source hair segmentation regions |
| 56 | Hand Landmarks | effect | hands | any | Display source hand landmarks |
| 57 | Highlight | effect | face, seg | 1.5-3 s | A golden radial backdrop glows around the subject while a white hand-drawn outline traces the silhouette |
| 58 | Inspiration | effect | face | 1.5-3 s | A single gold-white electric burst flashes beside the head with a right-side glint and a brief dark atmosphere |
| 59 | Laser Eyes | effect | face | 1.5-3 s | Golden beams follow head direction, diverge outward from each eye and fill the eyelids |
| 60 | Lightning Eyes | effect | face | 1.5-3 s | Concentrated white-gold eye lights with a warm bloom and short flickering electric arcs around the eyes and temples |
| 61 | Linear Mask | effect | - | any | Masks the layer with a directional, piecewise-linear opacity gradient controlled by 2 to 8 stops. |
| 62 | Local Mosaic | effect | face | 1.5-3 s | Pixelates a rectangular region of the frame with adjustable position, size, block size, and feathered edges. |
| 63 | Lost | effect | face | 1.5-3 s | A black orbit with cyan, yellow and white 迷茫 lettering and colored stars revolves around the crown, following head pose with rear occlusion. |
| 64 | Black Overlay (Screen) | effect | - | any | Overlays black-background footage |
| 65 | LUT | lut | - | whole clip | Apply a LUT file |
| 66 | Magnifying Glass | effect | - | any | Adds a circular lens that magnifies the area at the chosen center point, ringed by a white border. |
| 67 | Mask | mask | face | any | Combine ordered timed masks and hand correction layers, then stroke the completed mask. |
| 68 | Person Focus | effect | face | 1.5-3 s | A soft circular spotlight follows the face while the surroundings darken |
| 69 | Person Regions | effect | seg | any | Tint source person segmentation regions |
| 70 | Body Landmarks | effect | pose | any | Display source body landmarks |
| 71 | Question Marks | effect | face | 1.5-3 s | Five yellow comic question marks pop in and wobble along a face-following arch |
| 72 | Rectangle Mask | effect | - | any | Masks the layer to a rounded rectangle with adjustable size, corner radius, and feathered edges. |
| 73 | Red Hot Face | effect | face | 1.5-3 s | A continuously enlarged head turns hot red within the tracked face contour |
| 74 | Sad | effect | face, seg | 1.5-3 s | Two long blue cartoon tear streams fall below the eyes while outlined Chinese comic words scroll behind the subject |
| 75 | Camera Shake | effect | - | any | Adds handheld camera motion with fbm-noise jitter, rotation, zoom, and a subtle breathing pulse. |
| 76 | Gloomy | effect | face | 1.5-3 s | Purple dizzy spiral clouds float above the head and follow it |
| 77 | Sony S-Log3 s709 | lut | - | whole clip | Sony S-Log3 / S-Gamut3.Cine to Rec.709 |
| 78 | Stone | effect | face, seg | 1.5-3 s | The subject petrifies into grayscale stone with a broad open zigzag crack while the background keeps its color |
| 79 | Surprise | effect | face | 1.5-3 s | Two golden comic exclamation marks attach beside the temples and follow head pose |
| 80 | Really Thanks | effect | face | 1.5-3 s | An exaggerated wide low mouth, swollen cheeks and chin, lifted worried upper face, and a large glossy blue sweat drop anchored to the forehead |
| 81 | Tilt-Shift | effect | - | any | Simulates a miniature/tilt-shift lens with a focused band, falloff blur, boosted saturation, and vignette. |
| 82 | Is Something Wrong | effect | face | 1.5-3 s | A helpless worried face with sloping brows, pinched outer eyes, a small forced smile, fuller cheeks and chin, and six translucent beads attached across the top of the head |
| 83 | Zoom | zoom | - | 2-4 s | Timeline zoom animation |

## Zoom presets (`--zoom`)

- `slow-push`: Move in at a constant speed across the effect interval. (1.4x)
- `slow-pull`: Move out at a constant speed across the effect interval. (1.4x)
- `instant`: Immediately magnify the picture without an animated transition. (1.4x)
- `quick-in`: Quick spring zoom in with speed-dependent motion blur. (1.4x)
- `quick-out`: Quick spring zoom out with speed-dependent motion blur. (1.4x)
- `in-out`: Spring zoom in, hold, then zoom out; adjust each movement independently. (1.4x)

## Color grades (`--grade`, `--lut`)

- `70s`, `AG200`, `TX3200`: film-emulation grades applied from their stored curves, HSL shifts and grain.
- `--lut path.cube`: any 3D LUT, e.g. `styles/luts/blue-tint.cube` or a camera's log-to-Rec.709 LUT.

## Transitions (`transitions.py`)

| Name | ffmpeg xfade |
| --- | --- |
| Anticipation Zoom | `zoomin` |
| Clean Line Wipe | `wipeleft` |
| Cross Dissolve | `fade` |
| Dip to Black | `fadeblack` |
| Flash | `fadewhite` |
| blend | `dissolve` |
| push-down | `slidedown` |
| push-left | `slideleft` |
| push-right | `slideright` |
| push-up | `slideup` |
| slide-down | `coverdown` |
| slide-left | `coverleft` |
| slide-right | `coverright` |
| slide-up | `coverup` |
| wipe-barn-door-h | `horzopen` |
| wipe-barn-door-v | `vertopen` |
| wipe-circle | `circleopen` |
| wipe-down | `wipedown` |
| wipe-left | `wipeleft` |
| wipe-rect | `rectcrop` |
| wipe-right | `wiperight` |
| wipe-up | `wipeup` |
| xfade0r | `fade` |
| Impact Shake | `squeezeh` |
| Luma Blend | `fadegrays` |
| Organic Light Dissolve | `dissolve` |
| Page Curl | `diagtl` |
| Rack Focus | `hblur` |
| Soft Wipe | `smoothleft` |
| Whip Pan | `hlwind` |

Audio crossfades: Constant Power, Constant Gain, Exponential Fade, Fade Through Silence.

## Audio effects (`audio_fx.py`)

| Name | ffmpeg chain |
| --- | --- |
| Chorus | `chorus=0.6:0.9:50|60:0.4|0.32:0.25|0.4:2|1.3` |
| Compressor | `acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=3` |
| De-esser | `deesser=i=0.5:m=0.5:f=0.5` |
| Delay / Echo | `aecho=0.8:0.75:320:0.35` |
| Dialogue Clarity | `highpass=f=90,afftdn=nf=-25,equalizer=f=300:t=q:w=1:g=-3,equalizer=f=3500:t=q:w=1:g=3` |
| Dialogue Level | `loudnorm=I=-16:TP=-1.5:LRA=11` |
| Saturation / Distortion | `volume=2.5,asoftclip=type=tanh,volume=0.6` |
| Dynamic EQ | `adynamicequalizer=dfrequency=6000:dqfactor=2:tfrequency=6000:tqfactor=2:threshold=20:ratio=3:mode=cut` |
| Equalizer | `equalizer=f=120:t=q:w=1:g=2,equalizer=f=400:t=q:w=1:g=-2,equalizer=f=4000:t=q:w=1:g=2` |
| Flanger | `flanger=delay=2:depth=3:regen=20:speed=0.4` |
| Gain | `volume=3dB` |
| Noise Gate | `agate=threshold=0.02:ratio=3:attack=5:release=120` |
| Hall | `aecho=0.8:0.85:60|120|180|260:0.4|0.3|0.22|0.15` |
| High-pass Filter | `highpass=f=120` |
| Limiter | `alimiter=limit=0.89:attack=5:release=50` |
| Low-pass Filter | `lowpass=f=4000` |
| Pan | `stereotools=balance_out=-0.4` |
| Phaser | `aphaser=type=t:speed=0.5:decay=0.5` |
| Reverb | `aecho=0.8:0.8:40|80|130:0.35|0.25|0.18` |
| Small Room | `aecho=0.8:0.6:15|28:0.25|0.15` |
| Subtle Echo | `aecho=0.8:0.5:250:0.15` |
| Telephone | `highpass=f=300,lowpass=f=3400,volume=2,asoftclip=type=atan,volume=0.7` |
