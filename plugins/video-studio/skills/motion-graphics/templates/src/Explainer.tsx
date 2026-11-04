import React, { useEffect, useState } from "react";
import {
  AbsoluteFill, Audio, CalculateMetadataFunction, Easing, Img, Series, continueRender, delayRender,
  interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import stylesFile from "./data/design-styles.json";

export type DesignStyle = {
  label: string;
  colors: { background: string; surface: string; text: string; muted: string; accent: string; accent2: string };
  fonts: { heading: string; headingWeight: string; body: string; bodyWeight: string };
  captionPreset?: string;
  style_guide?: string;
};

export type Scene = {
  id: string; type: "title" | "bullets" | "steps" | "stat" | "quote" | "image" | "chart" | "cta";
  vo?: string; audio?: string; durationInFrames?: number;
  title?: string; subtitle?: string; items?: string[]; value?: number; unit?: string; label?: string;
  quote?: string; author?: string; src?: string; bars?: { label: string; value: number }[]; url?: string;
};

export type Storyboard = { style: string | DesignStyle; format?: "16:9" | "9:16"; fps?: number; music?: string; scenes: Scene[] };
type Props = { storyboardUrl?: string; storyboard?: Storyboard };

const STYLES = (stylesFile as unknown as { styles: Record<string, DesignStyle> }).styles;
const DEFAULT_SCENE_FRAMES = 120;

export const resolveStyle = (s: Storyboard["style"]): DesignStyle => {
  if (typeof s !== "string") return s;
  const style = STYLES[s];
  if (!style) throw new Error(`Unknown design style "${s}". Options: ${Object.keys(STYLES).join(", ")}`);
  return style;
};

const loadStoryboard = async (props: Props): Promise<Storyboard> =>
  props.storyboard ?? (await (await fetch(staticFile(props.storyboardUrl ?? "storyboard.json"))).json());

/** Sets duration and size from the storyboard so the composition always fits the voiceover. */
export const calculateExplainerMetadata: CalculateMetadataFunction<Props> = async ({ props }) => {
  const sb = await loadStoryboard(props);
  const fps = sb.fps ?? 30;
  const vertical = sb.format === "9:16";
  return {
    fps,
    width: vertical ? 1080 : 1920,
    height: vertical ? 1920 : 1080,
    durationInFrames: sb.scenes.reduce((n, s) => n + (s.durationInFrames ?? DEFAULT_SCENE_FRAMES), 0),
    props: { ...props, storyboard: sb },
  };
};

export const useFonts = (style: DesignStyle) => {
  const [handle] = useState(() => delayRender("design style fonts"));
  useEffect(() => {
    const fams = [[style.fonts.heading, style.fonts.headingWeight], [style.fonts.body, style.fonts.bodyWeight]];
    const href = "https://fonts.googleapis.com/css2?" +
      fams.map(([f, w]) => `family=${encodeURIComponent(f)}:wght@${w}`).join("&") + "&display=swap";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.addEventListener("load", () => {
      Promise.all(fams.map(([f, w]) => document.fonts.load(`${w} 40px "${f}"`))).finally(() => continueRender(handle));
    }, { once: true });
    link.addEventListener("error", () => continueRender(handle), { once: true });
    document.head.appendChild(link);
  }, [style, handle]);
};

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Shared entrance: fade + rise, staggered by index. Exit: quick fade in the last 8 frames. */
const useEnter = (index = 0, delay = 0) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(frame - delay - index * 4, [0, 12], [0, 1], { ...clamp, easing: ease });
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], clamp);
  return { opacity: t * out, transform: `translateY(${(1 - t) * 28}px)` };
};

