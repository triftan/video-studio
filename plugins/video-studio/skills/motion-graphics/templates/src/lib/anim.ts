import type React from "react";
import { Easing, interpolate, spring } from "remotion";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const easeOut = Easing.bezier(0.2, 0.8, 0.2, 1);
export const easeIn = Easing.bezier(0.4, 0, 1, 1);

/** 0 -> 1 over `dur` frames starting at `start`, eased out. */
export const enter = (frame: number, start = 0, dur = 12) =>
  interpolate(frame, [start, start + dur], [0, 1], { ...clamp, easing: easeOut });

/** 1 -> 0 over the last `dur` frames of a clip. */
export const exit = (frame: number, total: number, dur = 10) =>
  interpolate(frame, [total - dur, total], [1, 0], { ...clamp, easing: easeIn });

/** Springy 0 -> 1 (with a little overshoot) starting at `start`. */
export const pop = (frame: number, fps: number, start = 0) =>
  spring({ frame: frame - start, fps, config: { damping: 12, stiffness: 180, mass: 0.6 } });

/** Calm 0 -> 1 spring, no overshoot. */
export const settle = (frame: number, fps: number, start = 0) =>
  spring({ frame: frame - start, fps, config: { damping: 200 } });

/** Format a number with thousands separators and fixed decimals. */
export const fmt = (n: number, decimals = 0) =>
  n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

export type Corner = "top-left" | "top-right" | "bottom-left" | "bottom-right" | "center";

/** Absolute placement for an overlay card inside a safe margin. */
export const place = (corner: Corner, margin: number): React.CSSProperties => {
  const s: React.CSSProperties = { position: "absolute" };
  if (corner === "center") return { ...s, left: "50%", top: "50%", transform: "translate(-50%, -50%)" };
  if (corner.startsWith("top")) s.top = margin; else s.bottom = margin;
  if (corner.endsWith("left")) s.left = margin; else s.right = margin;
  return s;
};

/** Props shared by overlay templates. size scales the whole card (1 = authored at 1080p). */
export type OverlayProps = { size?: number };
