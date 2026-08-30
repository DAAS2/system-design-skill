# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/) — MAJOR when the method changes incompatibly, MINOR for new content, PATCH for corrections.

## [1.0.0] - 2026-08-30

### Added
- Six modes: design, map (codebase reverse-engineering), review (10-dimension adversarial rubric), evolve (migration planning), interview (coach + seniority grading), component (decision-table answers).
- The four gates: numbers (capacity math), stress-test (12 failure injections), right-sizing (6-tier table), cost (price catalog + anti-patterns).
- `scripts/botec.py` — stdlib-only back-of-the-envelope calculator with golden tests.
- 14 reference files including LLM-era infrastructure (RAG, vector search, model serving, agents) and 28 classic design problems.
- Output templates (design doc, as-is map, review report, migration plan) with Mermaid snippets.
- Behavioral eval suite (10 evals, with-skill vs baseline) — see `evals/README.md` for methodology and iteration-1 results (with-skill 56/56, baseline 46/56, blind-judged).
- `examples/` — six verbatim outputs produced by the skill in eval runs (design docs, as-is map, review, migration plan, interview grading).
- CI: structure validation, frontmatter checks, calculator tests, eval JSON validation.
- Claude Code plugin manifest for `/plugin marketplace add` installation.
