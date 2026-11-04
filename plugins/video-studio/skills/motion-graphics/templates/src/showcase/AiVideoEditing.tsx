import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Backdrop, FakeFootage, Mini, MusicBed, SceneSeries, ShowLabel, ShowProps, ShowScene } from "./common";
import { TimelineCut } from "./TimelineCut";
import { PresetCaptions } from "../PresetCaptions";
import { KineticTitle } from "../KineticTitle";
import { EditorialReveal } from "../EditorialReveal";
import { NeonPulse } from "../NeonPulse";
import { LowerThird } from "../LowerThird";
import { BarChart } from "../BarChart";
import { LogoReveal } from "../LogoReveal";
import { SceneView, StyleFonts, resolveStyle, Scene as ExplainerScene } from "../Explainer";
import { StampTitle } from "../library/StampTitle";
import { LoadingBar } from "../library/LoadingBar";
import { NumberCounter } from "../library/NumberCounter";
import { Callout } from "../library/Callout";
import { SocialHandle } from "../library/SocialHandle";
import { Checklist } from "../library/Checklist";
import { WeeklySchedule } from "../library/WeeklySchedule";
import { ChapterCard } from "../library/ChapterCard";
import { LineChart } from "../library/LineChart";
import { DonutChart } from "../library/DonutChart";
import { QuoteCard } from "../library/QuoteCard";
import { AppPromo } from "../library/AppPromo";
import { Countdown } from "../library/Countdown";
import { EndCard } from "../library/EndCard";
import { SubscribeButton } from "../library/SubscribeButton";
import { CtaPopup } from "../library/CtaPopup";

const ILLUSTRATIVE: [string, string] = ["Data", "illustrative"];
const LIGHT = { accent: "#3D7BFF", text: "#0E1116", surface: "#FFFFFF" };
const STYLE_KEYS = ["clean-saas", "dark-tech", "editorial", "playful-pop", "corporate-trust", "warm-story", "bold-creator", "edu-chalk"];

/** Captions for a scene, in a given preset, near the bottom of the frame. */
const Cap: React.FC<{ s: ShowScene; preset: string; y?: number }> = ({ s, preset, y = 0.9 }) => (
  <PresetCaptions preset={preset} words={s.words} y={y} wordsPerPage={6} />
);

/** Time a sub-sequence to the moment a word is spoken. */
const at = (s: ShowScene, word: string, fps: number, fallback = 0) => {
  const w = s.words.find((x) => x.text.toLowerCase().replace(/[^a-z]/g, "") === word);
  return w ? Math.round(w.start * fps) : fallback;
};

