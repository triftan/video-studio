import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, enter, exit } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type QuoteCardProps = { quote: string; author: string; role?: string; accent: string; background: string; text: string };

/** Pull quote: words fade up in reading order, author slides in with an accent rule. Full frame. */
export const QuoteCard: React.FC<QuoteCardProps> = ({ quote, author, role, accent, background, text }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const words = quote.split(/\s+/);
  const authorAt = 10 + words.length * 2 + 6;

  return (
    <AbsoluteFill style={{ background, color: text, justifyContent: "center", padding: `0 ${width * 0.12}px`, opacity: exit(frame, durationInFrames) }}>
      <div style={{ fontFamily: fonts.serif, fontSize: 240 * u, lineHeight: 0.6, color: accent, opacity: enter(frame), height: 120 * u }}>&ldquo;</div>
      <div style={{ fontFamily: fonts.serif, fontWeight: 600, fontSize: 76 * u, lineHeight: 1.18, display: "flex", flexWrap: "wrap", gap: `0 ${0.28}em` }}>
        {words.map((w, i) => {
          const e = enter(frame, 10 + i * 2, 10);
          return <span key={i} style={{ opacity: e, translate: `0 ${(1 - e) * 16}px` }}>{w}</span>;
        })}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 20 * u, marginTop: 50 * u, fontFamily: fonts.sans }}>
        <div style={{ height: 4 * u, width: interpolate(frame, [authorAt, authorAt + 12], [0, 70 * u], clamp), background: accent }} />
        <div style={{ opacity: enter(frame, authorAt + 4) }}>
          <div style={{ fontWeight: 800, fontSize: 34 * u }}>{author}</div>
          {role && <div style={{ fontWeight: 500, fontSize: 24 * u, opacity: 0.6 }}>{role}</div>}
        </div>
      </div>
    </AbsoluteFill>
  );
};
