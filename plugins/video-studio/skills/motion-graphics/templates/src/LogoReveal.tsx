import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", { weights: ["500", "900"], subsets: ["latin"] });

type Props = { brand: string; tagline: string; accent: string; logoSrc?: string };

/**
 * Logo reveal: mark scales in with a soft overshoot, a light sweep crosses the wordmark,
 * tagline rises in. Pass logoSrc (e.g. staticFile("logo.png")) to use an image instead of text.
 */
export const LogoReveal: React.FC<Props> = ({ brand, tagline, accent, logoSrc }) => {
  const frame = useCurrentFrame();
  const { fps, width, durationInFrames } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 11, stiffness: 140, mass: 0.7 } });
  const sweep = interpolate(frame, [14, 40], [-30, 130], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tag = spring({ frame: frame - 22, fps, config: { damping: 200 } });
  const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#0B0B0F", justifyContent: "center", alignItems: "center", fontFamily, opacity: out }}>
      <div style={{ position: "relative", overflow: "hidden", transform: `scale(${0.6 + pop * 0.4})`, opacity: Math.min(1, pop * 1.5) }}>
        {logoSrc ? (
          <img src={logoSrc} style={{ height: width * 0.1 }} />
        ) : (
          <div style={{ fontWeight: 900, fontSize: width * 0.085, letterSpacing: "0.04em", color: "#F5F5F7" }}>{brand}</div>
        )}
        <div style={{
          position: "absolute", top: 0, bottom: 0, left: `${sweep}%`, width: "25%", transform: "skewX(-20deg)",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent)", mixBlendMode: "overlay",
        }} />
      </div>
      <div style={{ height: 4, width: width * 0.06 * tag, background: accent, margin: `${width * 0.012}px 0`, borderRadius: 2 }} />
      <div style={{
        fontWeight: 500, fontSize: width * 0.018, letterSpacing: "0.3em", textTransform: "uppercase",
        color: "rgba(245,245,247,0.8)", opacity: tag, transform: `translateY(${(1 - tag) * 16}px)`,
      }}>
        {tagline}
      </div>
    </AbsoluteFill>
  );
};
