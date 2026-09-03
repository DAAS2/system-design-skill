# Evals

Behavioral evals for the system-design skill. The claim under test: **with the skill, an agent designs like a senior engineer; without it, like a tutorial.**

## Method

1. Run each prompt in `evals.json` twice: baseline (no skill) and with-skill, fresh session each, same model.
2. Judge each run against the eval's `expected_behaviors` checklist: behavior present = 1, absent = 0. Half-points allowed for partial.
3. Judge blind: outputs are anonymized as `run-1` / `run-2` with randomized arm assignment; judges never see which run used the skill.
4. Record per-eval scores and totals below, per iteration.

### Protocol details

- **Arms.** Every eval runs in two fresh agent sessions: *baseline* receives only the user prompt; *with-skill* receives the same prompt plus the skill installed at a neutral path and is told to read `SKILL.md` and follow it (its own progressive disclosure decides which references load — exactly how an auto-triggered skill behaves in Claude Code, minus the trigger itself).
- **Fixtures.** The map eval runs against `fixtures/demo-app` (a small FastAPI orders service with planted, realistic debt: no Stripe timeout, no idempotency, TTL-only cache, Redis-list queue with no DLQ, single unbacked Postgres). The interview eval grades `fixtures/interview-transcript.md` (a deliberately weak candidate performance).
- **Judging.** Each behavior is scored 0 / 0.5 / 1 with quoted evidence; artifact behaviors require the file to actually exist in the run directory with substance. Judge sessions are independent of the run sessions.
- **Caveats.** Skill auto-trigger is not tested here (the skill was force-loaded). Scores reflect one model, one date; different models will differ — run your own comparison and publish it.

## Deterministic checks

Not everything is subjective. CI runs the golden tests for the calculator:

```
cd system-design/scripts && python -m unittest test_botec
```

CI also runs `tools/validate_skill.py` (structure), `tools/validate_evals.py`, and `tools/validate_trigger_evals.py`.

## Trigger evals

The behavioral evals above **force-load** the skill, so they measure what the skill does once active — never whether it loads at all. Invocation is the higher-risk behavior: the model matches a task against one `description:` line, usually implicitly. A skill that never fires on real phrasing has an effective score of zero regardless of its gates.

`trigger_evals.json` addresses this with 20 labelled queries (10 train, 10 validation; half should-trigger, half must-not), each judged by asking a fresh agent — shown the skill's actual description — whether it would load the skill for that query, **3 repetitions per query**. `./run_triggers.sh` prints the prompts and the tally template.

Scoring per set:

- `trigger-rate` = mean rate over `should_trigger: true` cases → want **high** (≥0.5 minimum, ≥0.8 target)
- `false-load-rate` = mean rate over `should_trigger: false` cases → want **low** (≤0.5 minimum, ≤0.2 target)

The train set exists to tune the description (oblique phrasings, explicit exclusions); the validation set is the held-out verdict — never tune on it. Should-not cases concentrate on collision-heavy territory: "design a logo" (visual design), single-query DB tuning, pipeline debugging, framework pickers. When you change the description, re-run the train set first, then the validation set; publish both tables as a PR.

**Status (2026-09-04): the suite has a published run.** `./run_triggers.sh --auto --tool opencode` executed all 20 cases against the host CLI (OpenCode, default model), recording both the YES/NO self-report and behavioral evidence (whether the host actually loaded the skill, parsed from the tool's own load log):

| Set | Trigger rate (said yes) | False-load rate | Behavioral load | Behavioral false-load |
|---|---|---|---|---|
| train (10) | **1.00** | **0.00** | **1.00** | **0.00** |
| validation (10) | **1.00** | **0.00** | **1.00** | **0.00** |

Verdict: **PASS** (threshold 0.5; target ≥0.80/≤0.20 met). Scope, honestly: one tool, one model (OpenCode's default), n=1 per case, run 2026-09-03/04 — full per-case table in `out/triggers/opencode-2026-09-04/results-opencode-2026-09-04.md`. Every should-trigger query — including the oblique ones ("should we split this service", "is Postgres enough", "our DB is falling over at peak") — behaviorally loaded the skill; every should-not query ("design a logo", CSS, single-query tuning, pipeline debugging) correctly rejected it. **Claude Code and Codex tallies are the next most wanted data points** — the CLI is the only thing that changes:

```bash
bash evals/run_triggers.sh --auto --tool claude --reps 3
bash evals/run_triggers.sh --auto --tool codex  --reps 3
```

The train set exists to tune the description (oblique phrasings, explicit exclusions); the validation set is the held-out verdict — never tune on it. When you change the description, re-run the train set first, then the validation set; publish both tables as a PR.

## Iteration log

### Iteration 1 — 2026-08-30

20 fresh agent sessions (10 evals x 2 arms), blind-judged by 10 independent judge sessions. Same model for both arms.

| Eval | Max | With-skill | Baseline | Where baseline lost points |
|---|---|---|---|---|
| design-url-shortener | 7 | **7** | 4.5 | Kafka + multi-region + microservice split at ~5k rps (scale theater); no stampede analysis; ASCII not Mermaid; shallow non-goals |
| design-rate-limiter | 5 | **5** | 4 | No hot-key treatment for a single very active API key |
| right-size-pushback | 4 | **4** | 3.5 | Quantified QPS but never storage; peak estimate 30x too high |
| map-codebase | 7 | **7** | 4 | No diagram, no data-store map, no as-is artifact file |
| review-flawed-design | 6 | **6** | 5 | No scored dimensions; verdict lacked enumerated blocking framing; no cost |
| evolve-monolith-extract | 7 | **7** | 6 | No as-is understanding; endorsed app-level dual-write (the classic divergence bug) |
| component-sql-vs-nosql | 4 | **4** | 4 | — (narrow question; both strong) |
| estimate-capacity | 4 | **4** | 3.5 | Never raised label-cardinality / TSDB-shape concern for the metrics workload |
| design-rag-pipeline | 6 | **6** | 6 | — (both strong on the checklist) |
| interview-coach | 6 | **6** | 5.5 | No single "one thing"; feedback diluted across 7 co-equal fixes |
| **Total** | **56** | **56 (100%)** | **46 (82%)** | |

**Readings:**

- With the skill, every eval passed in full; baseline lost points in 8 of 10 evals.
- The skill's biggest wins are *process discipline*: artifacts that exist (design docs, maps, reports), diagrams that render (Mermaid), right-sizing pushback backed by numbers, estimation before components, non-goals, and failure-mode walks. Baseline fails most loudly on exactly the behaviors working engineers care about — scale theater in the URL shortener, missing artifacts in the codebase map.
- Baseline is strongest where the question is narrow and well-trodden (SQL vs NoSQL, RAG checklist). The skill's value concentrates where ambiguity, money, or failure are involved — which is where senior judgment actually matters.
- Judge-noted examples of with-skill strengths: "stampede-by-construction" reasoning in the URL shortener (immutable slugs + cache-forever = no TTL storm, single-flight bounds misses); the 12-injection failure table in the rate limiter; the forcing-function discipline in the migration plan (capacity math used to *disprove* scale as the driver); ACL-correct cache keys in the RAG design.
- **Skill changes from this iteration: none to the skill body.** Candidate follow-ups logged: (1) baseline RAG/component evals already pass — keep those checklists honest rather than inflating them; (2) with-skill runs occasionally cite `botec.py` without pasting its output. Both follow-ups shipped 2026-09-03 as tooling: `evals/trigger_evals.json` + `run_triggers.sh` (the force-loading gap above) and `scripts/gatecheck.py` (machine-checks the gate outputs, including the botec output block, in CI and on any design doc).