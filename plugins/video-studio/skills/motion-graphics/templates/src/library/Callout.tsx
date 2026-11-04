import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeOut, exit, pop , OverlayProps } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type CalloutProps = OverlayProps & {
  /** target point, 0-1 of frame */ x: number; y: number;
  /** label position, 0-1 of frame */ labelX: number; labelY: number;
  label: string; detail?: string; accent: string; ring: boolean;
};

/** Points at something in the footage: a ring pulses on the target, a line draws to a label. Transparent overlay. */
export const Callout: React.FC<CalloutProps> = ({ size = 1.35, x, y, labelX, labelY, label, detail, accent, ring }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const tx = x * width, ty = y * height, lx = labelX * width, ly = labelY * height;
  const dot = pop(frame, fps);
  const line = interpolate(frame, [6, 20], [0, 1], { ...clamp, easing: easeOut });
  const lab = pop(frame, fps, 16);
  const ringR = 40 * u + ((frame % 30) / 30) * 40 * u;
  const len = Math.hypot(lx - tx, ly - ty);
  const out = exit(frame, durationInFrames);

  return (
    <AbsoluteFill style={{ opacity: out }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {ring && <circle cx={tx} cy={ty} r={ringR} fill="none" stroke={accent} strokeWidth={4 * u} opacity={1 - (frame % 30) / 30} />}
        <circle cx={tx} cy={ty} r={14 * u * dot} fill={accent} stroke="#fff" strokeWidth={4 * u} />
        <line x1={tx} y1={ty} x2={lx} y2={ly} stroke="#fff" strokeWidth={4 * u} strokeDasharray={len} strokeDashoffset={len * (1 - line)} strokeLinecap="round" />
      </svg>
      <div style={{
        position: "absolute", left: lx, top: ly, translate: `${lx < tx ? "-100%" : "0"} -50%`, scale: String(lab),
        background: "#fff", color: "#0E1116", fontFamily: fonts.sans, borderRadius: 14 * u, padding: `${14 * u}px ${20 * u}px`,
        borderLeft: `6px solid ${accent}`, boxShadow: "0 12px 40px rgba(0,0,0,0.3)",
      }}>
        <div style={{ fontWeight: 800, fontSize: 30 * u }}>{label}</div>
        {detail && <div style={{ fontWeight: 500, fontSize: 22 * u, opacity: 0.6 }}>{detail}</div>}
      </div>
    </AbsoluteFill>
  );
};
