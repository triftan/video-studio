#!/bin/sh
# video-studio dependency installer for macOS and Linux. Needs only sh and curl (both preinstalled).
#
#   sh bootstrap.sh            check only: print what is missing (exit 0 when nothing is)
#   sh bootstrap.sh --install  install everything missing, in your home folder where possible
#   options: --workspace DIR (default ~/video-studio)  --no-workspace  --with-kokoro
#
# What it installs, and where:
#   Node.js LTS    ~/.video-studio/node        (official nodejs.org build, no admin needed)
#   uv + Python    ~/.local/bin/uv, Python 3.12 managed by uv (no admin needed)
#   Python env     ~/.video-studio/venv        (MediaPipe, OpenCV, Pillow, NumPy, faster-whisper)
#   ffmpeg         macOS: Homebrew (brew install ffmpeg)
#                  Linux: apt if it can run without a password prompt, else a static build in ~/.video-studio/bin
#   Remotion       the workspace folder, via npm install
# It adds ~/.video-studio/bin and ~/.video-studio/node/bin to PATH in your shell profile (one marked block).
# Exit codes: 0 done / nothing missing, 2 something needs one manual step (printed), 1 error.

set -u
MODE=check
WORKSPACE="$HOME/video-studio"
DO_WS=1
KOKORO=0
for a in "$@"; do
  case "$a" in
    --install) MODE=install ;;
    --workspace=*) WORKSPACE="${a#--workspace=}" ;;
    --no-workspace) DO_WS=0 ;;
    --with-kokoro) KOKORO=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
  esac
done

HERE=$(cd "$(dirname "$0")" && pwd)
PLUGIN=$(cd "$HERE/.." && pwd)
VS="$HOME/.video-studio"
mkdir -p "$VS/bin"
PATH="$VS/bin:$VS/node/bin:$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
OS=$(uname -s)
ARCH=$(uname -m)
MANUAL=""
missing=""

say() { printf '%s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }
need() { missing="$missing $1"; say "  ✗ $1: $2"; }
ok() { say "  ✓ $1: $2"; }

node_ok() { have node && [ "$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)" -ge 18 ]; }
ffmpeg_ok() { have ffmpeg && have ffprobe && ffmpeg -hide_banner -version 2>/dev/null | grep -q -- '--enable-libass'; }
venv_py() { printf '%s' "$VS/venv/bin/python"; }
venv_ok() { [ -x "$(venv_py)" ] && "$(venv_py)" -c 'import mediapipe, cv2, PIL, numpy, faster_whisper' >/dev/null 2>&1; }
ws_ok() { [ -d "$WORKSPACE/node_modules/remotion" ]; }

check() {
  missing=""
  say "video-studio dependency check ($OS $ARCH)"
  if node_ok; then ok node "$(node -v)"; else need node "Node.js 18+ (for motion graphics and setup)"; fi
  if ffmpeg_ok; then ok ffmpeg "$(ffmpeg -hide_banner -version | head -1 | cut -c1-40)"
  elif have ffmpeg; then need ffmpeg "installed but without libass (needed to burn in captions)"
  else need ffmpeg "video cutting, captions, export"; fi
  if have uv || have python3; then ok python "$(uv --version 2>/dev/null || python3 --version 2>&1)"; else need python "Python (installed through uv)"; fi
  if venv_ok; then ok python-env "$VS/venv"; else need python-env "effects, tracking and transcription packages"; fi
  if egl_ok; then :; else need egl "graphics library used by face tracking (libEGL)"; fi
  if [ "$DO_WS" = 1 ]; then
    if ws_ok; then ok workspace "$WORKSPACE"; else need workspace "Remotion workspace at $WORKSPACE"; fi
  fi
}

fetch() { curl -fsSL --proto '=https' --tlsv1.2 --retry 3 "$1" -o "$2"; }

install_node() {
  node_ok && return 0
  say "→ Installing Node.js LTS into $VS/node ..."
  case "$OS-$ARCH" in
    Darwin-arm64) plat=darwin-arm64 ;; Darwin-x86_64) plat=darwin-x64 ;;
    Linux-x86_64) plat=linux-x64 ;; Linux-aarch64|Linux-arm64) plat=linux-arm64 ;;
    *) MANUAL="$MANUAL\n- Install Node.js 18+ from https://nodejs.org"; return 1 ;;
  esac
  tmp=$(mktemp -d)
  fetch https://nodejs.org/dist/index.json "$tmp/index.json" || true
  ver=$(tr '{' '\n' < "$tmp/index.json" 2>/dev/null | grep '"lts":"' | head -1 | sed 's/.*"version":"\([^"]*\)".*/\1/')
  [ -n "$ver" ] || { rm -rf "$tmp"; MANUAL="$MANUAL\n- Install Node.js 18+ from https://nodejs.org"; return 1; }
  fetch "https://nodejs.org/dist/$ver/node-$ver-$plat.tar.gz" "$tmp/node.tgz" || { rm -rf "$tmp"; return 1; }
  rm -rf "$VS/node" && mkdir -p "$VS/node" && tar -xzf "$tmp/node.tgz" -C "$VS/node" --strip-components=1
  rm -rf "$tmp"
  node_ok && say "  ✓ node $(node -v)"
}

