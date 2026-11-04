import React from "react";
import { Composition, Folder } from "remotion";
import { KineticTitle } from "./KineticTitle";
import { EditorialReveal } from "./EditorialReveal";
import { NeonPulse } from "./NeonPulse";
import { LowerThird } from "./LowerThird";
import { BarChart } from "./BarChart";
import { LogoReveal } from "./LogoReveal";
import { PresetCaptions } from "./PresetCaptions";
import { Explainer, calculateExplainerMetadata } from "./Explainer";
import { LIBRARY, LIBRARY_COMPONENTS } from "./library";
import { AiVideoEditing } from "./showcase/AiVideoEditing";
import { CaptionStyles, DesignStyles } from "./showcase/CompanionVideos";
import { showMetadata } from "./showcase/common";
import { StylePreview } from "./StylePreview";

const HD = { width: 1920, height: 1080, fps: 30 };
const VERTICAL = { width: 1080, height: 1920, fps: 30 };

export const Root: React.FC = () => (
  <>
    <Composition id="KineticTitle" component={KineticTitle} durationInFrames={90} {...HD}
      defaultProps={{ text: "Make every frame count", accent: "#FF4D2E", background: "#0B0B0F" }} />
    <Composition id="EditorialReveal" component={EditorialReveal} durationInFrames={120} {...HD}
      defaultProps={{ kicker: "Chapter one", headline: "The quiet art of the cut", accent: "#C8A96A", background: "#F4F1EA" }} />
    <Composition id="NeonPulse" component={NeonPulse} durationInFrames={90} {...HD}
      defaultProps={{ text: "Level up your edits", glow: "#4DFFDF" }} />
    <Composition id="LowerThird" component={LowerThird} durationInFrames={150} {...HD}
      defaultProps={{ name: "Alex Rivera", role: "Founder, Northwind", accent: "#3D7BFF" }} />
    <Composition id="BarChart" component={BarChart} durationInFrames={120} {...HD}
      defaultProps={{
        title: "Watch time after editing",
        unit: "%",
        bars: [
          { label: "Raw", value: 31 },
          { label: "Cut silences", value: 52 },
          { label: "+ Captions", value: 68 },
          { label: "+ Zooms & B-roll", value: 81 },
        ],
        accent: "#3D7BFF",
      }} />
    <Composition id="LogoReveal" component={LogoReveal} durationInFrames={90} {...HD}
      defaultProps={{ brand: "NORTHWIND", tagline: "Built for creators", accent: "#FF4D2E" }} />
    <Composition id="PresetCaptions" component={PresetCaptions} durationInFrames={105} {...VERTICAL}
      defaultProps={{ preset: "tiktok", wordsUrl: "words.json" }} />
    <Composition id="Explainer" component={Explainer} calculateMetadata={calculateExplainerMetadata}
      durationInFrames={300} {...HD} defaultProps={{ storyboardUrl: "storyboard.json" }} />
    <Folder name="Library">
      {LIBRARY.map((t) => (
        <Composition key={t.id} id={t.id} component={LIBRARY_COMPONENTS[t.id]} durationInFrames={Math.round(t.seconds * 30)}
          {...HD} defaultProps={t.props} />
      ))}
    </Folder>
    {/* One-frame look preview used by the style-advisor skill: render with `remotion still --frame=40` */}
    <Composition id="StylePreview" component={StylePreview} durationInFrames={60} {...HD}
      defaultProps={{ style: "edu-chalk", captionPreset: "plain", title: "The water cycle", subtitle: "How rain gets back to the sky", caption: "Water never really disappears, it just moves", tag: "Option A" }} />
    <Composition id="StylePreviewVertical" component={StylePreview} durationInFrames={60} {...VERTICAL}
      defaultProps={{ style: "bold-creator", captionPreset: "tiktok", title: "3 study hacks", subtitle: "that actually work", caption: "Number one will change how you study", tag: "Option A" }} />
    {/* Showcase videos: run showcase/build_showcase.py first to create public/showcase/*.json */}
    <Folder name="Showcase">
      <Composition id="ShowcaseAiVideoEditing" component={AiVideoEditing} calculateMetadata={showMetadata(1920, 1080)}
        durationInFrames={300} {...HD} defaultProps={{ dataUrl: "showcase/main.json" }} />
      <Composition id="ShowcaseCaptionStyles" component={CaptionStyles} calculateMetadata={showMetadata(1080, 1920)}
        durationInFrames={300} {...VERTICAL} defaultProps={{ dataUrl: "showcase/captions.json" }} />
      <Composition id="ShowcaseDesignStyles" component={DesignStyles} calculateMetadata={showMetadata(1920, 1080)}
        durationInFrames={300} {...HD} defaultProps={{ dataUrl: "showcase/styles.json" }} />
    </Folder>
  </>
);
