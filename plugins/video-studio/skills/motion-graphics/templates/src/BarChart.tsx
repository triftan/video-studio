import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", { weights: ["500", "800"], subsets: ["latin"] });

type Bar = { label: string; value: number };
type Props = { title: string; unit: string; bars: Bar[]; accent: string; /** which bar gets the accent */ highlight?: "max" | "min" };

/** Horizontal bars grow in sequence while their numbers count up; the top value takes the accent. */
export const BarChart: React.FC<Props> = ({ title, unit, bars, accent, highlight = "max" }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const max = Math.max(...bars.map((b) => b.value), 1);
  const best = bars.reduce((a, b) => (highlight === "min" ? b.value < a.value : b.value > a.value) ? b : a, bars[0]);
  const titleIn = spring({ frame, fps, config: { damping: 200 } });
  const rowH = (height * 0.5) / bars.length;

  return (
    <AbsoluteFill style={{ background: "#0B0B0F", fontFamily, padding: `${height * 0.12}px ${width * 0.1}px` }}>
      <div style={{
        fontWeight: 800, fontSize: height * 0.06, color: "#F5F5F7", marginBottom: height * 0.06,
        opacity: titleIn, transform: `translateY(${(1 - titleIn) * 20}px)`,
      }}>
        {title}
      </div>
      {bars.map((bar, i) => {
        const grow = spring({ frame: frame - 10 - i * 6, fps, config: { damping: 22, stiffness: 90 } });
        const shown = Math.round(bar.value * grow);
        const isBest = bar === best;
        return (
          <div key={bar.label} style={{ display: "flex", alignItems: "center", height: rowH, gap: width * 0.02 }}>
            <div style={{ width: width * 0.18, color: "rgba(245,245,247,0.75)", fontWeight: 500, fontSize: height * 0.03 }}>
              {bar.label}
            </div>
            <div style={{ flex: 1, height: rowH * 0.55, background: "rgba(255,255,255,0.06)", borderRadius: 10 }}>
              <div style={{
                height: "100%", width: `${(bar.value / max) * 100 * grow}%`, borderRadius: 10,
                background: isBest ? accent : "rgba(245,245,247,0.35)",
              }} />
            </div>
            <div style={{
              width: width * 0.08, textAlign: "right", fontWeight: 800, fontSize: height * 0.04,
              color: isBest ? accent : "#F5F5F7", opacity: interpolate(grow, [0, 0.2], [0, 1], { extrapolateRight: "clamp" }),
              fontVariantNumeric: "tabular-nums",
            }}>
              {shown}{unit}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
