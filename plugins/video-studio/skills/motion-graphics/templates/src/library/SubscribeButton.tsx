import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, Corner, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts } from "../lib/fonts";

export type SubscribeButtonProps = OverlayProps & {
  channel: string; avatarText: string; buttonColor: string; doneColor: string; position: Corner; clickSecond: number;
};

/** Channel chip + subscribe button; a cursor glides in, clicks, the button flips to Subscribed and a bell rings. Transparent. */
export const SubscribeButton: React.FC<SubscribeButtonProps> = ({ size = 1.35, channel, avatarText, buttonColor, doneColor, position, clickSecond }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const inP = pop(frame, fps);
  const click = Math.round(clickSecond * fps);
  const cursorT = interpolate(frame, [click - 18, click - 2], [0, 1], clamp);
  const press = interpolate(frame, [click - 2, click, click + 4], [1, 0.9, 1], clamp);
  const subscribed = frame >= click;
  const bell = subscribed ? Math.sin((frame - click) / 2) * interpolate(frame, [click, click + 24], [18, 0], clamp) : 0;

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 70 * u), display: "flex", alignItems: "center", gap: 18 * u, padding: `${14 * u}px ${16 * u}px ${14 * u}px ${14 * u}px`,
        borderRadius: 999, background: "rgba(15,15,15,0.85)", fontFamily: fonts.sans, color: "#fff",
        opacity: Math.min(1, inP * 1.4) * exit(frame, durationInFrames), scale: String(0.7 + inP * 0.3),
      }}>
        <div style={{ width: 64 * u, height: 64 * u, borderRadius: 99, background: "linear-gradient(135deg,#FF8A00,#FF2E63)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 26 * u }}>
          {avatarText}
        </div>
        <div style={{ fontWeight: 700, fontSize: 28 * u, marginRight: 8 * u }}>{channel}</div>
        <div style={{ position: "relative" }}>
          <div style={{
            background: subscribed ? doneColor : buttonColor, color: subscribed ? "#fff" : "#fff", fontWeight: 800, fontSize: 26 * u,
            padding: `${14 * u}px ${28 * u}px`, borderRadius: 999, scale: String(press), display: "flex", alignItems: "center", gap: 10 * u,
          }}>
            {subscribed ? "Subscribed" : "Subscribe"}
            {subscribed && <span style={{ display: "inline-block", rotate: `${bell}deg`, transformOrigin: "50% 10%" }}>🔔</span>}
          </div>
          <svg width={40 * u} height={40 * u} viewBox="0 0 24 24" style={{
            position: "absolute", left: interpolate(cursorT, [0, 1], [220, 60]) * u, top: interpolate(cursorT, [0, 1], [120, 30]) * u,
            opacity: interpolate(frame, [click - 18, click - 12, click + 14, click + 20], [0, 1, 1, 0], clamp), scale: String(press),
          }}>
            <path d="M4 2l16 9-7 2-3 7z" fill="#fff" stroke="#000" strokeWidth={1.5} strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </AbsoluteFill>
  );
};
