<#
.SYNOPSIS
  install.ps1 — install the system-design skill into every agent, IDE, and
  CLI on this machine that supports the Agent Skills standard (40+ tools).

.EXAMPLE
  .\install.ps1                 # auto-detect installed tools, install to each
  .\install.ps1 -List           # show install targets and detection status
  .\install.ps1 -All            # install to every known target, detected or not
  .\install.ps1 -Only claude-code,opencode
  .\install.ps1 -Project        # also install to .agents\skills\ in the current dir
  .\install.ps1 -DryRun         # show what would happen without changing anything
  .\install.ps1 -Uninstall      # remove the skill from all targets (our installs only)

.NOTES
  Safety: this script never deletes anything except <target>\system-design
  directories that contain SKILL.md (i.e., a previous install of this skill).
  Foreign directories with the same name are skipped with a warning.
#>

param(
  [switch]$List,
  [switch]$All,
  [string]$Only = "",
  [switch]$DryRun,
  [switch]$Project,
  [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$source = Join-Path $PSScriptRoot "system-design"
if (-not (Test-Path (Join-Path $source "SKILL.md"))) {
  Write-Error "system-design/SKILL.md not found next to this script"
  exit 1
}

# name | install dir (relative to HOME) | detection dir (relative to HOME, empty = always offered)
$targets = @(
  @{ name = "universal";     dir = ".agents\skills";                  det = "" },
  @{ name = "claude-code";   dir = ".claude\skills";                  det = ".claude" },
  @{ name = "opencode";      dir = ".config\opencode\skills";         det = ".config\opencode" },
  @{ name = "codex";         dir = ".codex\skills";                   det = ".codex" },
  @{ name = "cursor";        dir = ".cursor\skills";                  det = ".cursor" },
  @{ name = "gemini-cli";    dir = ".gemini\skills";                  det = ".gemini" },
  @{ name = "antigravity";   dir = ".gemini\antigravity\skills";      det = ".gemini\antigravity" },
  @{ name = "windsurf";      dir = ".codeium\windsurf\skills";        det = ".codeium\windsurf" },
  @{ name = "copilot";       dir = ".copilot\skills";                 det = ".copilot" },
  @{ name = "kilocode";      dir = ".kilocode\skills";                det = ".kilocode" },
  @{ name = "cline";         dir = ".cline\skills";                   det = ".cline" },
  @{ name = "zed";           dir = ".config\zed\skills";              det = ".config\zed" },
  @{ name = "commandcode";   dir = ".commandcode\skills";             det = ".commandcode" },
  @{ name = "kiro";          dir = ".kiro\skills";                    det = ".kiro" }
)

function Want([string]$name) {
  if ($Only -eq "") { return $true }
  return ($Only -split "," | Where-Object { $_ -eq $name }).Count -gt 0
}

function Install-One([string]$name, [string]$rel, [string]$det) {
  if (-not (Want $name)) { return }
  $dest = Join-Path $HOME $rel
  $detected = $true
  if ($det -ne "" -and -not (Test-Path (Join-Path $HOME $det))) { $detected = $false }
  if (-not $All -and -not $detected) {
    Write-Host "  skip  $name (not detected — use -All to force)"
    return
  }
  Write-Host "  ->    $name  $dest"
  if ($DryRun) { return }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  $skillDir = Join-Path $dest "system-design"
  if (Test-Path $skillDir) {
    if (Test-Path (Join-Path $skillDir "SKILL.md")) {
      Remove-Item -Recurse -Force $skillDir
    } else {
      Write-Host "  WARN  $skillDir exists but is not this skill — leaving it untouched"
      return
    }
  }
  Copy-Item -Recurse -Force -Path $source -Destination $skillDir
}

function Uninstall-One([string]$name, [string]$rel) {
  if (-not (Want $name)) { return }
  $skillDir = Join-Path (Join-Path $HOME $rel) "system-design"
  if ((Test-Path $skillDir) -and (Test-Path (Join-Path $skillDir "SKILL.md"))) {
    Write-Host "  rm    $name  $skillDir"
    if ($DryRun) { return }
    Remove-Item -Recurse -Force $skillDir
  } else {
    Write-Host "  skip  $name (no previous install found)"
  }
}

if ($List) {
  Write-Host "Install targets (HOME=$HOME)"
  Write-Host ("  {0,-14} {1,-38} {2}" -f "TARGET", "GLOBAL DIR", "DETECTED")
  foreach ($t in $targets) {
    $st = "no"
    if ($t.det -eq "") { $st = "always" }
    elseif (Test-Path (Join-Path $HOME $t.det)) { $st = "yes" }
    Write-Host ("  {0,-14} {1,-38} {2}" -f $t.name, (Join-Path $HOME $t.dir), $st)
  }
  exit 0
}

Write-Host "system-design skill — installing from $source"
Write-Host ""

if ($Uninstall) {
  foreach ($t in $targets) { Uninstall-One $t.name $t.dir }
  Write-Host ""
  Write-Host "Done. Restart your agent/IDE to refresh the skill list."
  exit 0
}

foreach ($t in $targets) { Install-One $t.name $t.dir $t.det }

if ($Project) {
  New-Item -ItemType Directory -Force -Path ".agents\skills" | Out-Null
  $proj = ".agents\skills\system-design"
  if (Test-Path $proj) { Remove-Item -Recurse -Force $proj }
  Copy-Item -Recurse -Force -Path $source -Destination $proj
  Write-Host "  ->    project  .\.agents\skills\system-design"
}

Write-Host ""
if ($DryRun) {
  Write-Host "Dry run — nothing was changed."
} else {
  Write-Host "Installed. Verification: in any agent, ask"
  Write-Host "  'how would you architect a ticket booking system?'"
  Write-Host "  You should get capacity math before components, not a component zoo."
  Write-Host ""
  Write-Host "Other surfaces: Claude.ai (Settings > Skills > upload the zipped"
  Write-Host "system-design/ folder), Claude API (/v1/skills), and per-tool native"
  Write-Host "plugin commands — see INSTALL.md."
}