const Scene: React.FC<{ s: ShowScene }> = ({ s }) => {
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const u = height / 1080;
  switch (s.id) {
    case "hook":
      return (<>
        <StampTitle kicker="CASE FILE #001" title="The 4-hour edit" stamp="SOLVED" paper="#EFE6D2" ink="#1D1A16" stampColor="#C0392B" />
        <ShowLabel dark={false} items={[["Template", "StampTitle"], ["Skill", "motion-graphics"]]} />
      </>);
    case "kinetic":
      return (<>
        <KineticTitle text="AI changed the math" accent="#4DFFDF" background="#0B0B0F" />
        <ShowLabel items={[["Template", "KineticTitle"]]} />
      </>);
    case "timeline":
      return (<>
        <TimelineCut />
        <Cap s={s} preset="signal" y={0.95} />
        <ShowLabel items={[["Scene", "TimelineCut (custom)"], ["Skill", "video-editing"], ["Captions", "signal"]]} />
      </>);
    case "polish":
      return (<>
        <Backdrop colors={["#1B3A6B", "#4DFFDF", "#7C5CFF"]} base="#0B0B0F" />
        <LoadingBar {...LIGHT} accent="#14C38E" position="center" size={1.6} fillSeconds={3}
          stages={["Tightening pacing…", "Cleaning audio…", "Adding captions…", "Rendering preview…"]} doneLabel="Edit ready" />
        <NumberCounter {...LIGHT} accent="#14C38E" value={47} from={0} decimals={0} label="pauses removed" trend="−2:31" position="top-right" countSeconds={2.2} />
        <Cap s={s} preset="tiktok" y={0.93} />
        <ShowLabel items={[["Templates", "LoadingBar + NumberCounter"], ["Captions", "tiktok"], ILLUSTRATIVE]} />
      </>);
    case "captions": {
      const presets = ["tiktok", "submagic", "netflix", "bubble-pop", "luxe", "signal"];
      const tileW = width * 0.28, tileH = tileW * 9 / 16, sc = tileW / width;
      return (<>
        <Backdrop colors={["#2B1B4F", "#FF4D8D", "#3D7BFF"]} base="#0D0B14" />
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ display: "grid", gridTemplateColumns: `repeat(3, ${tileW}px)`, gap: 36 * u, marginTop: 40 * u }}>
            {presets.map((p) => (
              <div key={p}>
                <Mini w={tileW} h={tileH} scale={sc}>
                  <FakeFootage />
                  <PresetCaptions preset={p} words={s.words} y={0.8} wordsPerPage={p === "submagic" ? 2 : 3} scale={2} />
                </Mini>
                <div style={{ marginTop: 10 * u, fontFamily: "monospace", fontSize: 20 * u, color: "rgba(255,255,255,0.75)", textAlign: "center" }}>{p}</div>
              </div>
            ))}
          </div>
        </AbsoluteFill>
        <ShowLabel items={[["Template", "PresetCaptions × 6"], ["Styles", "caption-presets.json"]]} />
      </>);
    }
    case "workflow": {
      const style = resolveStyle("clean-saas");
      const sc: ExplainerScene = { id: "steps", type: "steps", title: "How it works", items: ["Upload your footage", "Describe the edit", "Review and export"] };
      return (<>
        <StyleFonts style={style} />
        <SceneView scene={sc} style={style} />
        <Cap s={s} preset="studio" y={0.92} />
        <ShowLabel dark={false} items={[["Template", "Explainer · steps"], ["Style", "clean-saas"], ["Captions", "studio"]]} />
      </>);
    }
    case "overlays":
      return (<>
        <FakeFootage />
        <LowerThird name="Maya Chen" role="Creator · edits with AI" accent="#FF4D8D" />
        <Sequence from={at(s, "callouts", fps, 60)} layout="none">
          <Callout x={0.5} y={0.42} labelX={0.22} labelY={0.3} label="Auto-framed" detail="face tracking zoom" accent="#FF4D8D" ring size={1.2} />
        </Sequence>
        <Sequence from={at(s, "handle", fps, 100)} layout="none">
          <SocialHandle platform="tiktok" handle="@maya.edits" position="top-right" size={1.2} />
        </Sequence>
        <ShowLabel items={[["Templates", "LowerThird + Callout + SocialHandle"], ["Over", "footage"]]} />
      </>);
    case "plan":
      return (<>
        <Backdrop colors={["#E8D9B5", "#F4C7A1", "#C8A96A"]} base="#F4F1EA" />
        <Checklist {...LIGHT} accent="#C0392B" title="Shoot list" tag="FILM → EDIT" items={["Hook: the 4-hour edit", "Demo the timeline", "Show 3 caption styles", "Call to action"]} position="top-left" secondsPerItem={0.7} size={1.25} />
        <WeeklySchedule {...LIGHT} accent="#C0392B" title="Posting plan" subtitle="This week" days={["Mon", "Tue", "Wed", "Thu", "Fri"]}
          slots={[{ day: 0, label: "Full video" }, { day: 1, label: "Short #1" }, { day: 3, label: "Short #2" }, { day: 4, label: "Behind the scenes" }]} position="bottom-right" size={1.25} />
        <ShowLabel dark={false} items={[["Templates", "Checklist + WeeklySchedule"]]} />
      </>);
    case "chapter2":
      return (<>
        <ChapterCard number="02" title="What changes" accent="#4DFFDF" background="#0B0B0F" text="#0B0B0F" transparent={false} />
        <ShowLabel dark={false} items={[["Template", "ChapterCard"]]} />
      </>);
    case "line":
      return (<>
        <LineChart title="Average view duration (sec)" unit="s" accent="#7C5CFF" background="#0B0B0F" text="#F5F5F7"
          points={[{ label: "Raw", value: 38 }, { label: "Cuts", value: 52 }, { label: "Captions", value: 61 }, { label: "Zooms", value: 70 }, { label: "B-roll", value: 84 }]} />
        <ShowLabel items={[["Template", "LineChart"], ILLUSTRATIVE]} />
      </>);
    case "donut":
      return (<>
        <DonutChart title="Where editing time goes" background="#F7F8FA" text="#0E1116" slices={[
          { label: "Cutting & trimming", value: 38, color: "#3D7BFF" }, { label: "Captions", value: 24, color: "#14C38E" },
          { label: "Audio cleanup", value: 21, color: "#FFB020" }, { label: "Creative choices", value: 17, color: "#FF4D8D" }]} />
        <ShowLabel dark={false} items={[["Template", "DonutChart"], ILLUSTRATIVE]} />
      </>);
    case "bars":
      return (<>
        <BarChart title="Minutes to finish a 10-min video" unit="m" accent="#14C38E" highlight="min" bars={[
          { label: "By hand", value: 240 }, { label: "Templates", value: 120 }, { label: "AI first pass", value: 35 }, { label: "AI + review", value: 50 }]} />
        <ShowLabel items={[["Template", "BarChart"], ILLUSTRATIVE]} />
      </>);
    case "quote":
      return (<>
        <QuoteCard quote="The best edit is the one nobody notices." author="An editor's rule of thumb" accent="#C8A96A" background="#F4F1EA" text="#16130F" />
        <ShowLabel dark={false} items={[["Template", "QuoteCard"]]} />
      </>);
    case "chapter3":
      return (<>
        <ChapterCard number="03" title="Make it yours" accent="#FFE100" background="#111111" text="#111111" transparent={false} />
        <ShowLabel dark={false} items={[["Template", "ChapterCard"]]} />
      </>);
    case "styles": {
      const tileW = width * 0.205, tileH = tileW * 9 / 16, sc = tileW / width;
      const kinds: ExplainerScene["type"][] = ["steps", "stat", "quote", "bullets", "chart", "title", "stat", "steps"];
      return (<>
        <AbsoluteFill style={{ background: "#0B0B0F" }} />
        {STYLE_KEYS.map((k) => <StyleFonts key={k} style={resolveStyle(k)} />)}
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div style={{ display: "grid", gridTemplateColumns: `repeat(4, ${tileW}px)`, gap: 28 * u, marginTop: 30 * u }}>
            {STYLE_KEYS.map((k, i) => {
              const delay = i * 5;
              return (
                <Sequence key={k} from={delay} layout="none">
                  <div>
                    <Mini w={tileW} h={tileH} scale={sc} radius={14}>
                      <SceneView style={resolveStyle(k)} scene={{
                        id: k, type: kinds[i], title: resolveStyle(k).label, subtitle: "Design style", items: ["Upload", "Describe", "Review"],
                        value: 81, unit: "%", label: "view duration", quote: "Make every frame count.", author: resolveStyle(k).label,
                        bars: [{ label: "A", value: 3 }, { label: "B", value: 5 }, { label: "C", value: 8 }],
                      }} />
                    </Mini>
                    <div style={{ marginTop: 8 * u, fontFamily: "monospace", fontSize: 18 * u, color: "rgba(255,255,255,0.75)", textAlign: "center" }}>{k}</div>
                  </div>
                </Sequence>
              );
            })}
          </div>
        </AbsoluteFill>
        <ShowLabel items={[["Template", "Explainer × 8"], ["Styles", "design-styles.json"]]} />
      </>);
    }
    case "titles": {
      const half = Math.round(durationInFrames / 2);
      return (<>
        <Sequence durationInFrames={half}><NeonPulse text="Titles can glow" glow="#4DFFDF" /><ShowLabel items={[["Template", "NeonPulse"]]} /></Sequence>
        <Sequence from={half}><EditorialReveal kicker="or" headline="they can whisper" accent="#C8A96A" background="#F4F1EA" /><ShowLabel dark={false} items={[["Template", "EditorialReveal"]]} /></Sequence>
      </>);
    }
    case "promo":
      return (<>
        <AppPromo appName="Video Studio" cta="Try the plugin" background="#F7F8FA" text="#0E1116" accent="#3D7BFF" secondsPerBeat={1.6}
          beats={[{ headline: "Upload", color: "#3D7BFF" }, { headline: "Describe the edit", color: "#14C38E" }, { headline: "Post in minutes", color: "#FF4D8D" }]} />
        <ShowLabel dark={false} items={[["Template", "AppPromo"]]} />
      </>);
    case "countdown": {
      const three = at(s, "three", fps, 30), two = at(s, "two", fps, three + 25);
      const per = Math.max(0.5, (two - three) / fps);
      return (<>
        <AbsoluteFill style={{ background: "#0B0B0F" }} />
        <Sequence from={three}>
          <Countdown from={3} label="Your turn" goText="GO" accent="#FF4D2E" background="#0B0B0F" text="#F5F5F7" secondsPerCount={per} />
        </Sequence>
        <ShowLabel items={[["Template", "Countdown"], ["Synced to", "voice"]]} />
      </>);
    }
    case "logo":
      return (<>
        <LogoReveal brand="VIDEO STUDIO" tagline="Built for creators" accent="#4DFFDF" />
        <ShowLabel items={[["Template", "LogoReveal"]]} />
      </>);
    case "end":
      return (<>
        <EndCard headline="Thanks for watching" handle="@videostudio" nextLabel="Watch next" nextTitle="32 caption styles in 35 seconds" accent="#FF4D2E" background="#0B0B0F" text="#F5F5F7" />
        <Sequence from={20} layout="none">
          <SubscribeButton channel="Video Studio" avatarText="VS" buttonColor="#FF0033" doneColor="#3A3A3A" position="bottom-left" clickSecond={1.4} size={1.1} />
        </Sequence>
        <Sequence from={45} layout="none">
          <CtaPopup {...LIGHT} accent="#FF4D2E" eyebrow="Free plugin" headline="Install video-studio" button="/plugin install" icon="🎬" position="bottom-right" size={1.0} />
        </Sequence>
        <ShowLabel items={[["Templates", "EndCard + SubscribeButton + CtaPopup"]]} />
      </>);
    default:
      return null;
  }
};

/** "AI video editing, explained": every template, labelled on screen. */
export const AiVideoEditing: React.FC<ShowProps> = ({ data }) => {
  if (!data) throw new Error("showcase data not loaded");
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <SceneSeries data={data} render={(s) => <Scene s={s} />} />
      <MusicBed data={data} />
    </AbsoluteFill>
  );
};
