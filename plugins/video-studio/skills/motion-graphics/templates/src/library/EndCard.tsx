import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { enter, exit, pop } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type EndCardProps = { headline: string; handle: string; nextLabel: string; nextTitle: string; accent: string; background: string; text: string };

/** YouTube-style end screen: headline, a "watch next" video slot, a subscribe circle and the handle. Full frame. */
export const EndCard: React.FC<EndCardProps> = ({ headline, handle, nextLabel, nextTitle, accent, background, text }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const slot = pop(frame, fps, 8);
  const circle = pop(frame, fps, 14);

  return (
    <AbsoluteFill style={{ background, color: text, fontFamily: fonts.sans, opacity: exit(frame, durationInFrames) }}>
      <div style={{ position: "absolute", top: 110 * u, width: "100%", textAlign: "center", fontWeight: 900, fontSize: 80 * u, letterSpacing: "-0.03em", opacity: enter(frame), translate: `0 ${(1 - enter(frame)) * 20}px` }}>
        {headline}
      </div>
      <div style={{ position: "absolute", top: 330 * u, left: width * 0.14, width: 820 * u, height: 461 * u, borderRadius: 24 * u, border: `4px dashed ${text}55`, background: `${text}0A`, scale: String(slot), display: "flex", flexDirection: "column", justifyContent: "flex-end", padding: 30 * u }}>
        <div style={{ fontSize: 22 * u, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: accent }}>{nextLabel}</div>
        <div style={{ fontSize: 40 * u, fontWeight: 800 }}>{nextTitle}</div>
      </div>
      <div style={{ position: "absolute", top: 390 * u, right: width * 0.14, display: "flex", flexDirection: "column", alignItems: "center", gap: 24 * u, scale: String(circle) }}>
        <div style={{ width: 300 * u, height: 300 * u, borderRadius: 999, border: `6px solid ${accent}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30 * u, fontWeight: 800 }}>
          SUBSCRIBE
        </div>
        <div style={{ fontSize: 32 * u, fontWeight: 700, opacity: 0.8 }}>{handle}</div>
      </div>
    </AbsoluteFill>
  );
};
