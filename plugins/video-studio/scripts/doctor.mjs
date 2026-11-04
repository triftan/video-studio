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
// Tools installed by bootstrap live in the home folder; find them even before a restart picks up the new PATH.
{
  const sep = WIN ? ";" : ":";
  const extra = [join(homedir(), ".video-studio", "bin"), join(homedir(), ".video-studio", "node", WIN ? "" : "bin"),
    join(homedir(), ".local", "bin"), "/opt/homebrew/bin", "/usr/local/bin"];
  process.env.PATH = extra.join(sep) + sep + (process.env.PATH || "");
}

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
  WIN ? `powershell -ExecutionPolicy Bypass -File "${join(PLUGIN_ROOT, "scripts", "bootstrap.ps1")}" -Install`
      : `sh "${join(PLUGIN_ROOT, "scripts", "bootstrap.sh")}" --install`);

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

// Private Python environment for the plugin's scripts (avoids "externally managed" errors on macOS/Linux)
const sysPy = WIN ? "python" : "python3";
const VENV = join(STATE_DIR, "venv");
const venvPy = WIN ? join(VENV, "Scripts", "python.exe") : join(VENV, "bin", "python");
const hasVenv = existsSync(venvPy);
const pyBin = hasVenv ? venvPy : sysPy;
const pip = `"${venvPy}" -m pip install`;
const effectsReq = join(PLUGIN_ROOT, "skills", "video-effects", "requirements.txt");
add("python-venv", hasVenv, hasVenv ? `ready at ${VENV}` : "not created yet",
  `${sysPy} -m venv "${VENV}"`);
const hasPkg = (mod) => run(pyBin, ["-c", `import ${mod}; print('ok')`]) === "ok";
add("video-effects (mediapipe, opencv)", hasVenv && hasPkg("mediapipe") && hasPkg("cv2") && hasPkg("PIL"),
  "needed for the 83 video effects, zooms and color grades", `${pip} -r "${effectsReq}"`);
add("faster-whisper", hasVenv && hasPkg("faster_whisper"), "word timestamps for captions", `${pip} faster-whisper`, false);
add("kokoro (free offline voice)", hasVenv && hasPkg("kokoro_onnx"), "fallback voiceover when Fish Audio credits run out",
  `${pip} kokoro-onnx soundfile`, false);

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
  python: pyBin,
  bootstrap: WIN ? `powershell -ExecutionPolicy Bypass -File "${join(PLUGIN_ROOT, "scripts", "bootstrap.ps1")}" -Install`
                 : `sh "${join(PLUGIN_ROOT, "scripts", "bootstrap.sh")}" --install`,
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
