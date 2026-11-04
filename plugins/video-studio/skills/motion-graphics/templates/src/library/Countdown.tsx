import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, exit } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type CountdownProps = { from: number; label: string; goText: string; accent: string; background: string; text: string; secondsPerCount?: number };

/** Ring countdown: each second the number punches in while the ring drains; ends on a GO flash. Full frame. */
export const Countdown: React.FC<CountdownProps> = ({ from, label, goText, accent, background, text, secondsPerCount = 1 }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const step = Math.max(1, Math.round(secondsPerCount * fps));
  const sec = Math.floor(frame / step);
  const inSec = (frame % step) / step;
  const n = from - sec;
  const go = n <= 0;
  const r = 230 * u, C = 2 * Math.PI * r;
  const punch = interpolate(inSec, [0, 0.15, 0.3], [1.35, 0.96, 1], clamp);
  const fade = interpolate(inSec, [0.75, 1], [1, 0.4], clamp);
  const flash = go ? interpolate(frame - from * step, [0, 8], [0.8, 0], clamp) : 0;

  return (
    <AbsoluteFill style={{ background, fontFamily: fonts.sans, color: text, justifyContent: "center", alignItems: "center", opacity: exit(frame, durationInFrames) }}>
      <svg width={r * 2 + 40 * u} height={r * 2 + 40 * u} style={{ position: "absolute", rotate: "-90deg" }}>
        <circle cx={r + 20 * u} cy={r + 20 * u} r={r} fill="none" stroke={text} strokeOpacity={0.1} strokeWidth={18 * u} />
        {!go && <circle cx={r + 20 * u} cy={r + 20 * u} r={r} fill="none" stroke={accent} strokeWidth={18 * u} strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * inSec} />}
      </svg>
      <div style={{ fontWeight: 900, fontSize: (go ? 200 : 300) * u, scale: String(punch), opacity: go ? 1 : fade, color: go ? accent : text, fontVariantNumeric: "tabular-nums" }}>
        {go ? goText : n}
      </div>
      <div style={{ position: "absolute", bottom: 160 * u, fontSize: 30 * u, fontWeight: 700, letterSpacing: "0.3em", textTransform: "uppercase", opacity: 0.6 }}>{label}</div>
      <AbsoluteFill style={{ background: accent, opacity: flash }} />
    </AbsoluteFill>
  );
};
