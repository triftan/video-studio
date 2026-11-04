import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { Corner, enter, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts, Theme } from "../lib/fonts";

export type CtaPopupProps = OverlayProps & Theme & { eyebrow: string; headline: string; button: string; icon: string; position: Corner };

/** Notification-style call-to-action card that springs in, with a button that pulses. Transparent overlay. */
export const CtaPopup: React.FC<CtaPopupProps> = ({ size = 1.35, eyebrow, headline, button, icon, position, accent, text, surface }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const p = pop(frame, fps);
  const pulse = 1 + 0.04 * Math.max(0, Math.sin((frame - 20) / 6));

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 60 * u), display: "flex", alignItems: "center", gap: 22 * u, width: 640 * u, padding: 24 * u, borderRadius: 26 * u,
        background: surface, color: text, fontFamily: fonts.sans, boxShadow: "0 24px 70px rgba(0,0,0,0.3)",
        opacity: Math.min(1, p * 1.4) * exit(frame, durationInFrames), translate: `0 ${(1 - p) * 60 * u}px`,
      }}>
        <div style={{ width: 84 * u, height: 84 * u, borderRadius: 20 * u, background: `${accent}1F`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 44 * u, flexShrink: 0 }}>
          {icon}
        </div>
        <div style={{ flex: 1, opacity: enter(frame, 6) }}>
          <div style={{ fontSize: 18 * u, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: accent }}>{eyebrow}</div>
          <div style={{ fontSize: 30 * u, fontWeight: 800, lineHeight: 1.15 }}>{headline}</div>
        </div>
        <div style={{ background: accent, color: surface, fontWeight: 800, fontSize: 24 * u, padding: `${16 * u}px ${24 * u}px`, borderRadius: 14 * u, scale: String(pulse * enter(frame, 10)), whiteSpace: "nowrap" }}>
          {button}
        </div>
      </div>
    </AbsoluteFill>
  );
};
