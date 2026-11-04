import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont as loadSerif } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadSans } from "@remotion/google-fonts/Inter";

const serif = loadSerif("normal", { weights: ["600"], subsets: ["latin"] }).fontFamily;
const sans = loadSans("normal", { weights: ["500"], subsets: ["latin"] }).fontFamily;

type Props = { kicker: string; headline: string; accent: string; background: string };

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

/** Editorial headline: kicker fades in, headline mask-wipes left to right, rule draws underneath. */
export const EditorialReveal: React.FC<Props> = ({ kicker, headline, accent, background }) => {
  const frame = useCurrentFrame();
  const { width, durationInFrames } = useVideoConfig();
  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

  const kickerIn = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: easeOut });
  const wipe = interpolate(frame, [8, 38], [100, 0], { ...clamp, easing: easeOut });
  const rule = interpolate(frame, [30, 60], [0, 1], { ...clamp, easing: easeOut });
  const out = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], clamp);

  return (
    <AbsoluteFill style={{ background, justifyContent: "center", paddingLeft: width * 0.1, opacity: out }}>
      <div style={{
        fontFamily: sans, fontSize: width * 0.014, letterSpacing: "0.32em", textTransform: "uppercase",
        color: accent, opacity: kickerIn, transform: `translateY(${(1 - kickerIn) * 12}px)`, marginBottom: width * 0.012,
      }}>
        {kicker}
      </div>
      <div style={{
        fontFamily: serif, fontWeight: 600, fontSize: width * 0.058, lineHeight: 1.08, color: "#16130F",
        maxWidth: width * 0.75, clipPath: `inset(0 ${wipe}% 0 0)`,
      }}>
        {headline}
      </div>
      <div style={{ height: 3, width: width * 0.22 * rule, background: accent, marginTop: width * 0.018 }} />
    </AbsoluteFill>
  );
};
