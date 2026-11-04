#!/bin/sh
# SessionStart hook: until video-studio's one-time setup has finished on this computer, ask Claude to run it.
# Plain sh on purpose: it must work before Node.js or Python are installed. Silent once setup is done.
STATE="$HOME/.video-studio/setup.json"
[ -f "$HOME/.video-studio/skip" ] && exit 0
if [ -f "$STATE" ] && grep -q '"completedAt"' "$STATE" 2>/dev/null; then
  exit 0
fi
cat <<'MSG'
video-studio plugin: the one-time setup has not been completed on this computer, so its tools (ffmpeg, Node.js, Python packages, the Remotion workspace, the Fish Audio sign-in) may be missing.
In your first reply, before anything else, tell the user in one or two friendly sentences that video-studio needs a one-time setup that installs everything for them (about 5-10 minutes), and ask "Shall I start now?".
If they agree, or if their first request is any video task, follow the video-studio `setup` skill: its first step installs every missing dependency in one go after a single confirmation. Then continue with what they asked.
MSG