install_ffmpeg() {
  ffmpeg_ok && return 0
  if [ "$OS" = Darwin ]; then
    if have brew; then
      # Homebrew's plain "ffmpeg" formula is built without libass (needed for captions); "ffmpeg-full" has it.
      say "→ brew install ffmpeg-full (a few minutes) ..."
      brew install ffmpeg-full >/dev/null 2>&1 || brew install ffmpeg-full
      fp=$(brew --prefix ffmpeg-full 2>/dev/null)
      if [ -n "$fp" ] && [ -x "$fp/bin/ffmpeg" ]; then
        ln -sf "$fp/bin/ffmpeg" "$VS/bin/ffmpeg"
        ln -sf "$fp/bin/ffprobe" "$VS/bin/ffprobe"
      fi
    else
      MANUAL="$MANUAL\n- Install Homebrew (it needs your Mac password, so run it yourself in the Terminal app):\n    /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n  then come back and say \"done\" so setup can install ffmpeg."
      return 1
    fi
  else
    if have apt-get && sudo -n true 2>/dev/null; then
      say "→ apt-get install ffmpeg ..."
      sudo -n apt-get update -qq && sudo -n apt-get install -y -qq ffmpeg
    fi
    if ! ffmpeg_ok; then
      case "$ARCH" in x86_64) f=amd64 ;; aarch64|arm64) f=arm64 ;; *) f="" ;; esac
      [ -n "$f" ] || { MANUAL="$MANUAL\n- Install ffmpeg with your package manager (e.g. sudo apt install ffmpeg)"; return 1; }
      say "→ Downloading a static ffmpeg build into $VS/bin ..."
      tmp=$(mktemp -d)
      fetch "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-$f-static.tar.xz" "$tmp/ff.tar.xz" &&
        tar -xJf "$tmp/ff.tar.xz" -C "$tmp" && cp "$tmp"/ffmpeg-*-static/ffmpeg "$tmp"/ffmpeg-*-static/ffprobe "$VS/bin/"
      rm -rf "$tmp"
    fi
  fi
  ffmpeg_ok && say "  ✓ ffmpeg ready"
}

