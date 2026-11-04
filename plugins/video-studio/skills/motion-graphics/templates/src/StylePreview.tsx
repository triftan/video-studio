import React from "react";
import { AbsoluteFill } from "remotion";
import { SceneView, StyleFonts, resolveStyle, Scene } from "./Explainer";
import { PresetCaptions } from "./PresetCaptions";
import { fonts } from "./lib/fonts";

export type StylePreviewProps = {
  /** design style key from styles/design-styles.json */ style: string;
  /** caption preset key from styles/caption-presets.json */ captionPreset: string;
  title: string;
  subtitle?: string;
  /** a sample spoken line, shown as captions */ caption: string;
  /** small tag in the corner, e.g. "Option A · Friendly lesson" */ tag?: string;
};

/** One frame that shows a design style and a caption preset together, for picking a look. */
export const StylePreview: React.FC<StylePreviewProps> = ({ style, captionPreset, title, subtitle, caption, tag }) => {
  const s = resolveStyle(style);
  const scene: Scene = { id: "preview", type: "title", title, subtitle };
  // words appear already spoken, with the 3rd word active, so the highlight treatment is visible
  const words = caption.split(/\s+/).filter(Boolean).map((text, i) => ({ text, start: i * 0.25, end: i * 0.25 + 0.25 }));
  return (
    <AbsoluteFill>
      <StyleFonts style={s} />
      <SceneView scene={scene} style={s} />
      <PresetCaptions preset={captionPreset} words={words} y={0.88} wordsPerPage={6} />
      {tag && (
        <div style={{
          position: "absolute", top: 28, right: 28, fontFamily: fonts.mono, fontSize: 22, padding: "8px 16px", borderRadius: 999,
          background: "rgba(0,0,0,0.65)", color: "#fff",
        }}>{tag}</div>
      )}
    </AbsoluteFill>
  );
};
