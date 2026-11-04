import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });

type Props = { text: string; accent: string; background: string };

/** Word-by-word title: each word springs up from a blur, the last word takes the accent color. */
export const KineticTitle: React.FC<Props> = ({ text, accent, background }) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  const stagger = 4;
  const exitStart = durationInFrames - 10;
  const exit = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.4, 0, 1, 1),
  });

  return (
    <AbsoluteFill style={{ background, justifyContent: "center", alignItems: "center" }}>
      <div style={{
        display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 0.28em",
        maxWidth: width * 0.8, fontFamily, fontWeight: 800, fontSize: width * 0.065,
        lineHeight: 1.05, letterSpacing: "-0.03em", color: "#F5F5F7", opacity: exit,
        transform: `translateY(${(1 - exit) * -30}px)`,
      }}>
        {words.map((word, i) => {
          const s = spring({ frame: frame - i * stagger, fps, config: { damping: 14, stiffness: 170, mass: 0.6 } });
          const blur = interpolate(s, [0, 1], [10, 0]);
          return (
            <span key={i} style={{
              display: "inline-block",
              opacity: interpolate(s, [0, 0.4], [0, 1], { extrapolateRight: "clamp" }),
              transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px) scale(${interpolate(s, [0, 1], [0.9, 1])})`,
              filter: `blur(${blur}px)`,
              color: i === words.length - 1 ? accent : undefined,
            }}>
              {word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
