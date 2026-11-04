import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, enter, exit, fmt, pop } from "../lib/anim";
import { fonts } from "../lib/fonts";

type Point = { label: string; value: number };
export type LineChartProps = { title: string; points: Point[]; unit?: string; accent: string; background: string; text: string };

/** Line draws left to right over a soft area fill; the last point gets a pulsing marker and value tag. Full frame. */
export const LineChart: React.FC<LineChartProps> = ({ title, points, unit = "", accent, background, text }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const W = width * 0.8, H = height * 0.5, x0 = width * 0.1, y0 = height * 0.3;
  const max = Math.max(...points.map((p) => p.value)) * 1.1, min = Math.min(0, ...points.map((p) => p.value));
  const xy = points.map((p, i) => [x0 + (i / Math.max(1, points.length - 1)) * W, y0 + H - ((p.value - min) / (max - min)) * H]);
  const path = xy.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  const draw = interpolate(frame, [10, 60], [0, 1], { ...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const len = xy.reduce((s, [x, y], i) => (i ? s + Math.hypot(x - xy[i - 1][0], y - xy[i - 1][1]) : 0), 0);
  const last = xy[xy.length - 1];
  const tag = pop(frame, fps, 60);
  const pulse = 1 + 0.25 * Math.abs(Math.sin(frame / 8));

  return (
    <AbsoluteFill style={{ background, fontFamily: fonts.sans, color: text, opacity: exit(frame, durationInFrames) }}>
      <div style={{ position: "absolute", top: 90 * u, left: x0, fontSize: 60 * u, fontWeight: 800, opacity: enter(frame), letterSpacing: "-0.02em" }}>{title}</div>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={accent} stopOpacity={0.35} />
            <stop offset="1" stopColor={accent} stopOpacity={0} />
          </linearGradient>
          <clipPath id="reveal"><rect x={0} y={0} width={x0 + W * draw} height={height} /></clipPath>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((g) => (
          <line key={g} x1={x0} x2={x0 + W} y1={y0 + H * g} y2={y0 + H * g} stroke={text} strokeOpacity={0.08} strokeWidth={2} />
        ))}
        <path d={`${path} L${x0 + W},${y0 + H} L${x0},${y0 + H} Z`} fill="url(#area)" clipPath="url(#reveal)" />
        <path d={path} fill="none" stroke={accent} strokeWidth={8 * u} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        {draw >= 1 && <circle cx={last[0]} cy={last[1]} r={14 * u * pulse} fill={accent} fillOpacity={0.3} />}
        {draw >= 1 && <circle cx={last[0]} cy={last[1]} r={10 * u} fill={accent} />}
      </svg>
      {points.map((p, i) => (
        <div key={p.label} style={{ position: "absolute", left: xy[i][0], top: y0 + H + 20 * u, translate: "-50% 0", fontSize: 24 * u, opacity: 0.55 * enter(frame, 10 + i * 3) }}>{p.label}</div>
      ))}
      <div style={{
        position: "absolute", left: last[0], top: last[1] - 90 * u, translate: "-50% 0", scale: String(tag), background: accent, color: background,
        fontWeight: 800, fontSize: 34 * u, padding: `${8 * u}px ${18 * u}px`, borderRadius: 12 * u, fontVariantNumeric: "tabular-nums",
      }}>
        {fmt(points[points.length - 1].value)}{unit}
      </div>
    </AbsoluteFill>
  );
};
