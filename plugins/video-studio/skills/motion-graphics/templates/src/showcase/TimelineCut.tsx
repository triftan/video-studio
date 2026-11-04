import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeOut, enter, fmt, pop } from "../lib/anim";
import { fonts } from "../lib/fonts";

type Seg = { text: string; cut?: "filler" | "pause" | "retake"; w: number };

// One spoken line split into transcript chips; flagged chips get cut.
const SEGS: Seg[] = [
  { text: "So", w: 2 }, { text: "um,", cut: "filler", w: 3 }, { text: "the", w: 3 }, { text: "trick", w: 4 },
  { text: "…", cut: "pause", w: 6 }, { text: "the trick is", cut: "retake", w: 9 }, { text: "the trick is", w: 9 },
  { text: "uh,", cut: "filler", w: 3 }, { text: "to", w: 2 }, { text: "cut", w: 3 }, { text: "…", cut: "pause", w: 7 },
  { text: "fast.", w: 4 },
];
const COLORS = { bg: "#0B0B0F", panel: "#15161C", text: "#F5F5F7", muted: "#8A8F98", accent: "#4DFFDF", cut: "#FF4D6D" };
const TAG: Record<NonNullable<Seg["cut"]>, string> = { filler: "filler", pause: "pause", retake: "retake" };

/**
 * Showcase scene for the video-editing skill: a playhead scans the transcript, flags fillers, pauses and
 * retakes, then the flagged pieces collapse out of both the transcript and the timeline.
 */
