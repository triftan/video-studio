import React from "react";
import { AbsoluteFill, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { clamp, easeOut, enter, exit, pop, settle } from "../lib/anim";
import { fonts } from "../lib/fonts";

type Beat = { headline: string; screen?: string; color: string };
export type AppPromoProps = { appName: string; beats: Beat[]; cta: string; background: string; text: string; accent: string; secondsPerBeat: number };

const Phone: React.FC<{ beat: Beat; u: number }> = ({ beat, u }) => (
  <div style={{ width: 380 * u, height: 780 * u, borderRadius: 60 * u, background: "#0A0A0A", padding: 14 * u, boxShadow: "0 40px 100px rgba(0,0,0,0.35)" }}>
    <div style={{ width: "100%", height: "100%", borderRadius: 48 * u, overflow: "hidden", background: beat.color, position: "relative" }}>
      {beat.screen
        ? <Img src={staticFile(beat.screen)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        : (
          <div style={{ padding: 30 * u, paddingTop: 80 * u, display: "flex", flexDirection: "column", gap: 18 * u }}>
            {[0.9, 0.6, 0.75, 0.5, 0.8].map((w, i) => (
              <div key={i} style={{ height: (i === 0 ? 120 : 60) * u, width: `${w * 100}%`, borderRadius: 18 * u, background: "rgba(255,255,255,0.35)" }} />
            ))}
          </div>
        )}
      <div style={{ position: "absolute", top: 14 * u, left: "50%", translate: "-50% 0", width: 110 * u, height: 30 * u, borderRadius: 99, background: "#0A0A0A" }} />
    </div>
  </div>
);

/** App promo: phone mockup in the center swaps screens per beat while headlines slide; ends on the app name + CTA. Full frame. */
export const AppPromo: React.FC<AppPromoProps> = ({ appName, beats, cta, background, text, accent, secondsPerBeat }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  const beatF = Math.round(secondsPerBeat * fps);
  const endStart = beats.length * beatF;
  const phoneIn = settle(frame, fps);

  return (
    <AbsoluteFill style={{ background, fontFamily: fonts.sans, color: text, opacity: exit(frame, durationInFrames) }}>
      {beats.map((b, i) => (
        <Sequence key={i} from={i * beatF} durationInFrames={beatF}>
          <BeatView beat={b} u={u} index={i} accent={accent} />
        </Sequence>
      ))}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-end", paddingRight: 220 * u, pointerEvents: "none" }}>
        <div style={{
          translate: `0 ${(1 - phoneIn) * 300 * u + interpolate(frame, [endStart, endStart + 15], [0, 1200 * u], { ...clamp, easing: easeOut })}px`,
          rotate: `${interpolate(frame, [0, durationInFrames], [-4, 4])}deg`,
        }}>
          <Phone beat={beats[Math.min(beats.length - 1, Math.floor(frame / beatF))]} u={u} />
        </div>
      </AbsoluteFill>
      <Sequence from={endStart}>
        <EndView appName={appName} cta={cta} accent={accent} background={background} u={u} />
      </Sequence>
    </AbsoluteFill>
  );
};

const BeatView: React.FC<{ beat: Beat; u: number; index: number; accent: string }> = ({ beat, u, index, accent }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const e = enter(frame, 0, 12) * exit(frame, durationInFrames, 8);
  return (
    <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 160 * u }}>
      <div style={{ fontSize: 26 * u, fontWeight: 800, color: accent, letterSpacing: "0.1em", opacity: e }}>0{index + 1}</div>
      <div style={{ fontSize: 96 * u, fontWeight: 900, lineHeight: 1.0, letterSpacing: "-0.03em", maxWidth: 900 * u, opacity: e, translate: `${(1 - e) * -60}px 0` }}>
        {beat.headline}
      </div>
    </AbsoluteFill>
  );
};

const EndView: React.FC<{ appName: string; cta: string; accent: string; background: string; u: number }> = ({ appName, cta, accent, background, u }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, 6);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 30 * u }}>
      <div style={{ fontSize: 140 * u, fontWeight: 900, letterSpacing: "-0.04em", scale: String(p) }}>{appName}</div>
      <div style={{ background: accent, color: background, fontWeight: 800, fontSize: 40 * u, padding: `${18 * u}px ${44 * u}px`, borderRadius: 999, opacity: enter(frame, 14) }}>
        {cta}
      </div>
    </AbsoluteFill>
  );
};
