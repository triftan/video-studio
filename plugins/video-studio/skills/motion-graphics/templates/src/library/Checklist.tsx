import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, Corner, enter, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts, Theme } from "../lib/fonts";

export type ChecklistProps = OverlayProps & Theme & { title: string; tag?: string; items: string[]; position: Corner; secondsPerItem: number };

/** Card with a list that ticks off one item at a time. Transparent overlay. */
export const Checklist: React.FC<ChecklistProps> = ({ size = 1.35, title, tag, items, position, secondsPerItem, accent, text, surface }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const cardIn = pop(frame, fps);
  const out = exit(frame, durationInFrames);
  const step = Math.round(secondsPerItem * fps);

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 60 * u), width: 520 * u, padding: 32 * u, borderRadius: 24 * u, background: surface,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)", fontFamily: fonts.sans, color: text,
        opacity: Math.min(1, cardIn * 1.4) * out,
        scale: String(0.85 + cardIn * 0.15), transformOrigin: position.replace("-", " "),
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 * u }}>
          <div style={{ fontWeight: 800, fontSize: 34 * u }}>{title}</div>
          {tag && <div style={{ fontSize: 16 * u, fontWeight: 700, letterSpacing: "0.12em", color: accent, background: `${accent}1A`, padding: `${6 * u}px ${12 * u}px`, borderRadius: 999 }}>{tag}</div>}
        </div>
        {items.map((item, i) => {
          const shown = enter(frame, 8 + i * 4, 10);
          const checkAt = 20 + (i + 1) * step;
          const check = pop(frame, fps, checkAt);
          const done = frame >= checkAt;
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 18 * u, padding: `${12 * u}px 0`, opacity: shown, translate: `${(1 - shown) * 20}px 0` }}>
              <div style={{
                width: 34 * u, height: 34 * u, borderRadius: 10 * u, flexShrink: 0,
                border: `3px solid ${done ? accent : `${text}33`}`, background: done ? accent : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <svg width={20 * u} height={20 * u} viewBox="0 0 20 20" style={{ scale: String(check) }}>
                  <path d="M4 10.5l4 4 8-9" fill="none" stroke={surface} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round"
                    strokeDasharray={24} strokeDashoffset={interpolate(check, [0, 1], [24, 0], clamp)} />
                </svg>
              </div>
              <div style={{ fontSize: 28 * u, fontWeight: 600, opacity: done ? 0.55 : 1, position: "relative" }}>
                {item}
                <div style={{ position: "absolute", left: 0, top: "52%", height: 3 * u, background: text, opacity: 0.6, width: `${interpolate(frame, [checkAt, checkAt + 8], [0, 100], clamp)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
