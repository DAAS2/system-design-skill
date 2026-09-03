# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/) — MAJOR when the method changes incompatibly, MINOR for new content, PATCH for corrections.

## [Unreleased]

### Added
- **`DEMO.md`** — three copy-paste prompts (oblique component question, repository map, hard grade), each linked to the real artifact it should resemble. Installation is not proof.
- **`.github/ISSUE_TEMPLATE/field_report.yml`** — field-report issue form (agent, model, verbatim prompt, detected mode, auto-trigger y/n, output link, what helped, what failed, quote permission). Field reports outrank feature requests.
- **`evals/run_triggers.sh --auto`** — automated trigger runs: invokes a host CLI (opencode/claude/codex/gemini) per case, records the YES/NO self-report plus behavioral evidence (whether the host actually loaded the skill), tallies self-report and behavioral rates, writes `evals/out/triggers/results-<tool>-<date>.{json,md}`.

### Changed
- **gatecheck.py** now detects baseline-vs-skill comparison/teardown documents and exits 2 (skipped, with an explanation) instead of failing them — `examples/design-griller-baseline-vs-skill.md` is a tear-down, not a produced design; CI checks the two design artifacts.
- README/HANDBOOK refreshed after the description hardening: SKILL.md is 148 lines (was reported as 132), frontmatter estimate ~270 tokens (was ~120).

## [1.0.0] - 2026-09-03

### Added
- **Trigger evals** — `evals/trigger_evals.json` (20 labelled queries, train/validation split) + `evals/run_triggers.sh` + `tools/validate_trigger_evals.py`: measures whether the skill *fires* on real phrasing (oblique asks + should-not collisions), which behavioral evals could not test because they force-load the skill.
- **`scripts/gatecheck.py`** (+ golden tests) — machine-checkable gate contract: parses a design doc and exits non-zero when a gate output is missing (capacity block, 12-injection table, tier line, monthly cost, cost-per-1k, non-goals, evolution). Wired into CI against the verbatim design examples; SKILL.md's design loop now self-checks with it before finishing.
- **Mode + assumptions preamble (Gate 0)** — every run opens with detected mode / tier / inputs / assumptions / artifact, making misrouting correctable in one turn.

### Changed
- **Hardened description** (SKILL.md): imperative form with oblique trigger phrasings and explicit should-not exclusions (UI/CSS/logo design, single-query DB tuning, pipeline debugging); validated against `trigger_evals.json`'s train set.
- README eval paragraph front-loads the honest caveats (one model, one date, force-loaded) next to the headline numbers.
- `evals/README.md`: trigger-eval methodology + scoring rules; iteration-1 "skill changes" note updated to record the follow-ups shipping as tooling.

### Fixed
- Metastable-failure attribution in `references/stress-tests.md`: Bronson, Aghayev, Charapko & Zhu (HotOS '21) + Aghayev et al. (OSDI '22) — was misattributed to "Obstgarten et al.".

### Added (earlier 1.0.0 batch, 2026-08-30)
- `HANDBOOK.md` — the complete project record: what the skill does, evidence, users, competition, marketing & distribution playbook, star strategy, maintenance, risks, repo map, metrics.
- `examples/design-griller-baseline-vs-skill.md` — same prompt, two agents, one tear-down (real eval outputs).
- `evals/run.sh` — one-command eval reproduction: deterministic checks + scaffold + prompts + judge checklists.
- README: "Try it in 60 seconds" (interview coach, design griller, design mode), griller + eval-runner references.
- `install.sh` + `install.ps1` — auto-detecting installers for every agent/IDE/CLI on the machine (14 targets, idempotent, guarded uninstall, `--list`/`--all`/`--only`/`--project`/`--dry-run`).
- `INSTALL.md` — full 40+ tool install matrix: universal `.agents/skills/` path, per-tool paths, native commands, verification per tool, updating, uninstalling, troubleshooting.
- Six modes: design, map (codebase reverse-engineering), review (10-dimension adversarial rubric), evolve (migration planning), interview (coach + seniority grading), component (decision-table answers).
- The four gates: numbers (capacity math), stress-test (12 failure injections), right-sizing (6-tier table), cost (price catalog + anti-patterns).
- `scripts/botec.py` — stdlib-only back-of-the-envelope calculator with golden tests.
- 14 reference files including LLM-era infrastructure (RAG, vector search, model serving, agents) and 28 classic design problems.
- Output templates (design doc, as-is map, review report, migration plan) with Mermaid snippets.
- Behavioral eval suite (10 evals, with-skill vs baseline) — see `evals/README.md` for methodology and iteration-1 results (with-skill 56/56, baseline 46/56, blind-judged).
- `examples/` — six verbatim outputs produced by the skill in eval runs (design docs, as-is map, review, migration plan, interview grading).
- CI: structure validation, frontmatter checks, calculator tests, eval JSON validation.
- Claude Code plugin manifest for `/plugin marketplace add` installation.
