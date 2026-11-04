import { loadFont as inter } from "@remotion/google-fonts/Inter";
import { loadFont as mono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as serif } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as display } from "@remotion/google-fonts/Anton";
import { loadFont as special } from "@remotion/google-fonts/SpecialElite";

export const fonts = {
  sans: inter("normal", { weights: ["500", "700", "800", "900"], subsets: ["latin"] }).fontFamily,
  mono: mono("normal", { weights: ["500", "700"], subsets: ["latin"] }).fontFamily,
  serif: serif("normal", { weights: ["600", "800"], subsets: ["latin"] }).fontFamily,
  display: display("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
  typewriter: special("normal", { weights: ["400"], subsets: ["latin"] }).fontFamily,
};

/** Common theme props every library template accepts. */
export type Theme = { accent: string; text: string; surface: string };
export const defaultTheme: Theme = { accent: "#3D7BFF", text: "#0E1116", surface: "#FFFFFF" };
