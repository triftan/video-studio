import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, Corner, easeOut, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type SocialHandleProps = OverlayProps & { platform: "instagram" | "tiktok" | "youtube" | "x"; handle: string; position: Corner };

const BRAND: Record<SocialHandleProps["platform"], { bg: string; glyph: string }> = {
  instagram: { bg: "linear-gradient(45deg,#F58529,#DD2A7B,#8134AF)", glyph: "◎" },
  tiktok: { bg: "linear-gradient(45deg,#25F4EE,#000 50%,#FE2C55)", glyph: "♪" },
  youtube: { bg: "#FF0000", glyph: "▶" },
  x: { bg: "#000", glyph: "𝕏" },
};

/** Icon pops, then a pill unrolls with the handle. Transparent watermark-style overlay. */
export const SocialHandle: React.FC<SocialHandleProps> = ({ size = 1.35, platform, handle, position }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const icon = pop(frame, fps);
  const unroll = interpolate(frame, [8, 22], [0, 1], { ...clamp, easing: easeOut });
  const b = BRAND[platform];

  return (
    <AbsoluteFill>
      <div style={{ ...place(position, 60 * u), display: "flex", alignItems: "center", opacity: exit(frame, durationInFrames), fontFamily: fonts.sans }}>
        <div style={{ zIndex: 1, width: 72 * u, height: 72 * u, borderRadius: 20 * u, background: b.bg, color: "#fff", fontSize: 36 * u, display: "flex", alignItems: "center", justifyContent: "center", scale: String(icon), boxShadow: "0 10px 30px rgba(0,0,0,0.3)" }}>
          {b.glyph}
        </div>
        <div style={{ marginLeft: -24 * u, paddingLeft: 40 * u, paddingRight: 26 * u, height: 58 * u, display: "flex", alignItems: "center", borderRadius: `0 ${999}px ${999}px 0`, background: "rgba(255,255,255,0.95)", color: "#111", fontWeight: 800, fontSize: 28 * u, clipPath: `inset(0 ${(1 - unroll) * 100}% 0 0)` }}>
          {handle}
        </div>
      </div>
    </AbsoluteFill>
  );
};
