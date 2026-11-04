import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, exit } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type StampTitleProps = { kicker: string; title: string; stamp: string; paper: string; ink: string; stampColor: string };

/** Case-file title card: kicker types on, title slams in, a rubber stamp thuds down. Full frame. */
export const StampTitle: React.FC<StampTitleProps> = ({ kicker, title, stamp, paper, ink, stampColor }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const typed = Math.floor(interpolate(frame, [4, 4 + kicker.length * 1.5], [0, kicker.length], clamp));
  const slam = interpolate(frame, [20, 28], [1.6, 1], clamp);
  const slamO = interpolate(frame, [20, 24], [0, 1], clamp);
  const stampT = 40;
  const stampS = interpolate(frame, [stampT, stampT + 6], [2.2, 1], clamp);
  const stampO = interpolate(frame, [stampT, stampT + 3], [0, 0.9], clamp);
  const shake = frame >= stampT + 6 && frame < stampT + 12 ? (random(`s${frame}`) - 0.5) * 10 * u : 0;
  const caret = frame % 16 < 8 && typed < kicker.length;

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(ellipse at center, ${paper} 55%, #00000033 130%), ${paper}`,
      justifyContent: "center", alignItems: "center", opacity: exit(frame, durationInFrames),
      translate: `${shake}px ${shake * 0.6}px`,
    }}>
      <div style={{ position: "relative", textAlign: "center", color: ink }}>
        <div style={{ fontFamily: fonts.typewriter, fontSize: 34 * u, letterSpacing: "0.2em", marginBottom: 24 * u, minHeight: 44 * u }}>
          {kicker.slice(0, typed)}{caret ? "▍" : ""}
        </div>
        <div style={{ fontFamily: fonts.display, fontSize: 170 * u, lineHeight: 0.95, textTransform: "uppercase", maxWidth: width * 0.8, scale: String(slam), opacity: slamO }}>
          {title}
        </div>
        <div style={{
          position: "absolute", right: -90 * u, bottom: -140 * u, rotate: "-12deg", scale: String(stampS), opacity: stampO,
          fontFamily: fonts.display, fontSize: 64 * u, color: stampColor, border: `6px solid ${stampColor}`,
          padding: `${4 * u}px ${22 * u}px`, borderRadius: 10 * u, letterSpacing: "0.08em", mixBlendMode: "multiply",
        }}>
          {stamp}
        </div>
      </div>
    </AbsoluteFill>
  );
};
