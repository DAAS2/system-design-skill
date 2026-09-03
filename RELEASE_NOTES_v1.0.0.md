# RELEASE NOTES — v1.0.0 (paste into the GitHub Release; delete this file after publishing)

**Tag:** `v1.0.0` · **Date:** 2026-09-03 · **Status:** first public release

## system-design — a staff engineer's system design brain for your coding agent

An Agent Skills folder that makes AI coding agents design, map, review, and evolve software systems with capacity math, failure analysis, right-sizing, and cost accounting — enforced as hard gates, not suggestions. Works on the codebase you actually run. One lean skill, 40+ agent tools, no network, no keys, no telemetry.

## Highlights

- **Six modes, auto-detected:** design · map · review · evolve · interview · component
- **Four enforcement gates** that block output rather than annotate it: numbers (capacity math), stress-test (12 failure injections), right-sizing (six-tier table, prototype → planetary), cost (monthly bill + per-1k requests)
- **`scripts/botec.py`** — stdlib-only, deterministic capacity calculator with golden tests; every component must trace to a number
- **`scripts/gatecheck.py`** — machine-checkable gate contract: parses any design doc and exits non-zero if a gate output (capacity block, 12-injection table, tier line, cost figures, non-goals, evolution path) is missing. Runs in CI against the repo's own examples; run it on yours
- **14 progressive-disclosure references** — DDIA / Alex Xu / Google SRE / classic papers lineage, plus the LLM-era layer (RAG, vector search, KV-cache serving physics, GPU scheduling)
- **Published eval suite** — 20 fresh sessions, blind-judged: with-skill 56/56 (100%), baseline 46/56 (82%). One model, one date, force-loaded — reproduce with `./evals/run.sh`
- **Trigger evals** — `evals/trigger_evals.json` + `./evals/run_triggers.sh`: 20 labelled queries (train/validation) measuring whether the skill *fires* on real phrasing, including oblique asks ("is Postgres enough?", "should we split this service?") and should-not collisions ("design a logo"). The first filled tally closes the auto-trigger caveat
- **Mode + assumptions preamble** (Gate 0) — every run opens with detected mode, tier, inputs read, and assumptions, so misrouting is correctable in one turn
- **Install** — `npx skills add DAAS2/system-design-skill --agent '*'`, or copy `system-design/` into `~/.agents/skills/`

## Verification

- CI on every push: structure validation, frontmatter budgets, botec + gatecheck golden tests, evals/trigger-evals JSON validation, installer dry-run
- Reproduce the evals: `./evals/run.sh` — publish your model's numbers as a PR
- Reproduce the trigger test: `./evals/run_triggers.sh --prompts`

## Sources

Sources line for the record: eval figures from `evals/README.md` (iteration 1, 2026-08-30); gate contract from `SKILL.md`; price/scale references from `references/cost.md` (labelled approximate — verify current pricing).
