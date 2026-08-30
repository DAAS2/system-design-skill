# Method: Design (greenfield)

## Contents
- [Phase 1: Clarify](#phase-1-clarify)
- [Phase 2: Estimate](#phase-2-estimate)
- [Phase 3: High-level design](#phase-3-high-level-design)
- [Phase 4: Deep dive](#phase-4-deep-dive)
- [Phase 5: Stress test](#phase-5-stress-test)
- [Phase 6: Right-size and cost](#phase-6-right-size-and-cost)
- [Phase 7: Write the doc](#phase-7-write-the-doc)
- [Worked example](#worked-example-url-shortener-abbreviated)

Run this loop for "design X" requests with no existing codebase (or when explicitly greenfield). Time budget for interactive/interview use: 45 min total — 10 clarify, 5 estimate, 10 high-level, 15 deep dive, 5 stress + wrap.

## Phase 1: Clarify

Extract three lists. Ask at most one round of questions, then proceed with stated assumptions.

**Functional requirements** — pick the 2-3 core features the system exists for. Everything else is out of scope. Write them as verbs: "shorten URL", "redirect", "view basic analytics".

**Non-functional requirements** — scale, latency, availability, consistency, durability, security/compliance, budget. If the user gives none, assume from the tier table (references/cost.md) and say so.

**Non-goals** — explicit "we will NOT handle X" list. Typical: no offline sync, no multi-region at launch, no custom client apps, no GDPR deletion pipeline v1.

Question bank (pick the ones the request leaves open):

| Question | Why it matters |
|---|---|
| How many daily active users / events? | Everything downstream |
| Read-heavy or write-heavy? Ratio? | Cache vs queue vs partition strategy |
| Latency SLO? (p50/p99, ms vs s) | Sync vs async paths, CDN, region placement |
| Availability target? (nines) | Multi-AZ vs multi-region, failover design |
| Strong consistency or eventual OK? Where exactly? | Datastore choice, replication mode |
| Read-after-write needed? For whom (author vs everyone)? | Cache invalidation, session routing |
| Data retention? Deletion obligations? | Storage tiering, hard-delete paths |
| Who are the users? Mobile/web/internal? | Edge strategy, auth model |
| Existing constraints? (stack, cloud, budget, team size) | Managed vs self-hosted, build vs buy |

## Phase 2: Estimate

Run the calculator:

```
python scripts/botec.py full --dau <N> --reads-per-user <R> --writes-per-user <W> \
  --read-size <B> --write-size <B> --peak-factor <F> --years <Y> --replication <X>
```

Include the output table in the design doc. Then write one sentence per major decision the numbers force, e.g.:

- "25 TB / 5 yr with 3x replication => partitioned storage or object storage; single-node DB is out."
- "Peak 40k read QPS, 100:1 read:write => cache layer is load-bearing, not optional."
- "p99 50 ms SLO => no cross-region hop on the read path; region-local reads."

Rules: state every assumption as falsifiable ("assuming 100 bytes/record, 2 min avg session"). Constants come from references/numbers.md — never invent them. Round aggressively; the process matters more than precision.

## Phase 3: High-level design

Produce, in this order:

1. **API surface** — 3-6 endpoints or message contracts. Name them. (REST verbs, or gRPC/queue topics if async.)
2. **Data model** — entities, primary key, the one or two access patterns per entity that drive the store choice.
3. **Diagram (Mermaid)** — boxes: client, edge, services, stores, queues. Follow `references/output-templates.md` snippets.
4. **Walk one write path and one read path end-to-end, out loud.** This is where hidden components surface (auth, idempotency, fanout).

Present the high-level to the user for a buy-in checkpoint before deep diving. Do not polish; get agreement on shape first.

## Phase 4: Deep dive

Deep dive only the 1-3 components where the hard problems actually live. Choose from:

- Data store choice + schema + partition key (the usual #1)
- Cache strategy + invalidation + stampede protection
- Fanout / hot-key strategy (feeds, celebrity writes)
- Consistency transactions across services (outbox/saga)
- Delivery semantics (idempotency, ordering, retries)
- The domain's core algorithm (matching, ranking, geospatial, matching engine)

Use `references/tradeoffs.md` and `references/data-systems.md` for options and their costs. Format every choice: **"X because Y; cost Z; revisit when W."**

Check `references/problems.md` first — if the request is a classic problem, start from its known hard part instead of re-deriving.

## Phase 5: Stress test

Walk all 12 injections from `references/stress-tests.md`. Produce the failure-mode table (template in output-templates.md):

| Injection | Behavior | Mitigation |
|---|---|---|
| Cache cluster down | ... | ... |

Survive / degrade / die for each. "Degrade" answers must say what the degraded behavior IS (stale reads? queue backlog? 503 on non-core features?).

## Phase 6: Right-size and cost

- Assign the tier (references/cost.md). If any component sits above tier default, either justify with a number from Phase 2 or delete it.
- Rough monthly cost at stated scale; cost per 1k requests. Two finalists close on tech? Cost decides.
- Add the evolution section: what breaks first at 10x, what the next architecture step is.

## Phase 7: Write the doc

Write `docs/design/YYYY-MM-DD-<name>.md` using the design-doc template (references/output-templates.md). Sections: Context, Requirements + Non-goals, Assumptions + Estimates (botec output), High-level (diagram + walk-through), Deep dives, Failure modes, Right-sizing + Cost, Evolution, Open questions.

Self-check against the quality bar in SKILL.md before finishing.

---

## Worked example: URL shortener (abbreviated)

Clarified: shorten, redirect, 30-day analytics. 100M DAU-reads, 1M new URLs/day. p99 redirect < 100 ms. Non-goals: custom aliases v1, private links, edit-after-create.

Estimate (botec, abbreviated): read QPS avg ~1.2k, peak ~4k (peak 3x); write ~12 avg. Storage 1M x 500 B x 3x = 1.4 GB/day, 2.5 TB / 5 yr. Numbers force: cache is load-bearing (100:1 read:write); storage trivial at this scale — single region, no sharding needed yet.

High-level: `POST /urls {long_url} -> {slug}`; `GET /:slug -> 301`. Store: single Postgres (slug PK, long_url, created_at, owner_id) — 2.5 TB / 5 yr fits one primary + replica comfortably. Redirect: edge cache (slug immutable => cache forever, TTL 1 yr) then app cache then DB.

Deep dive: ID generation — base62 of a Snowflake-style 64-bit ID (timestamp|node|seq): no coordination, sortable, collision-free; hash-and-check rejected (extra round trip, collision handling). 301 vs 302: 301 caches at browsers (faster, less load) but loses click analytics; 302 keeps analytics at cost of latency — product decision, flag it.

Stress test highlights: hot slug (viral link) => edge + app cache absorb, DB never sees hot reads; cache stampede on expiry => slugs are immutable so stale-while-revalidate is trivially safe; write burst (bot spam) => rate limit per IP + per-account.

Right-size: Tier 1-2. Monolith + managed Postgres + Redis + CDN. No Kafka, no k8s, no microservices. Cost ~ $150-400/mo at this scale.

Doc written to `docs/design/2026-08-30-url-shortener.md` with Mermaid diagram.
