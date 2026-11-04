#!/usr/bin/env node
// SessionStart hook: if video-studio setup has never been completed on this machine,
// ask Claude to offer the one-time setup. Silent once setup is done.
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const file = join(homedir(), ".video-studio", "setup.json");
let done = false;
try { done = !!JSON.parse(readFileSync(file, "utf8")).completedAt; } catch { done = false; }

if (!done && !existsSync(join(homedir(), ".video-studio", "skip"))) {
  console.log([
    "The video-studio plugin is installed but its one-time setup has not been run on this machine.",
    "At the start of your first reply, tell the user in one short sentence that they can run /video-studio:setup",
    "(about 5 minutes: checks ffmpeg/Node/Python, prepares the Remotion workspace, connects Fish Audio for",
    "voiceovers, and opens the style catalog). Then continue with whatever they asked. Do not run setup unasked.",
  ].join(" "));
}