export const SceneView: React.FC<{ scene: Scene; style: DesignStyle }> = ({ scene, style }) => {
  const { width, height, fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const c = style.colors;
  const u = Math.min(width, height) / 1080; // layout unit
  const H: React.CSSProperties = { fontFamily: `"${style.fonts.heading}"`, fontWeight: Number(style.fonts.headingWeight), color: c.text, lineHeight: 1.05, letterSpacing: "-0.02em" };
  const B: React.CSSProperties = { fontFamily: `"${style.fonts.body}"`, fontWeight: Number(style.fonts.bodyWeight), color: c.muted, lineHeight: 1.35 };
  const pad = { padding: `${height * 0.1}px ${width * 0.08}px` };
  const e0 = useEnter(0), e1 = useEnter(1), e2 = useEnter(2);

  const body = (() => {
    switch (scene.type) {
      case "title":
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center" }}>
            <div style={{ ...H, fontSize: 150 * u, color: c.accent, ...e0 }}>{scene.title}</div>
            {scene.subtitle && <div style={{ ...B, fontSize: 48 * u, marginTop: 20 * u, ...e1 }}>{scene.subtitle}</div>}
          </AbsoluteFill>
        );
      case "bullets":
      case "steps":
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center", gap: 28 * u }}>
            {scene.title && <div style={{ ...H, fontSize: 72 * u, marginBottom: 16 * u, ...e0 }}>{scene.title}</div>}
            {(scene.items ?? []).map((item, i) => (
              <Item key={i} index={i + 1} u={u} style={style} numbered={scene.type === "steps"} text={item} H={H} />
            ))}
          </AbsoluteFill>
        );
      case "stat": {
        const s = spring({ frame: frame - 4, fps, config: { damping: 22, stiffness: 80 } });
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center", alignItems: "center", textAlign: "center" }}>
            <div style={{ ...H, fontSize: 260 * u, color: c.accent, fontVariantNumeric: "tabular-nums", ...e0 }}>
              {Math.round((scene.value ?? 0) * s)}{scene.unit}
            </div>
            <div style={{ ...B, fontSize: 46 * u, maxWidth: width * 0.7, ...e1 }}>{scene.label}</div>
          </AbsoluteFill>
        );
      }
      case "chart": {
        const bars = scene.bars ?? [];
        const max = Math.max(...bars.map((b) => b.value), 1);
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center", gap: 22 * u }}>
            <div style={{ ...H, fontSize: 64 * u, marginBottom: 20 * u, ...e0 }}>{scene.title}</div>
            {bars.map((b, i) => {
              const g = spring({ frame: frame - 8 - i * 5, fps, config: { damping: 22, stiffness: 90 } });
              const top = b.value === max;
              return (
                <div key={b.label} style={{ display: "flex", alignItems: "center", gap: 24 * u }}>
                  <div style={{ ...B, width: width * 0.16, fontSize: 32 * u }}>{b.label}</div>
                  <div style={{ flex: 1, height: 44 * u, background: c.surface, borderRadius: 12 * u }}>
                    <div style={{ height: "100%", width: `${(b.value / max) * 100 * g}%`, background: top ? c.accent : c.muted, opacity: top ? 1 : 0.45, borderRadius: 12 * u }} />
                  </div>
                  <div style={{ ...H, width: 140 * u, fontSize: 40 * u, textAlign: "right", color: top ? c.accent : c.text }}>
                    {Math.round(b.value * g)}{scene.unit}
                  </div>
                </div>
              );
            })}
          </AbsoluteFill>
        );
      }
      case "quote":
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center" }}>
            <div style={{ ...H, fontSize: 200 * u, color: c.accent, height: 110 * u, ...e0 }}>&ldquo;</div>
            <div style={{ ...H, fontSize: 76 * u, maxWidth: width * 0.8, ...e1 }}>{scene.quote}</div>
            {scene.author && <div style={{ ...B, fontSize: 36 * u, marginTop: 28 * u, ...e2 }}>{scene.author}</div>}
          </AbsoluteFill>
        );
      case "image": {
        const zoom = interpolate(frame, [0, 300], [1, 1.08], clamp);
        return (
          <AbsoluteFill>
            {scene.src && <Img src={staticFile(scene.src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})` }} />}
            {scene.title && (
              <AbsoluteFill style={{ ...pad, justifyContent: "flex-end", background: "linear-gradient(transparent 55%, rgba(0,0,0,0.6))" }}>
                <div style={{ ...H, color: "#fff", fontSize: 64 * u, ...e0 }}>{scene.title}</div>
              </AbsoluteFill>
            )}
          </AbsoluteFill>
        );
      }
      case "cta":
        return (
          <AbsoluteFill style={{ ...pad, justifyContent: "center", alignItems: "center", textAlign: "center" }}>
            <div style={{ ...H, fontSize: 120 * u, ...e0 }}>{scene.title}</div>
            {scene.url && (
              <div style={{ ...H, fontSize: 44 * u, marginTop: 36 * u, color: c.background, background: c.accent, padding: `${16 * u}px ${40 * u}px`, borderRadius: 999, ...e1 }}>
                {scene.url}
              </div>
            )}
          </AbsoluteFill>
        );
    }
  })();

  return (
    <AbsoluteFill style={{ background: c.background }}>
      {body}
      {scene.audio && <Audio src={staticFile(scene.audio)} />}
    </AbsoluteFill>
  );
};

const Item: React.FC<{ index: number; u: number; style: DesignStyle; numbered: boolean; text: string; H: React.CSSProperties }> =
  ({ index, u, style, numbered, text, H }) => {
    const e = useEnter(index, 6);
    const c = style.colors;
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 28 * u, ...e }}>
        <div style={{
          width: 64 * u, height: 64 * u, borderRadius: numbered ? 999 : 16 * u, flexShrink: 0,
          background: numbered ? c.accent : c.surface, color: numbered ? c.background : c.accent,
          display: "flex", alignItems: "center", justifyContent: "center", ...H, fontSize: 34 * u, lineHeight: 1,
          border: numbered ? undefined : `3px solid ${c.accent}`,
        }}>
          {numbered ? index : "✓"}
        </div>
        <div style={{ ...H, fontSize: 56 * u, fontWeight: Number(style.fonts.bodyWeight) + 200 }}>{text}</div>
      </div>
    );
  };

/** Loads a design style's fonts (render once per composition). */
export const StyleFonts: React.FC<{ style: DesignStyle }> = ({ style }) => {
  useFonts(style);
  return null;
};

/** Renders a storyboard (see explainer-videos skill) scene by scene in a design style. */
export const Explainer: React.FC<Props> = ({ storyboard }) => {
  if (!storyboard) throw new Error("storyboard not loaded; calculateMetadata should provide it");
  const style = resolveStyle(storyboard.style);
  useFonts(style);
  return (
    <AbsoluteFill style={{ background: style.colors.background }}>
      <Series>
        {storyboard.scenes.map((scene) => (
          <Series.Sequence key={scene.id} durationInFrames={scene.durationInFrames ?? DEFAULT_SCENE_FRAMES} name={scene.id}>
            <SceneView scene={scene} style={style} />
          </Series.Sequence>
        ))}
      </Series>
      {storyboard.music && <Audio src={staticFile(storyboard.music)} volume={0.12} />}
    </AbsoluteFill>
  );
};
