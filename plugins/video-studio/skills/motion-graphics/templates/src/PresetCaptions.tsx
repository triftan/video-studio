import React, { useEffect, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, Easing, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import presetsFile from "./data/caption-presets.json";

type Word = { text: string; start: number; end: number };
type Box = { color: string; borderRadius?: number; paddingX?: number; paddingY?: number; shadow?: string } | null;
type Keyframe = { offset: number; opacity?: number; clipPath?: string; transform?: { scale?: number; translateX?: string } };
type Phase = { durationMs: number; easing: string; keyframes: Keyframe[] };
type Preset = {
  label: string; fontFamily: string; fontFallbacks?: string[]; fontSize: number; fontWeight: string;
  color: string; highlightColor?: string; highlightBackground?: Box; normalBackground?: Box;
  highlightUnit?: "off" | "word" | "line"; displayMode?: "single" | "stacked";
  stackedGap?: number; stackedLineTiltDeg?: { active?: number; normal?: number }; strokeColor?: string; strokeWidth?: number; textShadow?: string;
  textTransform?: string; letterSpacing?: number; lineHeight?: number; wordsPerPage?: number;
  wordAnimation?: { enter?: Phase; exit?: Phase };
};

const PRESETS = (presetsFile as unknown as { presets: Record<string, Preset> }).presets;

type Props = { preset: string; wordsUrl?: string; words?: Word[]; wordsPerPage?: number; y?: number; /** font size multiplier */ scale?: number };

/** Load a Google Font by family name and block rendering until it is ready. */
/** Some presets use fonts that are not on Google Fonts; load a close Google font in their place. */
const FONT_SUBSTITUTES: Record<string, string> = {
  "Xinqingnian Ti": "Anton",
  "HarmonyOS Sans": "Noto Sans SC",
  "Qingsong Shouxie Ti Yi": "Caveat",
};
export const loadableFont = (family: string) => FONT_SUBSTITUTES[family] ?? family;

/** Load a Google Font by family name and block rendering until it is ready (or has failed). */
const useGoogleFont = (rawFamily: string, weight: string, sampleText: string) => {
  const family = loadableFont(rawFamily);
  const [handle] = useState(() => delayRender(`font ${family}`, { timeoutInMilliseconds: 60000 }));
  useEffect(() => {
    if (!sampleText) return; // wait until the words are known
    let done = false;
    const finish = () => { if (!done) { done = true; continueRender(handle); } };
    const id = `gf-${family.replace(/\s+/g, "-")}-${weight}`;
    let link = document.getElementById(id) as HTMLLinkElement | null;
    if (!link) {
      link = document.createElement("link");
      link.id = id;
      link.rel = "stylesheet";
      // ask for the nearest available weights so a missing weight doesn't fail the whole request
      link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@${weight}&display=swap`;
      document.head.appendChild(link);
    }
    const ready = link.sheet ? Promise.resolve() : new Promise<void>((res) => {
      link!.addEventListener("load", () => res(), { once: true });
      link!.addEventListener("error", () => res(), { once: true }); // unknown family: fall back, don't hang
    });
    // Large fonts (e.g. CJK) are split into unicode-range chunks: load the chunks the captions actually use.
    ready
      .then(() => document.fonts.load(`${weight} 40px "${family}"`, sampleText))
      .then(() => document.fonts.ready)
      .catch(() => undefined)
      .finally(finish);
    const t = setTimeout(finish, 20000); // never block a render on a font
    return () => clearTimeout(t);
  }, [family, weight, handle, sampleText]);
};

const useWords = (words?: Word[], url?: string) => {
  const [data, setData] = useState<Word[] | null>(words ?? null);
  const [handle] = useState(() => (words ? null : delayRender("words")));
  useEffect(() => {
    if (words || !url) return;
    fetch(staticFile(url)).then((r) => r.json()).then((w: Word[]) => {
      setData(w);
      if (handle !== null) continueRender(handle);
    });
  }, [words, url, handle]);
  return data ?? [];
};

const bezier = (css: string) => {
  const m = css.match(/cubic-bezier\(([^)]+)\)/);
  if (m) {
    const [a, b, c, d] = m[1].split(",").map(Number);
    return Easing.bezier(a, b, c, d);
  }
  if (css === "ease-in") return Easing.bezier(0.42, 0, 1, 1);
  if (css === "ease-out") return Easing.bezier(0, 0, 0.58, 1);
  if (css === "linear") return (t: number) => t;
  return Easing.bezier(0.25, 0.1, 0.25, 1);
};

/** Sample a preset's keyframe phase at progress t (0-1) into CSS. */
const samplePhase = (phase: Phase, t: number): React.CSSProperties => {
  const p = bezier(phase.easing)(Math.min(1, Math.max(0, t)));
  const kfs = phase.keyframes;
  let a = kfs[0], b = kfs[kfs.length - 1];
  for (let i = 0; i < kfs.length - 1; i++) {
    if (p >= kfs[i].offset && p <= kfs[i + 1].offset) { a = kfs[i]; b = kfs[i + 1]; break; }
  }
  const span = b.offset - a.offset || 1;
  const k = (p - a.offset) / span;
  const mix = (x?: number, y?: number, d = 1) => (x ?? d) + ((y ?? d) - (x ?? d)) * k;
  const tx = (v?: string) => parseFloat(v ?? "0");
  const scale = mix(a.transform?.scale, b.transform?.scale);
  const translateX = tx(a.transform?.translateX) + (tx(b.transform?.translateX) - tx(a.transform?.translateX)) * k;
  return {
    opacity: mix(a.opacity, b.opacity),
    transform: `translateX(${translateX}em) scale(${scale})`,
    clipPath: k < 0.5 ? a.clipPath : b.clipPath,
  };
};

const boxStyle = (box: Box, unit: number): React.CSSProperties =>
  box ? {
    background: box.color, borderRadius: (box.borderRadius ?? 0) * unit,
    padding: `${(box.paddingY ?? 0) * unit}px ${(box.paddingX ?? 0) * unit}px`, boxShadow: box.shadow,
  } : {};

/**
 * Captions styled by any preset in styles/caption-presets.json, timed from words.json.
 * Renders on a transparent background so it can be laid over footage.
 */
export const PresetCaptions: React.FC<Props> = ({ preset, wordsUrl, words, wordsPerPage, y, scale = 1 }) => {
  const p = PRESETS[preset];
  if (!p) throw new Error(`Unknown caption preset "${preset}". Options: ${Object.keys(PRESETS).join(", ")}`);
  const all = useWords(words, wordsUrl);
  useGoogleFont(p.fontFamily, p.fontWeight, all.map((w) => w.text).join(" "));
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const vertical = height > width;
  const unit = (height / 1080) * scale; // preset pixel values are authored at 1080p
  const perPage = wordsPerPage ?? p.wordsPerPage ?? (vertical ? 3 : 6);

  const pages: Word[][] = [];
  for (let i = 0; i < all.length; i += perPage) pages.push(all.slice(i, i + perPage));
  const page = pages.find((pg, i) => t >= pg[0].start && t < (pages[i + 1]?.[0].start ?? pg[pg.length - 1].end + 0.3));
  if (!page) return <AbsoluteFill />;

  const pageEnd = page[page.length - 1].end + 0.3;
  const exit = p.wordAnimation?.exit;
  const exitT = exit ? (t - (pageEnd - exit.durationMs / 1000)) / (exit.durationMs / 1000) : -1;
  const hiUnit = p.highlightUnit ?? "word";
  const stacked = p.displayMode === "stacked";
  const ls = p.letterSpacing ?? 0;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: height * (1 - (y ?? (vertical ? 0.72 : 0.86))) }}>
      <div style={{
        display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "center", maxWidth: width * 0.84,
        flexDirection: stacked ? "column" : "row",
        gap: stacked ? (p.stackedGap ?? 0) * height : `0 ${0.25}em`,
        fontFamily: [p.fontFamily, loadableFont(p.fontFamily), ...(p.fontFallbacks ?? []), "sans-serif"].map((f) => `"${f}"`).join(", "),
        fontWeight: Number(p.fontWeight), fontSize: p.fontSize * height * scale, lineHeight: p.lineHeight ?? 1.2,
        letterSpacing: Math.abs(ls) <= 0.1 ? `${ls}em` : `${ls * unit}px`, color: p.color,
        textTransform: (p.textTransform ?? "none") as React.CSSProperties["textTransform"],
        textShadow: p.textShadow === "none" ? undefined : p.textShadow,
        WebkitTextStroke: p.strokeWidth ? `${p.strokeWidth * unit}px ${p.strokeColor}` : undefined,
        paintOrder: "stroke fill",
        ...(stacked ? {} : boxStyle(p.normalBackground ?? null, unit)),
        ...(exit && exitT >= 0 ? samplePhase(exit, exitT) : {}),
      }}>
        {page.map((w, i) => {
          const active = t >= w.start && t < (page[i + 1]?.start ?? pageEnd);
          // stacked: each word is its own line, so "line" highlighting follows the active word
          const highlighted = hiUnit !== "off" && (active || (hiUnit === "line" && !stacked));
          const enter = p.wordAnimation?.enter;
          const enterT = enter ? (t - w.start) / (enter.durationMs / 1000) : 1;
          const visible = t >= w.start || !enter;
          if (!visible && (p.normalBackground || stacked)) return null; // boxed styles grow word by word
          return (
            <span key={`${w.start}-${i}`} style={{
              display: "inline-block",
              opacity: visible ? 1 : 0,
              color: highlighted ? p.highlightColor ?? p.color : p.color,
              ...(stacked && !highlighted ? boxStyle(p.normalBackground ?? null, unit) : {}),
              ...(highlighted && p.highlightBackground ? boxStyle(p.highlightBackground, unit) : {}),
              ...(stacked ? { rotate: `${(active ? p.stackedLineTiltDeg?.active : p.stackedLineTiltDeg?.normal) ?? 0}deg` } : {}),
              ...(enter && visible && enterT < 1 ? samplePhase(enter, enterT) : {}),
            }}>
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
