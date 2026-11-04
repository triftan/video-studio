# video-studio dependency installer for Windows 10/11 (PowerShell 5.1+, uses winget).
#
#   powershell -ExecutionPolicy Bypass -File bootstrap.ps1            check only
#   powershell -ExecutionPolicy Bypass -File bootstrap.ps1 -Install   install everything missing
#   options: -Workspace DIR (default ~\video-studio)  -NoWorkspace  -WithKokoro
#
# Installs: Node.js LTS and ffmpeg via winget (Windows may show a "Do you want to allow..." prompt: click Yes),
# uv (Python manager, no admin) with Python 3.12, a private Python environment in ~\.video-studio\venv,
# and the Remotion workspace. Exit codes: 0 done, 2 one manual step left (printed), 3 something missing (check mode), 1 error.

param([switch]$Install, [string]$Workspace = "$HOME\video-studio", [switch]$NoWorkspace, [switch]$WithKokoro)

$ErrorActionPreference = "Continue"
$VS = Join-Path $HOME ".video-studio"
$Plugin = Split-Path -Parent $PSScriptRoot
$VenvPy = Join-Path $VS "venv\Scripts\python.exe"
$Manual = @()
New-Item -ItemType Directory -Force -Path (Join-Path $VS "bin") | Out-Null

function Refresh-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User") +
              ";$HOME\.local\bin;$VS\bin"
}
function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function NodeOk { if (-not (Have node)) { return $false }; try { [int](node -p "process.versions.node.split('.')[0]") -ge 18 } catch { $false } }
function FfmpegOk { (Have ffmpeg) -and (Have ffprobe) -and ((ffmpeg -hide_banner -version 2>$null | Out-String) -match "--enable-libass") }
function VenvOk { (Test-Path $VenvPy) -and ((& $VenvPy -c "import mediapipe, cv2, PIL, numpy, faster_whisper; print('ok')" 2>$null) -eq "ok") }
function WsOk { Test-Path (Join-Path $Workspace "node_modules\remotion") }

function Check {
  $script:Missing = @()
  Write-Host "video-studio dependency check (Windows)"
  if (NodeOk) { Write-Host "  OK node $(node -v)" } else { $script:Missing += "node"; Write-Host "  MISSING node: Node.js 18+" }
  if (FfmpegOk) { Write-Host "  OK ffmpeg" } else { $script:Missing += "ffmpeg"; Write-Host "  MISSING ffmpeg (with libass)" }
  if (VenvOk) { Write-Host "  OK python-env $VS\venv" } else { $script:Missing += "python-env"; Write-Host "  MISSING python-env: effects, tracking, transcription" }
  if (-not $NoWorkspace) { if (WsOk) { Write-Host "  OK workspace $Workspace" } else { $script:Missing += "workspace"; Write-Host "  MISSING workspace: $Workspace" } }
}

Refresh-Path
Check
if (-not $Install) {
  if ($Missing.Count -eq 0) { Write-Host "Everything is installed."; exit 0 }
  Write-Host "`nMissing: $($Missing -join ', ')`nRun: powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Install"
  exit 3
}
if ($Missing.Count -eq 0) { Write-Host "Everything is installed."; exit 0 }

$haveWinget = Have winget
$wingetArgs = @("--exact", "--silent", "--accept-source-agreements", "--accept-package-agreements")

if (-not (NodeOk)) {
  if ($haveWinget) { Write-Host "-> Installing Node.js LTS (winget)..."; winget install --id OpenJS.NodeJS.LTS @wingetArgs | Out-Null; Refresh-Path }
  if (-not (NodeOk)) { $Manual += "Install Node.js LTS from https://nodejs.org (Windows Installer .msi), then say 'done'." }
}
if (-not (FfmpegOk)) {
  if ($haveWinget) { Write-Host "-> Installing ffmpeg (winget)..."; winget install --id Gyan.FFmpeg @wingetArgs | Out-Null; Refresh-Path }
  if (-not (FfmpegOk)) { $Manual += "Install ffmpeg: open the Microsoft Store and update 'App Installer' (this provides winget), then say 'done'." }
}
if (-not (Have uv)) {
  Write-Host "-> Installing uv (Python manager)..."
  $env:UV_NO_MODIFY_PATH = "1"
  try { Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression | Out-Null } catch { }
  Refresh-Path
}
if (-not (Test-Path $VenvPy)) {
  if (Have uv) { Write-Host "-> Creating the Python environment (Python 3.12)..."; uv venv --python 3.12 "$VS\venv" | Out-Null }
  elseif (Have python) { python -m venv "$VS\venv" }
  else { $Manual += "Install Python 3.12 from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then say 'done'." }
}
if (Test-Path $VenvPy) {
  Write-Host "-> Installing Python packages (MediaPipe, OpenCV, faster-whisper; 1-3 minutes)..."
  $pkgs = @("-r", "$Plugin\skills\video-effects\requirements.txt", "faster-whisper")
  if ($WithKokoro) { $pkgs += @("kokoro-onnx", "soundfile") }
  if (Have uv) { uv pip install --python $VenvPy -q @pkgs } else { & $VenvPy -m pip install -q @pkgs }
}
if (-not $NoWorkspace -and -not (WsOk) -and (NodeOk)) {
  if ((Test-Path "$Workspace\package.json") -and -not (Test-Path "$Workspace\src\Root.tsx")) {
    $Manual += "$Workspace already holds another project; rerun with -Workspace C:\path\to\another\folder."
  } else {
    Write-Host "-> Preparing the Remotion workspace at $Workspace (1-2 minutes)..."
    New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
    robocopy "$Plugin\skills\motion-graphics\templates" $Workspace /E /XD node_modules out /NFL /NDL /NJH /NJS /NP | Out-Null
    Push-Location $Workspace; npm install --no-audit --no-fund --loglevel=error; Pop-Location
  }
}
# Keep ~\.video-studio\bin and uv's folder on the user PATH for future sessions.
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
foreach ($p in @("$VS\bin", "$HOME\.local\bin")) {
  if ($userPath -notlike "*$p*") { $userPath = "$p;$userPath" }
}
[Environment]::SetEnvironmentVariable("Path", $userPath, "User")

Write-Host ""
Check
if ($Manual.Count -gt 0) { Write-Host "`nOne manual step left:"; $Manual | ForEach-Object { Write-Host "- $_" }; exit 2 }
if ($Missing.Count -eq 0) { Write-Host "`nAll set. Restart Claude Code once so the new tools are on your PATH."; exit 0 }
exit 1
