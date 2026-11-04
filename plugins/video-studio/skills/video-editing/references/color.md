# Color

Order of operations: **correct, match, then look**.

1. **Correct:** exposure and white balance per clip (`eq=brightness=..:contrast=..`, `colortemperature=temperature=5600`).
2. **Match:** make all shots of the same scene look alike before styling.
3. **Look:** one grade over the whole piece.

## Log footage

Convert log to Rec.709 before grading. Use the official camera LUTs from the manufacturer:

- Sony S-Log3: Sony "S-Log3 to s709" (free from Sony).
- Canon Log3: Canon "Canon Log3 to BT.709" (free from Canon).
- Nikon N-Log: Nikon "N-Log BT.2020 to Rec.709" (free from Nikon).

`ffmpeg -i in.mp4 -vf "lut3d=slog3_to_709.cube" out.mp4`

## Bundled looks

- `../../../styles/color-presets.json`: three film-emulation grades (**70s**, **AG200**, **TX3200**) described as parameters (temperature, saturation, richness, fade, split toning, grain, halation). Read the values and map them to filters (see below) or to your grading tool.
- `../../../styles/luts/blue-tint.cube`: a cool blue tint LUT (CC0, from Kdenlive).

Popular third-party creative LUTs (buy or download from the authors, not included here): Danny Gevirtz *Creative Filmmaking LUTs* (Clean, Vintage, Warm Nostalgia) and Daniel Schiffer *Sandfield Standard* (Moody, Greens).

## Mapping preset fields to ffmpeg

| Preset field | ffmpeg approach |
| --- | --- |
| `exposure` (stops) | `exposure=exposure=X` |
| `contrast` (1 = neutral) | `eq=contrast=X` |
| `saturation` (1 = neutral) | `eq=saturation=X` |
| `temperature` (K, 6500 = neutral) | `colortemperature=temperature=X` |
| `tint` | `colorbalance` green/magenta midtones |
| `fade` | `curves` lifting the black point, e.g. `curves=all='0/0.08 1/1'` |
| `split*` (split toning hue/amount) | `colorbalance=rs=..:bs=..:rh=..:bh=..` |
| `lift_*` / `gamma_*` / `gain_*` wheels | `colorbalance` shadows / midtones / highlights, or `lutrgb` |
| `rgbCurve`, `redCurve`... | `curves=r='..':g='..':b='..'` using the same control points |
| `hsl*` per-color tweaks | `huesaturation=colors=r:saturation=..` (ffmpeg 6+) |
| `grainAmount` / `grainSize` | `noise=alls=8:allf=t` (scale strength with amount) |
| `vignetteAmount` / `vignetteSize` | `vignette=PI/5` |
| `flicker*`, `damage*` (dust, scratches) | overlay a film-damage clip in `screen` blend mode |
| `filmGate*` | crop/pad to the gate ratio with soft rounded corners |
| bloom / halation (not in presets, common add) | `split[a][b];[b]gblur=sigma=12,colorchannelmixer=rr=1:gg=0.3:bb=0.2[g];[a][g]blend=all_mode=screen:all_opacity=0.25` |

Quick looks without a LUT:

- **Warm film:** `colortemperature=5200,eq=saturation=0.9:contrast=1.05,curves=all='0/0.05 1/0.97',noise=alls=6:allf=t`
- **Moody teal-orange:** `colorbalance=rs=-0.05:bs=0.08:rh=0.08:bh=-0.06,eq=saturation=0.85:contrast=1.1`
- **Bleach bypass:** `eq=saturation=0.45:contrast=1.25`
- **Black and white high contrast (TX3200 feel):** `hue=s=0,eq=contrast=1.3,noise=alls=12:allf=t`