egl_ok() { [ "$OS" != Linux ] || ldconfig -p 2>/dev/null | grep -q 'libEGL.so.1' || ls /usr/lib/*/libEGL.so.1 /usr/lib64/libEGL.so.1 >/dev/null 2>&1; }

install_egl() {
  egl_ok && return 0
  if have apt-get && sudo -n true 2>/dev/null; then
    say "→ apt-get install libegl1 libgles2 (needed by face tracking) ..."
    sudo -n apt-get update -qq && sudo -n apt-get install -y -qq libegl1 libgles2 libgl1 >/dev/null
  fi
  egl_ok || MANUAL="$MANUAL\n- Face tracking needs the EGL graphics library: run  sudo apt install libegl1 libgles2  (or your distro's equivalent)"
}

install_python() {
  if ! have uv; then
    say "→ Installing uv (Python manager) ..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >/dev/null 2>&1 || true
  fi
  if [ ! -x "$(venv_py)" ]; then
    if have uv; then
      say "→ Creating the Python environment (Python 3.12) ..."
      uv venv --python 3.12 "$VS/venv" >/dev/null 2>&1 || uv venv "$VS/venv"
    elif have python3; then
      python3 -m venv "$VS/venv" || { MANUAL="$MANUAL\n- Python venv failed; install Python 3.10-3.12 from python.org"; return 1; }
    else
      MANUAL="$MANUAL\n- Install Python 3.12 from https://www.python.org/downloads/"; return 1
    fi
  fi
  pkgs="-r $PLUGIN/skills/video-effects/requirements.txt faster-whisper"
  [ "$KOKORO" = 1 ] && pkgs="$pkgs kokoro-onnx soundfile"
  say "→ Installing Python packages (MediaPipe, OpenCV, faster-whisper; 1-3 minutes) ..."
  if have uv; then
    # shellcheck disable=SC2086
    uv pip install --python "$(venv_py)" -q $pkgs
  else
    "$(venv_py)" -m pip install -q --upgrade pip && "$(venv_py)" -m pip install -q $pkgs
  fi
  venv_ok && say "  ✓ python packages ready"
}

install_workspace() {
  [ "$DO_WS" = 1 ] || return 0
  ws_ok && return 0
  node_ok || return 1
  say "→ Preparing the Remotion workspace at $WORKSPACE (1-2 minutes) ..."
  if [ -f "$WORKSPACE/package.json" ] && [ ! -f "$WORKSPACE/src/Root.tsx" ]; then
    MANUAL="$MANUAL\n- $WORKSPACE already holds another project; rerun with --workspace=/another/folder"; return 1
  fi
  mkdir -p "$WORKSPACE"
  (cd "$PLUGIN/skills/motion-graphics/templates" && tar --exclude=node_modules --exclude=out -cf - .) | (cd "$WORKSPACE" && tar -xf -)
  (cd "$WORKSPACE" && npm install --no-audit --no-fund --loglevel=error) && say "  ✓ workspace ready"
}

add_path() {
  block_start="# >>> video-studio >>>"
  line="export PATH=\"\$HOME/.video-studio/bin:\$HOME/.video-studio/node/bin:\$HOME/.local/bin:\$PATH\""
  for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
    case "$rc" in
      */.zshrc) [ "$OS" = Darwin ] || [ -f "$rc" ] || continue ;;
      */.bashrc) [ -f "$rc" ] || continue ;;
    esac
    grep -q "$block_start" "$rc" 2>/dev/null && continue
    printf '\n%s\n%s\n%s\n' "$block_start" "$line" "# <<< video-studio <<<" >> "$rc"
  done
}

check
if [ "$MODE" = check ]; then
  [ -z "$missing" ] && { say "Everything is installed."; exit 0; }
  say ""
  say "Missing:$missing"
  say "Run: sh \"$0\" --install"
  exit 3
fi

[ -z "$missing" ] && { say "Everything is installed."; exit 0; }
say ""
install_node
install_ffmpeg
install_egl
install_python
install_workspace
add_path
say ""
check
if [ -n "$MANUAL" ]; then
  say ""
  say "One manual step left:"
  printf '%b\n' "$MANUAL"
  exit 2
fi
[ -z "$missing" ] && { say ""; say "All set. Restart Claude Code once so the new tools are on your PATH."; exit 0; }
exit 1
