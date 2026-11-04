import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { Corner, enter, exit, place, pop , OverlayProps } from "../lib/anim";
import { fonts, Theme } from "../lib/fonts";

type Slot = { day: number; label: string };
export type WeeklyScheduleProps = OverlayProps & Theme & { title: string; subtitle?: string; days: string[]; slots: Slot[]; position: Corner };

/** Week grid; posts pop into their day one after another. Transparent overlay. */
export const WeeklySchedule: React.FC<WeeklyScheduleProps> = ({ size = 1.35, title, subtitle, days, slots, position, accent, text, surface }) => {
  const frame = useCurrentFrame();
  const { fps, height, durationInFrames } = useVideoConfig();
  const u = (height / 1080) * size;
  const cardIn = pop(frame, fps);
  const col = 92 * u;

  return (
    <AbsoluteFill>
      <div style={{
        ...place(position, 60 * u), padding: 30 * u, borderRadius: 24 * u, background: surface, color: text,
        boxShadow: "0 20px 60px rgba(0,0,0,0.25)", fontFamily: fonts.sans,
        opacity: Math.min(1, cardIn * 1.4) * exit(frame, durationInFrames), scale: String(0.85 + cardIn * 0.15),
      }}>
        <div style={{ fontWeight: 800, fontSize: 32 * u }}>{title}</div>
        {subtitle && <div style={{ fontSize: 20 * u, opacity: 0.55, marginBottom: 18 * u }}>{subtitle}</div>}
        <div style={{ display: "flex", gap: 10 * u }}>
          {days.map((d, i) => {
            const colIn = enter(frame, 6 + i * 2, 10);
            const daySlots = slots.map((s, k) => ({ ...s, k })).filter((s) => s.day === i);
            return (
              <div key={d} style={{ width: col, opacity: colIn }}>
                <div style={{ fontSize: 18 * u, fontWeight: 700, opacity: 0.5, textAlign: "center", marginBottom: 10 * u }}>{d}</div>
                <div style={{ height: 220 * u, borderRadius: 14 * u, background: `${text}0D`, padding: 8 * u, display: "flex", flexDirection: "column", gap: 8 * u }}>
                  {daySlots.map((s) => {
                    const p = pop(frame, fps, 18 + s.k * 6);
                    return (
                      <div key={s.k} style={{
                        background: accent, color: surface, fontSize: 15 * u, fontWeight: 700, borderRadius: 10 * u,
                        padding: `${10 * u}px ${8 * u}px`, scale: String(p), opacity: Math.min(1, p * 2), lineHeight: 1.15,
                      }}>
                        {s.label}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
