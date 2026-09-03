---
name: system-design
description: End-to-end system design for real codebases and greenfield problems. Use when the user asks to design or architect a system, map or reverse-engineer an existing architecture, review a design doc/PR/ADR, plan a migration, scaling evolution or service split, choose technologies (SQL vs NoSQL, Kafka vs SQS, cache strategy, sharding), size infrastructure (servers, QPS, storage, cost), or practice system design interviews. Also fires on oblique asks such as "is Postgres enough?", "will this hold at 10x?", "should we split this service?", "write an ADR", "capacity plan for peak", "our DB falls over at peak". Covers capacity math, failure-mode stress testing, right-sizing against over-engineering, cost estimation, distributed-systems fundamentals, and LLM-era infrastructure (RAG, vector search, model serving). Produces ADR-style design docs with Mermaid diagrams, architecture maps, scored reviews, and migration plans. NOT for UI/visual/CSS/logo design, single-query database tuning, or DevOps pipeline debugging.
license: MIT
---

# System Design

Design, map, review, and evolve software systems the way a staff engineer does: numbers first, trade-offs explicit, failures walked, complexity justified. This skill works on both greenfield problems and real codebases.

## Operating principles

1. **Numbers before architecture.** No component enters a design until scale is estimated. Run `scripts/botec.py` and cite the output. A design with no capacity math is an opinion.
2. **Explicit non-goals.** Every design states what it deliberately does not handle. Scope creep is the silent killer.
3. **Every choice names its trade-off.** Format: "X because Y; the cost is Z; revisit when W." A choice presented without a cost is a red flag.
4. **Stress-test before shipping.** Walk the failure injections in `references/stress-tests.md` before finalizing. Designs fail in production, not on the whiteboard.
5. **Right-size, never scale-theater.** Match architecture to actual scale using the tier table in `references/cost.md`. Kafka for 5k users is a bug, not a design.
6. **Ground in the codebase.** When a repository exists, read it before designing. As-is reality beats imagined greenfield.
7. **Artifacts, not chat.** Persist outputs as markdown files (design docs, maps, reviews, plans) so teams can review and diff them.

## Step 0: Detect mode

Classify the request, then follow the matching procedure. When ambiguous, ask one clarifying question or infer from context (codebase present → map/review/evolve likely; no codebase → design/interview likely).

**Open every run with a preamble block** at the top of the first reply, before any analysis:

```
mode: <detected mode> · tier: <0-5, or n/a until known> · inputs: <files/context read>
assumptions: <the 1-3 load-bearing assumptions, each falsifiable>
producing: <the artifact this run ends with>
```

The preamble makes mode misrouting correctable in one turn — the user corrects a plan, not a finished document. The four gates (design, review, evolve) run after the preamble is acknowledged or corrected.

| Mode | Trigger examples | Procedure |
|------|-----------------|-----------|
| **design** | "design X", "architect Y", "how would you build Z", "proposal for..." | `references/method-design.md` |
| **map** | "what does our architecture look like", "map this codebase", "how is X structured" | `references/method-map.md` |
| **review** | "review this design/PR/ADR", "is this architecture sound", "what's wrong with..." | `references/method-review.md` |
| **evolve** | "we're hitting scale on X", "migrate from A to B", "refactor into services", "add multi-region" | `references/method-evolve.md` |
| **interview** | "practice system design", "mock interview", "grade my answer to..." | `references/method-interview.md` |
| **component** | "SQL or NoSQL for...", "cache strategy for...", "how do I shard...", "Kafka vs SQS" | Route via `references/tradeoffs.md` and `references/components.md`; use `references/data-systems.md` for depth |

Modes compose: evolve requires map first (as-is before to-be); interview reuses design as its grading target.

Read the procedure file for the selected mode before proceeding. Do not hold all procedures in context at once.

## The four gates (design, review, evolve modes only)

Gate every substantial design output. A gate failure blocks the output, not just annotates it.

### Gate 1 — Numbers

- Estimate traffic (QPS avg + peak, read:write ratio), storage (with replication and growth horizon), bandwidth, hot-set cache size, and server counts.
- Run `python scripts/botec.py full --dau N --reads-per-user R --writes-per-user W [--write-size B] [--read-size B] [--peak-factor F]` and include the output table in the doc.
- Every major component must trace to a number: "91 TB / 5 yr ⇒ single Postgres is out; partitioned storage is in."
- Constants live in `references/numbers.md`. Never invent latency or capacity numbers; use the table.

### Gate 2 — Stress test

- Walk all 12 failure injections from `references/stress-tests.md`: dependency down, 10x spike, hot key, cache stampede, retry storm, partition/split-brain, poison message, slow consumer, region loss, clock skew, cascading failure, metastable failure.
- For each: does the design survive, degrade, or die? Dying is acceptable only with an explicit redesign note.
- The design doc must include a failure-mode table (see `references/output-templates.md`).

### Gate 3 — Right-sizing

- Classify the system into a tier (0-5) via `references/cost.md`.
- Every component above the tier default requires written justification tied to numbers, not adjectives. Reject "we might need it someday" — note it in the evolution section instead.
- Actively flag over-engineering: message queues, microservices, multi-region, k8s, custom sharding below their tier.

