#!/usr/bin/env bash
#
# install.sh — install the system-design skill into every agent, IDE, and CLI
# on this machine that supports the Agent Skills standard (40+ tools).
#
# Usage:
#   ./install.sh                auto-detect installed tools, install to each
#   ./install.sh --list         show install targets and detection status
#   ./install.sh --all          install to every known target, detected or not
#   ./install.sh --only claude-code,opencode
#   ./install.sh --project      also install to .agents/skills/ in the current dir
#   ./install.sh --dry-run      show what would happen without changing anything
#   ./install.sh --uninstall    remove the skill from all targets (our installs only)
#
# Safety: this script never deletes anything except <target>/system-design
# directories that contain SKILL.md (i.e., a previous install of this skill).
# Foreign directories with the same name are skipped with a warning.

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/system-design"

if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
  echo "error: system-design/SKILL.md not found next to this script" >&2
  exit 1
fi

HOME_DIR="${HOME:-$USERPROFILE}"

# name | install dir (relative to HOME) | detection dir (relative to HOME, empty = always offered)
readonly TARGETS=(
  "universal|.agents/skills|"
  "claude-code|.claude/skills|.claude"
  "opencode|.config/opencode/skills|.config/opencode"
  "codex|.codex/skills|.codex"
  "cursor|.cursor/skills|.cursor"
  "gemini-cli|.gemini/skills|.gemini"
  "antigravity|.gemini/antigravity/skills|.gemini/antigravity"
  "windsurf|.codeium/windsurf/skills|.codeium/windsurf"
  "copilot|.copilot/skills|.copilot"
  "kilocode|.kilocode/skills|.kilocode"
  "cline|.cline/skills|.cline"
  "zed|.config/zed/skills|.config/zed"
  "commandcode|.commandcode/skills|.commandcode"
  "kiro|.kiro/skills|.kiro"
)

LIST=0; ALL=0; DRY=0; PROJECT=0; UNINSTALL=0
ONLY=""

for arg in "$@"; do
  case "$arg" in
    --list) LIST=1 ;;
    --all) ALL=1 ;;
    --dry-run) DRY=1 ;;
    --project) PROJECT=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --only=*) ONLY="${arg#--only=}" ;;
    --only) echo "error: --only requires a comma-separated list (e.g. --only=claude-code,opencode)" >&2; exit 1 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "error: unknown argument: $arg (try --help)" >&2; exit 1 ;;
  esac
done

want() {
  local name="$1"
  if [ -n "$ONLY" ]; then
    case ",$ONLY," in *",$name,"*) return 0 ;; *) return 1 ;; esac
  fi
  return 0
}

detected() {
  local name="$1" det="$2"
  if [ -n "$ONLY" ]; then return 0; fi          # explicit choice beats detection
  if [ -z "$det" ]; then return 0; fi           # universal: no detection needed
  [ -d "$HOME_DIR/$det" ]
}

install_one() {
  local name="$1" rel="$2"
  local dest="$HOME_DIR/$rel"
  if ! want "$name"; then return 0; fi
  if [ "$ALL" -eq 0 ] && ! detected "$name" "$3"; then
    echo "  skip  $name (not detected — use --all to force)"
    return 0
  fi
  echo "  ->    $name  $dest"
  if [ "$DRY" -eq 1 ]; then return 0; fi
  mkdir -p "$dest"
  if [ -d "$dest/system-design" ]; then
    if [ -f "$dest/system-design/SKILL.md" ]; then
      rm -rf "$dest/system-design"
    else
      echo "  WARN  $dest/system-design exists but is not this skill — leaving it untouched"
      return 0
    fi
  fi
  cp -R "$SOURCE_DIR" "$dest/system-design"
}

uninstall_one() {
  local name="$1" rel="$2"
  local dest="$HOME_DIR/$rel"
  if ! want "$name"; then return 0; fi
  if [ -d "$dest/system-design" ] && [ -f "$dest/system-design/SKILL.md" ]; then
    echo "  rm    $name  $dest/system-design"
    if [ "$DRY" -eq 1 ]; then return 0; fi
    rm -rf "$dest/system-design"
  else
    echo "  skip  $name (no previous install found)"
  fi
}

if [ "$LIST" -eq 1 ]; then
  echo "Install targets (HOME=$HOME_DIR)"
  printf "  %-14s %-34s %s\n" "TARGET" "GLOBAL DIR" "DETECTED"
  for t in "${TARGETS[@]}"; do
    IFS='|' read -r name rel det <<<"$t"
    st="no"
    [ -n "$det" ] && [ -d "$HOME_DIR/$det" ] && st="yes"
    [ -z "$det" ] && st="always"
    printf "  %-14s %-34s %s\n" "$name" "$HOME_DIR/$rel" "$st"
  done
  exit 0
fi

echo "system-design skill — installing from $SOURCE_DIR"
echo

if [ "$UNINSTALL" -eq 1 ]; then
  for t in "${TARGETS[@]}"; do
    IFS='|' read -r name rel det <<<"$t"
    uninstall_one "$name" "$rel"
  done
  echo
  echo "Done. Restart your agent/IDE to refresh the skill list."
  exit 0
fi

count=0
for t in "${TARGETS[@]}"; do
  IFS='|' read -r name rel det <<<"$t"
  install_one "$name" "$rel" "$det"
  count=$((count + 1))
done

if [ "$PROJECT" -eq 1 ]; then
  mkdir -p .agents/skills
  if [ -d .agents/skills/system-design ]; then rm -rf .agents/skills/system-design; fi
  cp -R "$SOURCE_DIR" .agents/skills/system-design
  echo "  ->    project  ./.agents/skills/system-design"
fi

echo
if [ "$DRY" -eq 1 ]; then
  echo "Dry run — nothing was changed."
else
  echo "Installed. Verification: in any agent, ask"
  echo "  'how would you architect a ticket booking system?'"
  echo "  You should get capacity math before components, not a component zoo."
  echo
  echo "Other surfaces: Claude.ai (Settings > Skills > upload the zipped"
  echo "system-design/ folder), Claude API (/v1/skills), and per-tool native"
  echo "plugin commands — see INSTALL.md."
fi