import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", { weights: ["500", "700"], subsets: ["latin"] });

type Props = { name: string; role: string; accent: string };

/** Transparent lower third: accent bar grows, name slides in, role follows; reverses on exit. */
export const LowerThird: React.FC<Props> = ({ name, role, accent }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const ease = Easing.bezier(0.2, 0.8, 0.2, 1);
  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const outStart = durationInFrames - 14;

  const bar = interpolate(frame, [0, 10], [0, 1], { ...clamp, easing: ease })
    * interpolate(frame, [outStart + 6, durationInFrames], [1, 0], clamp);
  const nameIn = interpolate(frame, [4, 16], [0, 1], { ...clamp, easing: ease })
    * interpolate(frame, [outStart, outStart + 8], [1, 0], clamp);
  const roleIn = interpolate(frame, [8, 20], [0, 1], { ...clamp, easing: ease })
    * interpolate(frame, [outStart, outStart + 6], [1, 0], clamp);

  return (
    <AbsoluteFill>
      <div style={{
        position: "absolute", left: width * 0.06, bottom: height * 0.12,
        display: "flex", alignItems: "stretch", gap: width * 0.01, fontFamily,
      }}>
        <div style={{ width: 6, background: accent, transform: `scaleY(${bar})`, transformOrigin: "bottom", borderRadius: 3 }} />
        <div style={{ overflow: "hidden" }}>
          <div style={{
            fontWeight: 700, fontSize: height * 0.05, color: "#FFFFFF", lineHeight: 1.1,
            textShadow: "0 2px 12px rgba(0,0,0,0.55)", opacity: nameIn, transform: `translateX(${(1 - nameIn) * -40}px)`,
          }}>
            {name}
          </div>
          <div style={{
            fontWeight: 500, fontSize: height * 0.028, color: "rgba(255,255,255,0.85)", marginTop: 6,
            textShadow: "0 2px 10px rgba(0,0,0,0.55)", opacity: roleIn, transform: `translateX(${(1 - roleIn) * -30}px)`,
          }}>
            {role}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
