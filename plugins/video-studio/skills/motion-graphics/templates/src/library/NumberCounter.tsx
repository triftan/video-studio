import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, Corner, exit, fmt, place, pop , OverlayProps } from "../lib/anim";
import { fonts, Theme } from "../lib/fonts";

export type NumberCounterProps = OverlayProps & Theme & {
  value: number; from: number; prefix?: string; suffix?: string; decimals: number;
  label: string; trend?: string; position: Corner; countSeconds: number;
};

/** Big metric that counts up with a live-dot label and optional trend chip. Transparent overlay. */
export const NumberCounter: React.FC<NumberCounterProps> = ({ size = 1.35,
  value, from, prefix = "", suffix = "", decimals, label, trend, position, countSeconds, accent, text, surface,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const cardIn = pop(frame, fps);
  const t = interpolate(frame, [6, 6 + countSeconds * fps], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const n = from + (value - from) * t;
  const blink = 0.5 + 0.5 * Math.sin(frame / 4);
  const trendIn = pop(frame, fps, 6 + countSeconds * fps);

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 60 * u), padding: `${28 * u}px ${36 * u}px`, borderRadius: 24 * u, background: surface,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)", fontFamily: fonts.sans, color: text,
        opacity: Math.min(1, cardIn * 1.4) * exit(frame, durationInFrames), scale: String(0.8 + cardIn * 0.2),
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 * u, fontSize: 20 * u, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", opacity: 0.6 }}>
          <div style={{ width: 10 * u, height: 10 * u, borderRadius: 99, background: accent, opacity: 0.4 + blink * 0.6 }} />
          {label}
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 16 * u }}>
          <div style={{ fontWeight: 900, fontSize: 120 * u, letterSpacing: "-0.04em", fontVariantNumeric: "tabular-nums", lineHeight: 1.05 }}>
            {prefix}{fmt(n, decimals)}{suffix}
          </div>
          {trend && (
            <div style={{ fontWeight: 800, fontSize: 26 * u, color: accent, background: `${accent}1A`, padding: `${6 * u}px ${14 * u}px`, borderRadius: 999, scale: String(trendIn) }}>
              {trend}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
