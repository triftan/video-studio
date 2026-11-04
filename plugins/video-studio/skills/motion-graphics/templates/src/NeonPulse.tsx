import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Unbounded";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["latin"] });

type Props = { text: string; glow: string };

/** Glowing uppercase text on a dark glass card, with a gentle breathing pulse and a scanline sweep. */
export const NeonPulse: React.FC<Props> = ({ text, glow }) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const exit = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const pulse = 1 + Math.sin((frame / fps) * 5.2) * 0.015;
  const glowStrength = 0.75 + Math.sin((frame / fps) * 5.2) * 0.25;
  const sweep = interpolate(frame % 60, [0, 60], [-20, 120]);

  return (
    <AbsoluteFill style={{
      background: "radial-gradient(ellipse at 50% 40%, #0E1A2B 0%, #04070D 70%)",
      justifyContent: "center", alignItems: "center",
    }}>
      <div style={{
        position: "relative", overflow: "hidden", padding: `${height * 0.04}px ${width * 0.05}px`,
        borderRadius: width * 0.012, background: "rgba(3, 10, 22, 0.64)",
        border: `1px solid ${glow}55`, boxShadow: `0 0 ${40 * glowStrength}px ${glow}33, inset 0 0 30px ${glow}14`,
        opacity: enter * exit, transform: `scale(${(0.92 + enter * 0.08) * pulse})`,
      }}>
        <div style={{
          fontFamily, fontWeight: 800, fontSize: width * 0.05, textTransform: "uppercase", letterSpacing: "0.02em",
          color: "#EAFBFF",
          textShadow: `0 0 ${8 * glowStrength}px ${glow}, 0 0 ${24 * glowStrength}px ${glow}AA, 0 0 ${60 * glowStrength}px ${glow}55`,
        }}>
          {text}
        </div>
        <div style={{
          position: "absolute", top: 0, bottom: 0, left: `${sweep}%`, width: "12%",
          background: `linear-gradient(90deg, transparent, ${glow}22, transparent)`,
        }} />
      </div>
    </AbsoluteFill>
  );
};
