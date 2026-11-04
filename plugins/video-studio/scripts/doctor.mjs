#!/usr/bin/env node
// Checks everything the video-studio plugin needs and prints a JSON report.
// Usage: node doctor.mjs            -> report
//        node doctor.mjs --mark-done -> also record that setup finished (writes ~/.video-studio/setup.json)
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || join(dirname(fileURLToPath(import.meta.url)), "..");
const STATE_DIR = join(homedir(), ".video-studio");
const STATE_FILE = join(STATE_DIR, "setup.json");
const WIN = platform() === "win32";

const run = (cmd, args) => {
  try {
    return execFileSync(cmd, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], timeout: 20000, shell: WIN }).trim();
  } catch (e) {
    return e.stdout ? String(e.stdout).trim() || null : null;
  }
};
const firstLine = (s) => (s ? s.split(/\r?\n/)[0] : null);
const version = (s) => (s && (s.match(/(\d+)\.(\d+)(?:\.(\d+))?/) || []).slice(1, 3).map(Number)) || null;

const checks = [];
const add = (id, ok, detail, fix, required = true) => checks.push({ id, ok, required, detail, fix });

// Node
const nodeV = version(process.versions.node);
add("node", nodeV && nodeV[0] >= 18, `Node ${process.versions.node}`,
  "Install Node.js 18 or newer from https://nodejs.org (LTS).");

// ffmpeg + libass (needed to burn styled captions)
const ff = run("ffmpeg", ["-hide_banner", "-version"]);
const hasLibass = !!(ff && ff.includes("--enable-libass"));
const fixFfmpeg = platform() === "darwin" ? "brew install ffmpeg"
  : WIN ? "winget install --id Gyan.FFmpeg -e   (then open a new terminal)"
  : "sudo apt install ffmpeg   (or your distro's package)";
add("ffmpeg", !!ff, ff ? firstLine(ff) : "not found", fixFfmpeg);
add("ffmpeg-libass", hasLibass, hasLibass ? "caption burn-in supported" : "ffmpeg built without libass",
  `Reinstall a full ffmpeg build: ${fixFfmpeg}`);
add("ffprobe", !!run("ffprobe", ["-version"]), "used to measure clips", fixFfmpeg);

// Python 3.9+
const py = run(WIN ? "python" : "python3", ["--version"]) || run("python", ["--version"]);
const pyV = version(py);
add("python", !!(pyV && (pyV[0] > 3 || (pyV[0] === 3 && pyV[1] >= 9))), py || "not found",
  platform() === "darwin" ? "brew install python" : WIN ? "winget install Python.Python.3.12" : "sudo apt install python3 python3-pip");

// Optional Python packages
const pyBin = WIN ? "python" : "python3";
const hasPkg = (mod) => run(pyBin, ["-c", `import ${mod}; print('ok')`]) === "ok";
add("faster-whisper", hasPkg("faster_whisper"), "word timestamps for captions",
  `${pyBin} -m pip install faster-whisper`, false);
add("kokoro (free offline voice)", hasPkg("kokoro_onnx"), "fallback voiceover when Fish Audio credits run out",
  `${pyBin} -m pip install kokoro-onnx soundfile`, false);

// Remotion workspace
let state = {};
try { state = JSON.parse(readFileSync(STATE_FILE, "utf8")); } catch { /* first run */ }
const ws = state.workspace || join(homedir(), "video-studio");
const wsReady = existsSync(join(ws, "node_modules", "remotion"));
add("remotion-workspace", wsReady, wsReady ? `ready at ${ws}` : `not set up (${ws})`,
  `Copy ${join(PLUGIN_ROOT, "skills", "motion-graphics", "templates")} to ${ws} and run "npm install" there.`);

const report = {
  plugin_root: PLUGIN_ROOT,
  platform: platform(),
  setup_done: !!state.completedAt,
  state_file: STATE_FILE,
  workspace: ws,
  catalog: join(PLUGIN_ROOT, "catalog", "index.html"),
  checks,
  missing_required: checks.filter((c) => c.required && !c.ok).map((c) => c.id),
};

if (process.argv.includes("--mark-done")) {
  if (report.missing_required.length) {
    report.mark_done = `not marked: still missing ${report.missing_required.join(", ")}`;
  } else {
    mkdirSync(STATE_DIR, { recursive: true });
    const fish = process.argv.find((a) => a.startsWith("--fish="));
    writeFileSync(STATE_FILE, JSON.stringify({ ...state, workspace: ws, completedAt: new Date().toISOString(),
      fishAudio: fish ? fish.slice(7) : state.fishAudio || "unknown" }, null, 2));
    report.mark_done = `recorded in ${STATE_FILE}`;
    report.setup_done = true;
  }
}
const wsArg = process.argv.find((a) => a.startsWith("--workspace="));
if (wsArg) {
  mkdirSync(STATE_DIR, { recursive: true });
  writeFileSync(STATE_FILE, JSON.stringify({ ...state, workspace: wsArg.slice(12) }, null, 2));
  report.workspace = wsArg.slice(12);
}
console.log(JSON.stringify(report, null, 2));
