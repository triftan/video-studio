import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import presetsFile from "../data/caption-presets.json";
import { Backdrop, FakeFootage, MusicBed, SceneSeries, ShowLabel, ShowProps, ShowScene } from "./common";
import { PresetCaptions } from "../PresetCaptions";
import { SceneView, StyleFonts, resolveStyle, Scene as ExplainerScene } from "../Explainer";
import { clamp, enter } from "../lib/anim";
import { fonts } from "../lib/fonts";

const PRESETS = (presetsFile as unknown as { presets: Record<string, { label: string; fontFamily: string; color: string; highlightColor?: string }> }).presets;

const BACKDROPS: [string, string, string][] = [
  ["#FF2E63", "#7C5CFF", "#25F4EE"], ["#00E83C", "#0A0A0A", "#3D7BFF"], ["#E50914", "#221F1F", "#5A5A5A"],
  ["#FFEC1A", "#FF4D8D", "#3BC9F5"], ["#C8A96A", "#3A2A20", "#E8C07D"], ["#4DFFDF", "#0E1A2B", "#7C5CFF"],
  ["#A3FF12", "#071007", "#14C38E"], ["#B64A3B", "#F4F1EA", "#C8A96A"], ["#FFE20A", "#111111", "#FF3B30"],
];

/** 9:16 short: one line per caption preset, over placeholder footage, labelled. */
const CaptionScene: React.FC<{ s: ShowScene; i: number }> = ({ s, i }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const u = height / 1920;
  const preset = s.preset ?? "plain";
  const p = PRESETS[preset];
  const wipe = interpolate(frame, [0, 8], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ clipPath: `inset(0 0 ${(1 - wipe) * 100}% 0)` }}>
      <Backdrop colors={BACKDROPS[i % BACKDROPS.length]} base="#08080C" />
      <AbsoluteFill style={{ opacity: 0.85 }}><FakeFootage tone="#22303F" /></AbsoluteFill>
      <PresetCaptions preset={preset} words={s.words} y={0.66} wordsPerPage={preset === "submagic" ? 3 : 3} />
      <AbsoluteFill style={{ alignItems: "center" }}>
        <div style={{ marginTop: 300 * u, textAlign: "center", fontFamily: fonts.sans, color: "#fff", opacity: enter(frame, 6) }}>
          <div style={{ fontSize: 30 * u, letterSpacing: "0.3em", textTransform: "uppercase", opacity: 0.6 }}>caption style {String(i + 1).padStart(2, "0")}</div>
          <div style={{ fontSize: 76 * u, fontWeight: 900, letterSpacing: "-0.02em", textShadow: "0 4px 30px rgba(0,0,0,0.5)" }}>{p?.label}</div>
          <div style={{ fontSize: 28 * u, opacity: 0.7, marginTop: 6 * u }}>{p?.fontFamily}</div>
        </div>
      </AbsoluteFill>
      <ShowLabel items={[["Preset", preset], ["Template", "PresetCaptions"]]} top={90 * u} />
    </AbsoluteFill>
  );
};

export const CaptionStyles: React.FC<ShowProps> = ({ data }) => {
  if (!data) throw new Error("showcase data not loaded");
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <SceneSeries data={data} render={(s, i) => <CaptionScene s={s} i={i} />} />
      <MusicBed data={data} volume={0.1} />
    </AbsoluteFill>
  );
};

/** 16:9 reel: one Explainer scene per design style, captions in that style's own preset. */
const KIND: Record<string, ExplainerScene> = {
  "clean-saas": { id: "a", type: "steps", title: "How it works", items: ["Upload your footage", "Describe the edit", "Review and export"] },
  "dark-tech": { id: "b", type: "stat", value: 47, unit: "", label: "pauses removed in a 10-minute talk (illustrative)" },
  "editorial": { id: "c", type: "quote", quote: "The best edit is the one nobody notices.", author: "An editor's rule of thumb" },
  "playful-pop": { id: "d", type: "bullets", title: "Make it pop", items: ["Bouncy captions", "Sticker callouts", "Punch-in zooms"] },
  "corporate-trust": { id: "e", type: "chart", title: "Minutes per video (illustrative)", unit: "m", bars: [{ label: "By hand", value: 240 }, { label: "AI first pass", value: 35 }, { label: "AI + review", value: 50 }] },
  "warm-story": { id: "f", type: "title", title: "Every story", subtitle: "deserves a good edit" },
  "bold-creator": { id: "g", type: "stat", value: 3, unit: "x", label: "more videos a week (illustrative)" },
  "edu-chalk": { id: "h", type: "steps", title: "Today's lesson", items: ["Find the hook", "Cut the dead air", "Caption everything"] },
};

const StyleScene: React.FC<{ s: ShowScene }> = ({ s }) => {
  const key = s.style ?? "clean-saas";
  const style = resolveStyle(key);
  const c = style.colors;
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const u = height / 1080;
  const light = ["clean-saas", "editorial", "playful-pop", "corporate-trust"].includes(key);
  return (
    <AbsoluteFill>
      <StyleFonts style={style} />
      <SceneView scene={KIND[key]} style={style} />
      <PresetCaptions preset={style.captionPreset ?? "plain"} words={s.words} y={0.92} wordsPerPage={6} />
      {/* palette + fonts card */}
      <div style={{ position: "absolute", right: 40 * u, bottom: 150 * u, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10 * u, opacity: enter(frame, 10) }}>
        <div style={{ display: "flex", gap: 8 * u }}>
          {Object.values(c).map((col, i) => (
            <div key={i} style={{ width: 34 * u, height: 34 * u, borderRadius: 8 * u, background: col, border: "1px solid rgba(128,128,128,0.4)", scale: String(enter(frame, 12 + i * 2, 8)) }} />
          ))}
        </div>
        <div style={{ fontFamily: fonts.mono, fontSize: 16 * u, color: light ? "rgba(0,0,0,0.55)" : "rgba(255,255,255,0.6)" }}>
          {style.fonts.heading} / {style.fonts.body}
        </div>
      </div>
      <ShowLabel dark={!light} items={[["Style", key], ["Scene", `Explainer · ${KIND[key].type}`], ["Captions", style.captionPreset ?? "plain"]]} />
    </AbsoluteFill>
  );
};

export const DesignStyles: React.FC<ShowProps> = ({ data }) => {
  if (!data) throw new Error("showcase data not loaded");
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <SceneSeries data={data} render={(s) => <StyleScene s={s} />} />
      <MusicBed data={data} volume={0.1} />
    </AbsoluteFill>
  );
};
