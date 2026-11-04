# Showcase videos

Three example videos built from this template project. Every scene carries an on-screen label naming the template, design style and caption preset in use.

| Composition | Format | What it shows |
| --- | --- | --- |
| `ShowcaseAiVideoEditing` | 16:9, ~100 s | "AI video editing, explained": all 24 templates, a custom timeline-cut scene, captions and design styles |
| `ShowcaseCaptionStyles` | 9:16, ~35 s | Nine caption presets, one spoken line each |
| `ShowcaseDesignStyles` | 16:9, ~28 s | All eight design styles, each captioned in its own matching preset |

Charts marked "illustrative" use example numbers, not measured data.

## Rebuild

1. Voice, word timings and music (free and local: Kokoro TTS, faster-whisper, a synthesized pad):
   ```bash
   pip install kokoro-onnx soundfile faster-whisper numpy
   # download kokoro-v1.0.onnx and voices-v1.0.bin from
   # https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
   python showcase/build_showcase.py --kokoro-dir /path/to/kokoro-files
   ```
   This writes `public/showcase/` (git-ignored). Edit `showcase/script.json` to change the lines; scene lengths follow the voice.
2. Render:
   ```bash
   npx remotion render src/index.ts ShowcaseAiVideoEditing out/ai-video-editing.mp4
   npx remotion render src/index.ts ShowcaseCaptionStyles out/caption-styles.mp4
   npx remotion render src/index.ts ShowcaseDesignStyles out/design-styles.mp4
   ```

The scene code in `src/showcase/` is also a worked example of combining templates: overlays on footage, word-synced timing (the countdown follows the voice), captions per scene and labelled grids of mini-renders.
