# system-design

**Give your coding agent a staff engineer's system design brain.**

Every other system design tool teaches an agent to whiteboard "design WhatsApp" from scratch. This one does the job you actually have: it **reads your codebase, maps the architecture you really run, reviews designs like a hostile staff engineer, and plans the migration** — with the capacity math, failure analysis, right-sizing, and cost accounting to back every claim.

```
Without the skill:                With the skill:
"You should use Kafka,            "50k DAU is tier 1: monolith + managed Postgres +
 Kubernetes, and microservices     replica. Kafka at this scale is a tax, not a tool.
 for scalability!"                 Here's the math. Here's what breaks first at 10x,
                                   and the tripwire that would justify Kafka later."
```

## What it does

Six modes, auto-detected from the request:

| Mode | Ask things like | Get |
|---|---|---|
| **Design** | "design a URL shortener for 100M daily reads" | ADR-style design doc + Mermaid diagram in `docs/design/` |
| **Map** | "what does our architecture actually look like?" | Reverse-engineered as-is map: components, flows, data stores, risk register — every claim cites a file path |
| **Review** | "review this design doc / PR / ADR" | 10-dimension scored report: blocking findings, verdict (ship / fix-then-ship / redesign) |
| **Evolve** | "our monolith payments code is blocking releases" | Phased migration plan (strangler fig, outbox, dual-write + backfill + cutover) with rollback at every phase |
| **Interview** | "mock system design interview, grade me hard" | Curveball-injecting coach + mid/senior/staff rubric grading with evidence |
| **Component** | "SQL or NoSQL?", "Kafka vs SQS?", "cache strategy?" | Decision-table answers: default, when to deviate, cost of the choice |

## The four gates

Every design/review/evolve run must pass four gates before it's allowed to finish. This is what makes the difference between a junior-sounding answer and a senior one:

1. **Numbers gate** — capacity math runs first (`botec.py`, bundled calculator), and every component traces to a number: *91 TB / 5 yr ⇒ single Postgres is out.*
2. **Stress-test gate** — the design walks all 12 failure injections: dependency down, 10x spike, hot key, cache stampede, retry storm, split-brain, poison message, slow consumer, region loss, clock skew, cascading failure, metastable failure.
3. **Right-sizing gate** — the design is tier-checked (prototype → planetary). Kafka for 5k users isn't "enterprise-grade", it's a bug. Over-tier components get deleted or justified with numbers.
4. **Cost gate** — rough monthly bill + cost per 1k requests. Two options technically close? Cost decides.

## Before / after

**You:** "Design a rate limiter for our API across 100 gateway nodes."

**Without gates** you get a Wikipedia article: *"There are several algorithms... token bucket is popular..."* — no numbers, no decision, no failure behavior.

**With the skill:**

```
  Read QPS avg / peak        2,400.0 / 7,200.0
  Decisions these numbers force:
  - peak read QPS > 10k: cache layer mandatory; CDN if cacheable

Algorithm: sliding window counter (default) — fixed window's boundary-burst
is unacceptable for an API product; sliding log's per-key memory is not.
Distributed state: Redis counters, atomic via Lua. The limiter fails OPEN
on Redis outage — availability of the API outranks abuse control; flag
this as a product decision to confirm.
Contract: 429 + Retry-After, enforced AFTER authN (unauthenticated floods
must not pass).
Hot-key: single heavy tenant -> in-process micro-cache with 100ms sync;
at 100x that, dedicated shard for the whale.
```

## Install

The skill folder is `system-design/` — standard Agent Skills format, works everywhere skills do.

| Tool | Install |
|---|---|
| Any (CLI) | `npx skills add <github-user>/system-design-skill` |
| Claude Code | copy `system-design/` into `~/.claude/skills/` (personal) or `.claude/skills/` (project) |
| Claude Code plugin | `/plugin marketplace add <github-user>/system-design-skill` then `/plugin install system-design` |
| Claude.ai | zip the `system-design/` folder → Settings → Skills → upload |
| OpenCode | copy into `.opencode/skills/` or `~/.config/opencode/skills/` |
| Codex / Gemini CLI / Cursor / Windsurf | copy into the tool's skills directory (all support the Agent Skills standard) |

Verify: ask *"how would you architect a ticket booking system?"* — you should see capacity math before components, not a component zoo.

## What's inside

```
system-design/
├── SKILL.md                 # mode router + the four gates (lean by design)
├── scripts/
│   ├── botec.py             # capacity calculator (QPS, storage, bandwidth, cost forces)
│   └── test_botec.py        # golden-value tests
└── references/              # loaded on demand — zero context cost until needed
    ├── method-design.md     # the design loop + worked example
    ├── method-map.md        # codebase reverse-engineering procedure + commands
    ├── method-review.md     # 10-dimension adversarial rubric + red-flag catalog
    ├── method-evolve.md     # migration pattern library + phasing skeleton
    ├── method-interview.md  # coach protocol + seniority rubric + curveballs
    ├── stress-tests.md      # the 12 failure injections + antidotes
    ├── numbers.md           # latency/nines/capacity constants (2026, LLM included)
    ├── tradeoffs.md         # decision tables: SQL vs NoSQL, push vs pull, queues...
    ├── data-systems.md      # replication, partitioning, consistency, transactions (DDIA distilled)
    ├── components.md        # building-block catalog with capacity numbers
    ├── problems.md          # 28 classic designs + the one insight that matters in each
    ├── llm-infra.md         # RAG, vector search, LLM serving, agents, GPU scheduling
    ├── cost.md              # tier table, price catalog, cost anti-patterns
    └── output-templates.md  # design doc / map / review / plan templates + Mermaid
```

Knowledge lineage: DDIA (Kleppmann), System Design Interview Vol 1-2 (Alex Xu), Google SRE + Release It!, and the classic papers (Dynamo, Spanner, Aurora, Kafka, Raft, Tail at Scale, PagedAttention) — distilled into checklists an agent will actually enforce, plus the LLM-era layer (RAG, vector search, vLLM-class serving) that predates most system design material.

## Evals

`evals/` ships 10 behavioral evals (with-skill vs baseline, judge rubric included) plus deterministic golden tests for the calculator. CI validates skill structure, frontmatter, and reference integrity on every push. Run your own comparison: `evals/README.md`.

## Design principles of this skill

- **Numbers before architecture.** A design with no capacity math is an opinion.
- **Ground in the codebase.** Claims cite `file:line`, not vibes.
- **Right-size.** Boring technology at the right tier beats scale theater every time.
- **Reversibility.** Migrations keep a rollback path until the last deliberate, dated step.
- **Artifacts, not chat.** Output lands in `docs/` where teammates can review and diff it.

## Contributing

Issues and PRs welcome — especially: better golden numbers (with sources), new failure injections, new red flags, and eval results from your runs.

## License

MIT