export const TimelineCut: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const u = height / 1080;
  const total = SEGS.reduce((s, x) => s + x.w, 0);
  const kept = SEGS.filter((s) => !s.cut).reduce((s, x) => s + x.w, 0);
  const scanStart = 12, scanEnd = 78, cutStart = 92, cutEnd = 122;
  const scan = interpolate(frame, [scanStart, scanEnd], [0, 1], clamp);
  const collapse = interpolate(frame, [cutStart, cutEnd], [0, 1], { ...clamp, easing: easeOut });
  const trackW = width * 0.84;
  const unit = trackW / total;
  const saved = Math.round((1 - kept / total) * 100);
  const statIn = pop(frame, fps, cutEnd - 4);

  let acc = 0;
  const pieces = SEGS.map((s) => {
    const x0 = acc / total;
    acc += s.w;
    const flagged = !!s.cut && scan >= (x0 + s.w / total / 2);
    const w = s.cut ? s.w * (1 - collapse) : s.w;
    return { ...s, x0, flagged, w };
  });
  const liveTotal = pieces.reduce((s, p) => s + p.w, 0);

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 0%, #13233A 0%, ${COLORS.bg} 60%)`, fontFamily: fonts.sans, color: COLORS.text }}>
      <div style={{ position: "absolute", left: width * 0.08, top: 120 * u, opacity: enter(frame), fontSize: 26 * u, letterSpacing: "0.2em", textTransform: "uppercase", color: COLORS.accent, fontFamily: fonts.mono }}>
        transcript
      </div>
      {/* transcript chips */}
      <div style={{ position: "absolute", left: width * 0.08, top: 170 * u, width: trackW, display: "flex", flexWrap: "nowrap", gap: 0, alignItems: "center", height: 90 * u }}>
        {pieces.map((p, i) => {
          const visibleW = (p.w / liveTotal) * trackW;
          const red = p.flagged;
          return (
            <div key={i} style={{ width: visibleW, overflow: "hidden", flexShrink: 0, opacity: enter(frame, 2 + i, 8) * (p.cut ? 1 - collapse * 0.9 : 1) }}>
              <div style={{
                margin: `0 ${4 * u}px`, padding: `${12 * u}px ${10 * u}px`, borderRadius: 12 * u, textAlign: "center", whiteSpace: "nowrap",
                fontSize: 30 * u, fontWeight: 700, background: red ? `${COLORS.cut}26` : COLORS.panel,
                border: `2px solid ${red ? COLORS.cut : "rgba(255,255,255,0.08)"}`, color: red ? COLORS.cut : COLORS.text,
                textDecoration: red ? "line-through" : "none", position: "relative",
              }}>
                {p.text}
                {red && p.cut && (
                  <div style={{ position: "absolute", top: -26 * u, left: "50%", translate: "-50% 0", fontFamily: fonts.mono, fontSize: 15 * u, color: COLORS.cut, scale: String(pop(frame, fps, scanStart + (scanEnd - scanStart) * (p.x0 + 0.02))) }}>
                    {TAG[p.cut]}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      {/* timeline */}
      <div style={{ position: "absolute", left: width * 0.08, top: 380 * u, fontSize: 26 * u, letterSpacing: "0.2em", textTransform: "uppercase", color: COLORS.accent, fontFamily: fonts.mono, opacity: enter(frame, 6) }}>
        timeline
      </div>
      {["V1", "A1"].map((track, ti) => (
        <div key={track} style={{ position: "absolute", left: width * 0.08, top: (430 + ti * 150) * u, width: trackW, height: 130 * u, display: "flex", opacity: enter(frame, 8 + ti * 3) }}>
          {pieces.map((p, i) => {
            const w = (p.w / liveTotal) * trackW * (1 - 0) ;
            const red = p.flagged;
            return (
              <div key={i} style={{ width: w, height: "100%", flexShrink: 0, padding: `0 ${2 * u}px`, boxSizing: "border-box" }}>
                <div style={{
                  height: "100%", borderRadius: 10 * u, overflow: "hidden", position: "relative",
                  background: red ? `${COLORS.cut}33` : ti === 0 ? "linear-gradient(180deg,#2B4C7E,#1B2F4F)" : "linear-gradient(180deg,#1E5A52,#123A35)",
                  border: `2px solid ${red ? COLORS.cut : "rgba(255,255,255,0.08)"}`,
                }}>
                  {ti === 1 && (
                    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", gap: 3 * u, padding: `0 ${6 * u}px` }}>
                      {Array.from({ length: Math.max(1, Math.round(p.w * 2.2)) }).map((_, k) => {
                        const amp = p.cut === "pause" ? 0.05 : 0.2 + random(`w${i}-${k}`) * 0.75;
                        return <div key={k} style={{ flex: 1, height: `${amp * 90}%`, borderRadius: 3, background: red ? COLORS.cut : COLORS.accent, opacity: 0.85 }} />;
                      })}
                    </div>
                  )}
                  {ti === 0 && <div style={{ position: "absolute", left: 8 * u, top: 8 * u, fontSize: 15 * u, fontFamily: fonts.mono, color: "rgba(255,255,255,0.55)" }}>{p.cut ? "" : "cam_A.mp4"}</div>}
                </div>
              </div>
            );
          })}
        </div>
      ))}
      {/* playhead */}
      {frame < cutStart + 4 && (
        <div style={{ position: "absolute", left: width * 0.08 + scan * trackW, top: 160 * u, width: 4 * u, height: 580 * u, background: COLORS.accent, boxShadow: `0 0 24px ${COLORS.accent}`, opacity: interpolate(frame, [scanStart, scanStart + 4, cutStart, cutStart + 4], [0, 1, 1, 0], clamp) }} />
      )}
      {/* result */}
      <div style={{ position: "absolute", right: width * 0.08, top: 770 * u, display: "flex", alignItems: "baseline", gap: 18 * u, scale: String(statIn), opacity: Math.min(1, statIn * 1.5) }}>
        <div style={{ fontSize: 96 * u, fontWeight: 900, color: COLORS.accent, fontVariantNumeric: "tabular-nums" }}>−{fmt(Math.round(saved * Math.min(1, statIn)))}%</div>
        <div style={{ fontSize: 30 * u, color: COLORS.muted, fontWeight: 600 }}>runtime, same story</div>
      </div>
    </AbsoluteFill>
  );
};
