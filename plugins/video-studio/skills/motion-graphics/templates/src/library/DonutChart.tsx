import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, enter, exit } from "../lib/anim";
import { fonts } from "../lib/fonts";

type Slice = { label: string; value: number; color: string };
export type DonutChartProps = { title: string; slices: Slice[]; background: string; text: string };

/** Donut chart whose slices sweep in clockwise, with a legend and a center total. Full frame. */
export const DonutChart: React.FC<DonutChartProps> = ({ title, slices, background, text }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const sweep = interpolate(frame, [8, 50], [0, 1], { ...clamp, easing: Easing.bezier(0.65, 0, 0.35, 1) });
  const r = 200 * u, stroke = 70 * u, C = 2 * Math.PI * r;
  const lead = slices.reduce((a, b) => (b.value > a.value ? b : a), slices[0]);
  let acc = 0;

  return (
    <AbsoluteFill style={{ background, fontFamily: fonts.sans, color: text, opacity: exit(frame, durationInFrames) }}>
      <div style={{ position: "absolute", top: 90 * u, left: width * 0.08, fontSize: 60 * u, fontWeight: 800, opacity: enter(frame), letterSpacing: "-0.02em" }}>
        {title}
      </div>
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 120 * u, paddingTop: 80 * u }}>
        <div style={{ position: "relative", width: (r + stroke) * 2, height: (r + stroke) * 2 }}>
          <svg width={(r + stroke) * 2} height={(r + stroke) * 2} style={{ rotate: "-90deg" }}>
            {slices.map((s) => {
              const frac = s.value / total;
              const start = acc;
              acc += frac;
              const visible = Math.max(0, Math.min(frac, sweep - start));
              return (
                <circle key={s.label} cx={r + stroke} cy={r + stroke} r={r} fill="none" stroke={s.color} strokeWidth={stroke}
                  strokeDasharray={`${visible * C} ${C}`} strokeDashoffset={-start * C} />
              );
            })}
          </svg>
          <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <div style={{ fontSize: 90 * u, fontWeight: 900, fontVariantNumeric: "tabular-nums" }}>{Math.round((lead.value / total) * 100 * sweep)}%</div>
            <div style={{ fontSize: 26 * u, fontWeight: 700, color: lead.color }}>{lead.label}</div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 26 * u }}>
          {slices.map((s, i) => {
            const e = enter(frame, 20 + i * 6);
            return (
              <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 18 * u, opacity: e, translate: `${(1 - e) * 24}px 0` }}>
                <div style={{ width: 24 * u, height: 24 * u, borderRadius: 6 * u, background: s.color }} />
                <div style={{ fontSize: 34 * u, fontWeight: 600, minWidth: 260 * u }}>{s.label}</div>
                <div style={{ fontSize: 34 * u, fontWeight: 800, fontVariantNumeric: "tabular-nums" }}>{Math.round((s.value / total) * 100)}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
