import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeOut, enter, exit } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type ChapterCardProps = { number: string; title: string; accent: string; background: string; text: string; transparent: boolean };

/** Section divider: an accent panel wipes across, the big chapter number counts in, the title rises. */
export const ChapterCard: React.FC<ChapterCardProps> = ({ number, title, accent, background, text, transparent }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const wipe = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: easeOut });
  const unwipe = interpolate(frame, [durationInFrames - 12, durationInFrames], [0, 1], { ...clamp, easing: easeOut });
  const out = exit(frame, durationInFrames, 8);

  return (
    <AbsoluteFill style={{ background: transparent ? "transparent" : background }}>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${unwipe * 100}%`, width: `${(wipe - unwipe) * 100}%`, background: accent }} />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: width * 0.1, color: text, fontFamily: fonts.sans, opacity: out }}>
        <div style={{ fontFamily: fonts.display, fontSize: 300 * u, lineHeight: 0.9, opacity: 0.18 + 0.82 * enter(frame, 8), translate: `${(1 - enter(frame, 8, 16)) * -80}px 0` }}>
          {number}
        </div>
        <div style={{ fontWeight: 900, fontSize: 96 * u, letterSpacing: "-0.03em", maxWidth: width * 0.75, opacity: enter(frame, 14), translate: `0 ${(1 - enter(frame, 14)) * 30}px` }}>
          {title}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
