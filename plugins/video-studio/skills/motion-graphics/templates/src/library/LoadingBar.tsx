import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, Corner, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts, Theme } from "../lib/fonts";

export type LoadingBarProps = OverlayProps & Theme & { stages: string[]; doneLabel: string; position: Corner; fillSeconds: number };

/** Progress bar that steps through stage labels with a shimmer, then flips to a done state. Transparent overlay. */
export const LoadingBar: React.FC<LoadingBarProps> = ({ size = 1.35, stages, doneLabel, position, fillSeconds, accent, text, surface }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const cardIn = pop(frame, fps);
  const fillEnd = 8 + fillSeconds * fps;
  const p = interpolate(frame, [8, fillEnd], [0, 1], { ...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1) });
  const done = frame >= fillEnd;
  const doneP = pop(frame, fps, fillEnd);
  const stage = stages[Math.min(stages.length - 1, Math.floor(p * stages.length))];
  const shimmer = ((frame * 3) % 140) - 20;

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 60 * u), width: 560 * u, padding: `${26 * u}px ${30 * u}px`, borderRadius: 22 * u, background: surface,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)", fontFamily: fonts.sans, color: text,
        opacity: Math.min(1, cardIn * 1.4) * exit(frame, durationInFrames), scale: String(0.85 + cardIn * 0.15),
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 26 * u, fontWeight: 700, marginBottom: 16 * u }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 * u }}>
            {done ? (
              <div style={{ width: 30 * u, height: 30 * u, borderRadius: 99, background: accent, color: surface, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 * u, scale: String(doneP) }}>✓</div>
            ) : (
              <div style={{ width: 26 * u, height: 26 * u, borderRadius: 99, border: `4px solid ${accent}33`, borderTopColor: accent, rotate: `${frame * 14}deg` }} />
            )}
            <span>{done ? doneLabel : stage}</span>
          </div>
          <span style={{ fontFamily: fonts.mono, fontVariantNumeric: "tabular-nums", opacity: 0.6 }}>{Math.round(p * 100)}%</span>
        </div>
        <div style={{ height: 14 * u, borderRadius: 99, background: `${text}14`, overflow: "hidden" }}>
          <div style={{ position: "relative", height: "100%", width: `${p * 100}%`, borderRadius: 99, background: accent, overflow: "hidden" }}>
            {!done && <div style={{ position: "absolute", top: 0, bottom: 0, left: `${shimmer}%`, width: "30%", background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)" }} />}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
