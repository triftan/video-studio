# ffmpeg cookbook

Commands the editing skill relies on. Paths are examples.

## Probe

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels -of json in.mp4
```

## Transcribe (word timestamps)

Pick whichever is installed, in this order:

1. **whisper.cpp / faster-whisper** (local, free):
   ```bash
   pip install faster-whisper
   python -c "
   import json,sys
   from faster_whisper import WhisperModel
   m=WhisperModel('small', compute_type='int8')
   segs,_=m.transcribe(sys.argv[1], word_timestamps=True, vad_filter=True)
   words=[{'text':w.word.strip(),'start':round(w.start,3),'end':round(w.end,3)} for s in segs for w in s.words]
   json.dump(words,open('words.json','w'),indent=1)
   " in.mp4
   ```
2. **OpenAI Whisper API** or **ElevenLabs Scribe**: both return word timestamps. Normalize to `[{text,start,end}]`.

Extract audio first for speed: `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 audio.wav`.

## Find silences

```bash
ffmpeg -i in.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null - 2>&1 | grep silence_
```

`scripts/silence_edl.py` wraps this and writes `edl.json`.

## Frame-accurate trim

Re-encode for exact cuts (stream copy snaps to keyframes):

```bash
ffmpeg -ss 12.40 -to 31.85 -i in.mp4 -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k seg01.mp4
```

## Reframe 16:9 to 9:16

Center crop: `-vf "crop=ih*9/16:ih,scale=1080:1920"`.
Speaker off-center: shift crop x, e.g. `crop=ih*9/16:ih:iw*0.55-ih*9/32:0`.

## Punch-in zoom on a segment

Static 1.15x punch: `-vf "scale=iw*1.15:-2,crop=iw/1.15:ih/1.15"`.
Slow push over the clip (d = duration in s, fps 30):

```bash
-vf "zoompan=z='min(1+0.15*on/(30*d),1.15)':x='iw/2-(iw/zoom/2)':y='ih*0.37-(ih/zoom*0.37)':d=1:s=1920x1080:fps=30"
```

(Focal y 0.37 keeps eyes in frame, matching the slow-push preset.)

## Crossfade between two clips

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v][1:v]xfade=transition=fade:duration=0.4:offset=OFFSET[v];[0:a][1:a]acrossfade=d=0.4[a]" \
-map "[v]" -map "[a]" out.mp4
```

`OFFSET` = duration of a minus 0.4. Useful `xfade` transitions: `fade`, `fadeblack`, `wipeleft`, `slideleft`, `circleopen`, `radial`, `smoothleft`, `zoomin`.

## Burn captions

```bash
ffmpeg -i in.mp4 -vf "ass=captions.ass:fontsdir=./fonts" -c:a copy out.mp4
```

Download the preset's Google Font into `./fonts` first (e.g. Mulish, Inter, Noto Sans SC, Unbounded, Roboto).

## Music under speech (sidechain ducking)

```bash
ffmpeg -i voice.wav -i music.mp3 -filter_complex \
"[1:a]volume=0.5[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];[0:a][duck]amix=inputs=2:duration=first:normalize=0[a]" \
-map "[a]" mix.wav
```

## Loudness normalize

```bash
ffmpeg -i in.mp4 -af loudnorm=I=-14:TP=-1:LRA=11 -c:v copy out.mp4
```

## Apply a LUT or grade

```bash
ffmpeg -i in.mp4 -vf "lut3d=../../styles/luts/blue-tint.cube" out.mp4
```

See `color.md` for preset-to-filter recipes.

## Export presets

| Target | Command fragment |
| --- | --- |
| YouTube 1080p | `-c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart` |
| Reels / TikTok / Shorts | 1080x1920, 30 fps, same as above, keep under 60 s for Shorts |
| Preview | `-vf scale=-2:540 -crf 28 -preset veryfast` |
| Alpha overlay | `-c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le out.mov` |

## Grab frames to check your work

```bash
ffmpeg -ss 00:00:12.5 -i out.mp4 -frames:v 1 -q:v 3 check.jpg
ffmpeg -i out.mp4 -vf "fps=1/5,scale=480:-2,tile=4x3" contact.jpg   # contact sheet
```
