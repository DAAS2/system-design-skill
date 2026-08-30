# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/) — MAJOR when the method changes incompatibly, MINOR for new content, PATCH for corrections.

## [1.0.0] - 2026-08-30

### Added
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
