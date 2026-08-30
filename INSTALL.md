# Install — every agent, IDE, and CLI

The skill is a standard Agent Skills folder (`system-design/`), which runs in **40+ tools** — Claude Code, OpenCode, Codex, Cursor, Gemini CLI, Antigravity, GitHub Copilot, Windsurf, Kilo Code, Cline, Zed, and more. Pick one path below; they all install the same folder.

## Option 1 — one command for every tool you have (recommended)

The open [skills CLI](https://github.com/vercel-labs/skills) detects which agents are installed on your machine and installs to all of them:

```bash
npx skills add DAAS2/system-design-skill --agent '*'     # every detected agent
npx skills add DAAS2/system-design-skill -a claude-code -a opencode   # specific ones
```

> Requires Node. Use `--agent '*'` for all detected tools, or repeat `-a <agent>` per tool. Full agent list: `npx skills add DAAS2/system-design-skill --list`.

## Option 2 — auto-detecting installer script (no Node needed)

Clone the repo and run one script. It detects every tool installed on this machine and copies the skill into each one's skills directory (idempotent, safe — only ever touches its own installs).

```bash
git clone https://github.com/DAAS2/system-design-skill.git
cd system-design-skill
./install.sh          # macOS / Linux / Git-Bash (Windows)
# or on Windows PowerShell:
.\install.ps1
```

Flags: `--list` · `--all` (install everywhere, even undetected) · `--only=<tool1,tool2>` · `--project` (also install to `./.agents/skills/`) · `--dry-run` · `--uninstall`.

## Option 3 — the universal directory (covers ~10 tools with one copy)

Many agents read the shared `.agents/skills/` path natively — OpenCode, Codex, Cursor, Gemini CLI, GitHub Copilot, Cline, Amp, Kimi Code CLI and others. One copy covers them all:

```bash
# global (all your projects)
mkdir -p ~/.agents/skills && cp -r system-design ~/.agents/skills/
# or per-project
mkdir -p .agents/skills && cp -r system-design .agents/skills/
```

## Option 4 — per-tool (full matrix)

| Tool | Type | Project path | Global path | Notes |
|---|---|---|---|---|
| **Claude Code** | CLI | `.claude/skills/` | `~/.claude/skills/` | Or `/plugin marketplace add DAAS2/system-design-skill` then `/plugin install system-design` |
| **OpenCode** | CLI | `.opencode/skills/` (also `.agents/skills/`, `.claude/skills/`) | `~/.config/opencode/skills/` (also `~/.agents/skills/`, `~/.claude/skills/`) | Native `skill` tool; also configurable via the `skills` array in `opencode.json` |
| **OpenAI Codex** | CLI | `.agents/skills/` | `~/.codex/skills/` (respects `CODEX_HOME`) | Invoke with `@system-design` |
| **Cursor** | IDE | `.agents/skills/` (also `.cursor/skills/`) | `~/.cursor/skills/` | Also `Agent Rules` → `.cursor/rules/` for policies |
| **Gemini CLI** | CLI | `.agents/skills/` | `~/.gemini/skills/` | Native: `gemini skills install https://github.com/DAAS2/system-design-skill.git --path system-design` |
| **Antigravity** | IDE + CLI | `.agent/skills/` | `~/.gemini/antigravity/skills/` | |
| **GitHub Copilot** | CLI/IDE | `.agents/skills/` (also `.github/skills/`) | `~/.copilot/skills/` | Agent mode reads `SKILL.md`; invoke via `/skills` |
| **Windsurf** | IDE | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` | Cascade agent mode |
| **Kilo Code** | IDE | `.kilocode/skills/` | `~/.kilocode/skills/` | |
| **Cline** | IDE | `.agents/skills/` (also `.cline/skills/`) | `~/.cline/skills/` | |
| **Roo Code** | IDE | `.agents/skills/` | `~/.roo/skills/` | |
| **Zed** | IDE | `.zed/skills/` | `~/.config/zed/skills/` | |
| **Command Code** | CLI | `.commandcode/skills/` | `~/.commandcode/skills/` | Native: `cmd skills add DAAS2/system-design-skill` |
| **Kiro** | IDE/CLI | `.kiro/skills/` | `~/.kiro/skills/` | |
| **Kimi Code CLI** | CLI | `.agents/skills/` | `~/.agents/skills/` | |
| **Amp** | CLI | `.agents/skills/` | `~/.agents/skills/` | |

**Also covered** (via the skills CLI, and `.agents/skills/` where supported): OpenHands, CodeBuddy, OpenClaw, Qoder, Zencoder, Neovate, Pi, Crush, Factory AI/Droid, Pochi, Ara, Aide, Qwen Code, Sourcegraph Cody, Hermes, and the rest of the 40+ in the [skills CLI registry](https://github.com/vercel-labs/skills).

## Other surfaces

| Surface | How |
|---|---|
| **Claude.ai** (web/app) | Zip the `system-design/` folder → Settings → Skills → Upload skill |
| **Claude API** | POST to the `/v1/skills` endpoint (workspace-scoped), or bundle the folder with the code-execution container |
| **Anthropic open standard** | The folder is plain Agent Skills — any future conforming tool can read it as-is (see [agentskills.io](https://agentskills.io)) |

## Verify the install

In any tool, ask:

> *"how would you architect a ticket booking system?"*

A working install answers with capacity math before components (QPS, storage), names its trade-offs, and rejects over-engineering for the stated scale. A broken install answers with a component zoo and no numbers.

Per-tool quick checks:

- **Claude Code**: `/skills` shows `system-design`.
- **OpenCode**: `opencode` lists the skill in its skill tool output (`skill` tool → `system-design`); `~/.config/opencode/skills/system-design/SKILL.md` exists.
- **Codex**: `@system-design` appears in the tool menu.
- **Cursor**: Settings → Features → Agent → Skills shows `system-design`.
- **Gemini CLI**: `/skills` shows `system-design`.

## Updating

The skill is plain files — update = reinstall:

```bash
npx skills update DAAS2/system-design-skill        # via skills CLI
./install.sh                                       # via the script (re-copies, idempotent)
git pull && ./install.sh
```

## Uninstalling

```bash
npx skills remove DAAS2/system-design-skill
./install.sh --uninstall          # script: only removes its own installs
# or delete the folder manually per tool (see matrix above)
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Skill never triggers | The `description` frontmatter drives auto-loading. Ask with the words "design", "architect", "map", or "review" (see the README modes). Some tools require an explicit invoke (`/skills`, `@system-design`). |
| Nothing in the menu after install | Restart the agent/IDE. Some tools cache the skill list at startup. |
| OpenCode shows the skill twice | Older OpenCode versions scanned both `skill/` and `skills/`. Use the plural `skills` path, update OpenCode, and remove the duplicate folder. |
| "not detected" in the installer | Detection is by config directory. Use `--all` to install anyway. |
| A tool you use isn't in the matrix | It almost certainly still works — any Agent Skills-conforming tool reads this folder. Put it in the tool's skills directory and open an issue so we can add it here. |