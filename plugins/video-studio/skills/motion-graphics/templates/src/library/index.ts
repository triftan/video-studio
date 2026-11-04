import React from "react";
import catalog from "./catalog.json";
import { Checklist } from "./Checklist";
import { NumberCounter } from "./NumberCounter";
import { WeeklySchedule } from "./WeeklySchedule";
import { StampTitle } from "./StampTitle";
import { LoadingBar } from "./LoadingBar";
import { DonutChart } from "./DonutChart";
import { LineChart } from "./LineChart";
import { Countdown } from "./Countdown";
import { SubscribeButton } from "./SubscribeButton";
import { SocialHandle } from "./SocialHandle";
import { CtaPopup } from "./CtaPopup";
import { Callout } from "./Callout";
import { AppPromo } from "./AppPromo";
import { QuoteCard } from "./QuoteCard";
import { ChapterCard } from "./ChapterCard";
import { EndCard } from "./EndCard";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const LIBRARY_COMPONENTS: Record<string, React.FC<any>> = {
  Checklist, NumberCounter, WeeklySchedule, StampTitle, LoadingBar, DonutChart, LineChart, Countdown,
  SubscribeButton, SocialHandle, CtaPopup, Callout, AppPromo, QuoteCard, ChapterCard, EndCard,
};

export type LibraryEntry = {
  id: string; category: string; overlay: boolean; seconds: number; desc: string; file: string;
  props: Record<string, unknown>;
};
export const LIBRARY = (catalog as unknown as { templates: LibraryEntry[] }).templates;
