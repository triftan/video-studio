import React from "react";
import {
  AbsoluteFill, Audio, CalculateMetadataFunction, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { clamp, easeOut } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type Word = { text: string; start: number; end: number };
export type ShowScene = {
  id: string; vo: string; audio: string; voStartFrame: number; durationInFrames: number; startFrame: number; words: Word[];
  preset?: string; style?: string;
};
export type ShowData = { fps: number; durationInFrames: number; music: string; scenes: ShowScene[] };
export type ShowProps = { dataUrl: string; data?: ShowData };

/** Reads public/showcase/<video>.json (written by showcase/build_showcase.py) and sizes the composition to it. */
export const showMetadata = (width: number, height: number): CalculateMetadataFunction<ShowProps> => async ({ props }) => {
  const data: ShowData = props.data ?? (await (await fetch(staticFile(props.dataUrl))).json());
  return { fps: data.fps, durationInFrames: data.durationInFrames, width, height, props: { ...props, data } };
};

/** Voice for a scene, placed at its lead-in offset, plus a music bed ducked under speech. */
export const SceneAudio: React.FC<{ scene: ShowScene }> = ({ scene }) => (
  <Sequence from={scene.voStartFrame} layout="none">
    <Audio src={staticFile(scene.audio)} />
  </Sequence>
);

export const MusicBed: React.FC<{ data: ShowData; volume?: number }> = ({ data, volume = 0.13 }) => {
  const { fps } = useVideoConfig();
  // duck to 45% while any voice is playing
  const speaking = (f: number) => data.scenes.some((s) => {
    const a = s.startFrame + s.voStartFrame + Math.round((s.words[0]?.start ?? 0.35) * fps) - Math.round(0.35 * fps);
    const b = s.startFrame + s.voStartFrame + Math.round((s.words[s.words.length - 1]?.end ?? 1) * fps) - Math.round(0.35 * fps);
    return f >= a - 4 && f <= b + 6;
  });
  return <Audio src={staticFile(data.music)} volume={(f) => volume * (speaking(f) ? 0.45 : 1)} />;
};

/** Plays each scene in sequence. `render` draws the scene's visuals. */
export const SceneSeries: React.FC<{ data: ShowData; render: (s: ShowScene, i: number) => React.ReactNode }> = ({ data, render }) => (
  <>
    {data.scenes.map((s, i) => (
      <Sequence key={s.id} from={s.startFrame} durationInFrames={s.durationInFrames} name={s.id}>
        {render(s, i)}
        <SceneAudio scene={s} />
      </Sequence>
    ))}
  </>
);

/** The on-screen "what you're looking at" chip. */
export const ShowLabel: React.FC<{ items: [string, string][]; dark?: boolean; top?: number }> = ({ items, dark = true, top }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const u = height / 1080;
  const vertical = useVideoConfig().width < height;
  const k = (vertical ? 1.15 : 1.3) * u;
  const e = interpolate(frame, [4, 14], [0, 1], { ...clamp, easing: easeOut });
  return (
    <AbsoluteFill style={{ alignItems: "center", pointerEvents: "none", zIndex: 50 }}>
      <div style={{
        marginTop: top ?? 22 * u, display: "flex", gap: 6 * k, padding: 6 * k, borderRadius: 999,
        background: dark ? "rgba(10,10,14,0.72)" : "rgba(255,255,255,0.85)", backdropFilter: "blur(10px)",
        border: dark ? "1px solid rgba(255,255,255,0.14)" : "1px solid rgba(0,0,0,0.08)",
        fontFamily: fonts.mono, fontSize: 17 * k, opacity: e, translate: `0 ${(1 - e) * -14}px`,
        boxShadow: "0 8px 30px rgba(0,0,0,0.18)", whiteSpace: "nowrap",
      }}>
        {items.map(([k1, v], i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 * k, padding: `${6 * k}px ${12 * k}px`, borderRadius: 999, background: dark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.05)" }}>
            <span style={{ color: dark ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.45)", textTransform: "uppercase", letterSpacing: "0.12em", fontSize: 13 * k }}>{k1}</span>
            <span style={{ color: dark ? "#fff" : "#111", fontWeight: 700 }}>{v}</span>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** Renders children at full composition size, scaled into a tile. */
export const Mini: React.FC<{ w: number; h: number; scale: number; children: React.ReactNode; radius?: number }> = ({ w, h, scale, children, radius = 18 }) => {
  const { width, height } = useVideoConfig();
  return (
    <div style={{ width: w, height: h, overflow: "hidden", borderRadius: radius, position: "relative", boxShadow: "0 18px 50px rgba(0,0,0,0.35)" }}>
      <div style={{ width, height, transform: `scale(${scale})`, transformOrigin: "top left", position: "absolute" }}>{children}</div>
    </div>
  );
};

/** Slowly moving gradient blobs: a cheap, pretty backdrop. */
export const Backdrop: React.FC<{ colors: [string, string, string]; base: string }> = ({ colors, base }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = frame / 30;
  const blob = (c: string, x: number, y: number, r: number, i: number) => (
    <div key={i} style={{
      position: "absolute", left: x + Math.sin(t * 0.5 + i) * width * 0.06, top: y + Math.cos(t * 0.4 + i * 2) * height * 0.06,
      width: r, height: r, borderRadius: 999, background: c, filter: `blur(${r * 0.35}px)`, opacity: 0.55,
    }} />
  );
  return (
    <AbsoluteFill style={{ background: base, overflow: "hidden" }}>
      {blob(colors[0], width * 0.05, height * 0.1, width * 0.45, 0)}
      {blob(colors[1], width * 0.55, height * 0.35, width * 0.4, 1)}
      {blob(colors[2], width * 0.25, height * 0.6, width * 0.35, 2)}
    </AbsoluteFill>
  );
};

/** Stand-in for camera footage: a softly lit "talking head" silhouette with slow handheld drift. */
export const FakeFootage: React.FC<{ tone?: string }> = ({ tone = "#2C3E50" }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const dx = Math.sin(frame / 37) * 6, dy = Math.cos(frame / 53) * 4;
  const breathe = 1 + Math.sin(frame / 24) * 0.006;
  const cx = width * 0.5, headR = height * 0.15;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 70% 30%, #6D8BA6 0%, ${tone} 55%, #0F1720 100%)`, overflow: "hidden" }}>
      <div style={{ position: "absolute", right: width * 0.08, top: height * 0.12, width: width * 0.22, height: height * 0.5, borderRadius: 12, background: "rgba(255,230,190,0.18)", filter: "blur(30px)" }} />
      <div style={{ position: "absolute", inset: 0, translate: `${dx}px ${dy}px`, scale: String(breathe) }}>
        <div style={{ position: "absolute", left: cx - headR, top: height * 0.24, width: headR * 2, height: headR * 2.3, borderRadius: "48% 48% 45% 45%", background: "linear-gradient(160deg,#D9B79A,#8C6650)" }} />
        <div style={{ position: "absolute", left: cx - headR * 1.05, top: height * 0.2, width: headR * 2.1, height: headR * 1.1, borderRadius: "50% 50% 30% 30%", background: "#2A1D17" }} />
        <div style={{ position: "absolute", left: cx - width * 0.2, top: height * 0.62, width: width * 0.4, height: height * 0.5, borderRadius: "45% 45% 0 0", background: "linear-gradient(180deg,#34495E,#1C2833)" }} />
      </div>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.45) 100%)" }} />
      <div style={{ position: "absolute", left: 24, bottom: 18, fontFamily: fonts.mono, fontSize: 14, color: "rgba(255,255,255,0.45)" }}>placeholder footage</div>
    </AbsoluteFill>
  );
};