### Gate 4 — Cost

- Produce a rough monthly cost estimate at stated scale (compute, storage, egress, managed services, licenses). Use the price catalog in `references/cost.md` (mark as approximate; verify current pricing).
- State cost per 1k requests or per user per month — a number teams can reason about.
- If two options are technically close, cost decides.

## Mode summaries

Full procedures live in the reference files. Sketches:

### design (greenfield)

Clarify (functional + non-functional + non-goals) → estimate (Gate 1) → high-level (API + data model + diagram; walk one read and one write path) → deep dive the 1-3 hardest components → stress test (Gate 2) → right-size (Gate 3) → cost (Gate 4) → write design doc to `docs/design/YYYY-MM-DD-<name>.md`. Interview practice uses the same loop under time budget. Before declaring the run finished, machine-check the gate outputs: `python scripts/gatecheck.py <doc path>` (exit 0 = all gates produced their artifacts). If script execution is unavailable, verify the same seven checks manually against the quality bar below.

### map (codebase reverse-engineering)

Inventory the repo (entry points, frameworks, manifests, dependencies) → trace request flows (route → handler → service → store) → map data stores and their writers/readers → map infra (deploy, CI) → render C4-container view as Mermaid → list topology risks → write to `docs/architecture/as-is.md`.

### review (adversarial)

Understand intent → score 10 dimensions (requirements, capacity, data design, API, failure containment, scalability, observability, security, cost/right-sizing, evolution) 1-5 with evidence per score → catalog red flags with fixes → verdict: ship / fix-then-ship / redesign. Write report to `docs/architecture/reviews/`.

### evolve (migration)

Confirm the forcing function (scale, cost, feature, risk) → require as-is map → define target state → choose migration patterns (strangler fig, expand-contract, dual-write + backfill + cutover, CDC) → phase the rollout with verification and rollback per phase → risk table for mid-migration failures → write plan to `docs/architecture/`.

### interview (coach)

Pose or accept a problem → run the design loop interactively with the user driving → inject curveballs at natural checkpoints → grade against the seniority rubric (mid/senior/staff) with evidence → name the single highest-leverage improvement.

### component (single decisions)

Answer from the decision tables first (`references/tradeoffs.md`), then deepen (`references/components.md`, `references/data-systems.md`). Always answer: recommended default, when to deviate, and the cost of the choice. Tie to the caller's workload numbers when given.

## Quality bar (self-check before finishing any mode)

- [ ] Scale numbers stated and sourced from botec.py or references/numbers.md
- [ ] Non-goals explicit
- [ ] Every major component justified by a number or a named constraint
- [ ] Trade-offs stated with costs, not just benefits
- [ ] 12 failure injections walked (or explicitly scoped out with reason)
- [ ] Tier assigned; over-tier components justified or removed
- [ ] Cost estimated roughly
- [ ] Output written to a file in docs/ with a Mermaid diagram where visual
- [ ] Claims about the codebase verified by reading it, not assumed
- [ ] Next-step evolution section present (what changes at 10x)

## Reference index

Read these files only when the task needs them. All paths relative to this skill's directory.

| File | Read when |
|------|-----------|
| `references/method-design.md` | Running the design mode (full loop + worked example) |
| `references/method-map.md` | Reverse-engineering a codebase (procedure + commands) |
| `references/method-review.md` | Reviewing a design/PR/ADR (10-dimension rubric + red flags) |
| `references/method-evolve.md` | Planning a migration or scaling evolution |
| `references/method-interview.md` | Coaching or grading a system design interview |
| `references/numbers.md` | Any capacity or latency estimation (constants tables) |
| `references/stress-tests.md` | Gate 2 (the 12 failure injections + antidotes) |
| `references/tradeoffs.md` | Technology choice questions (decision tables) |
| `references/data-systems.md` | Data-layer depth: replication, partitioning, consistency, transactions |
| `references/components.md` | Building-block catalog with capacity numbers |
| `references/problems.md` | Recognizing classic design problems and their key insights |
| `references/llm-infra.md` | LLM/AI workloads: RAG, vector search, serving, agents |
| `references/cost.md` | Gate 3 + 4: tiers, price catalog, cost anti-patterns |
| `references/output-templates.md` | Writing any output artifact (templates + Mermaid snippets) |
| `scripts/botec.py` | Gate 1: capacity math (run it, never hand-wave) |
| `scripts/gatecheck.py` | Machine-checks the four gates' outputs on any design doc (CI + self-check) |

## Rules of engagement

- If the user's ask is vague ("make it scalable"), ask exactly one round of scoping questions (scale? latency SLO? consistency needs? budget?), then proceed with stated assumptions.
- State assumptions explicitly in every artifact; make them falsifiable.
- Prefer boring technology from the tier default unless numbers force otherwise.
- When the codebase contradicts the request, surface the contradiction with evidence (file:line) before designing.
- Never fabricate benchmark numbers or cloud prices; label everything approximate and verifiable.
- Keep diagrams Mermaid-first: they render in GitHub, GitLab, and most docs tools.
