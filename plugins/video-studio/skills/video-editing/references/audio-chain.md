# Audio chain

Full parameter ranges for each effect are in `../../../styles/audio-effects.json` (compressor, de-esser, dynamic EQ, gate, limiter, reverb, telephone and more).

## Dialogue (default order)

1. **High-pass** at 80 Hz (male) to 100 Hz (female) to remove rumble.
2. **De-noise:** `afftdn=nf=-25`. For heavy noise use an ML model (RNNoise `arnndn`, Adobe Podcast, ElevenLabs Voice Isolator). Keep the original so you can revert.
3. **Gate** (optional, gently): `agate=threshold=0.02:ratio=2:attack=5:release=150`.
4. **EQ:** small cut around 250 to 400 Hz if muddy. Gentle lift at 3 to 5 kHz for presence.
5. **Compress:** `acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=3`.
6. **De-ess:** `deesser=i=0.4`.
7. **Loudness:** `loudnorm=I=-14:TP=-1:LRA=11` (social) or `I=-16` (podcast or YouTube long form).

One-liner:

```bash
ffmpeg -i in.wav -af "highpass=f=90,afftdn=nf=-25,equalizer=f=300:t=q:w=1:g=-3,equalizer=f=4000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=3,deesser=i=0.4,loudnorm=I=-14:TP=-1:LRA=11" out.wav
```

## Music

- Under speech: duck 12 to 18 dB (sidechain, see the ffmpeg cookbook). Without speech: up to -16 LUFS integrated.
- Low-pass the music around 8 to 10 kHz under dense dialogue so speech sits on top.

## Crossfades at cuts

Use a 10 to 20 ms fade on every audio cut to prevent clicks. For audible crossfades between scenes, "constant power" sounds natural and "fade through silence" gives a clean break (see `audio-effects.json` transitions).

## Character effects

- **Phone / radio:** band-pass 300 to 3400 Hz plus mild saturation (the "Telephone" preset).
- **Hall / small room:** short reverb for flashbacks or emphasis. Keep it subtle.
- **Echo:** delay 250 to 400 ms with low feedback for a single dramatic word.
