# Method: Review (adversarial design review)

## Contents
- [Inputs](#inputs)
- [Protocol](#protocol)
- [The 10 scoring dimensions](#the-10-scoring-dimensions)
- [Red flag catalog](#red-flag-catalog)
- [Verdicts](#verdicts)
- [Output](#output)

## Inputs

Review targets: a design doc, an ADR, a PR with architectural impact, an as-is map (from method-map), or a described architecture. If reviewing code-as-architecture, run method-map first to get the evidence base.

## Protocol

1. **Understand intent first.** Restate in 3 sentences: what this system/change is trying to achieve, at what scale, with what constraints. Never review against imagined requirements — review against stated ones, and note when stated ones are missing (that's a dimension score).
2. **Score every dimension below 1-5, with evidence.** A score without a cited quote/file/line is invalid. 3 = "defensible, no better than average". 5 = "staff-level defense". 1 = "will cause an incident or block evolution".
3. **Catalog red flags** from the list below (or novel ones) with fixes.
4. **Assign a verdict.**
5. **Write the report** to `docs/architecture/reviews/YYYY-MM-DD-<target>.md` (template in output-templates.md).

Review the design that is, not the design you would have built. Alternative-architecture essays belong in an appendix, one paragraph max, unless asked.

## The 10 scoring dimensions

| # | Dimension | What 5 looks like | What 1 looks like |
|---|---|---|---|
| 1 | Requirements & non-goals | Scale, latency, availability stated; non-goals explicit | No scale statement; scope infinitely elastic |
| 2 | Capacity & numbers | botec-level math drives component choices | Components chosen by fashion |
| 3 | Data design | Store fits access patterns; PK/shard key justified; consistency needs named per flow | One Mongo for everything; no consistency discussion |
| 4 | API & contracts | Clear resource model, error semantics, versioning stance | Verbs-as-endpoints, no error contract |
| 5 | Failure containment | Timeouts/circuit breakers/bulkheads placed; degradation modes named | All dependencies assumed healthy |
| 6 | Scalability path | Bottleneck at 10x named with next step | "We'll add more instances" with a stateful monolith |
| 7 | Observability & ops | Golden signals per endpoint; runbook hooks; alert on symptoms | No metrics story |
| 8 | Security | AuthN/Z model, secrets handling, tenant isolation, input trust boundaries | None of these mentioned |
| 9 | Cost & right-sizing | Tier-appropriate; monthly cost estimated; no over-engineering | Kafka for 5k users; cost never mentioned |
| 10 | Evolution & migration | Rollout phases, rollback, data migration addressed | Big-bang cutover only |

## Red flag catalog

Each flag: why it hurts -> the fix to propose.

**Over-engineering**
- Message broker below tier 2 with no async requirement -> delete until a queue-shaped problem exists.
- Microservices with one team -> modular monolith; split when team count forces it.
- Multi-region below tier 4 -> single region multi-AZ; spend the effort on backups instead.
- Custom sharding below ~500 GB hot data -> vertical scaling and read replicas first.

**Under-engineering**
- No idempotency on money/booking/creation endpoints -> idempotency keys + dedup store.
- Sync third-party calls (payment, email, LLM) on request path without timeout -> queue or async with bounded timeout.
- Single DB primary, no replica, no backup restore test -> replica + tested restore.
- No rate limiting on public endpoints -> gateway-level limiter, 429 + Retry-After.

**Data red flags**
- Dual writes (DB + cache/queue/index as separate calls) -> transactional outbox.
- Distributed transactions across services (2PC) -> saga or restructure ownership.
- Cache over mutable data with TTL-only coherence -> invalidate-on-write or version keys.
- Cross-service synchronous reads in a transaction -> own your data, event-carried state.

**Operational red flags**
- Infinite/no timeouts on outbound calls -> timeout budget per hop, total < SLO.
- Retries without backoff+jitter or budgets -> exponential backoff, full jitter, retry budget.
- Queue consumers with no DLQ -> DLQ + alert on depth.
- Deploy without rollback story -> phased rollout + kill switch.

**Review-craft red flags (about the design doc itself)**
- No numbers anywhere -> demand estimates before evaluating components.
- "Scalable" as a requirement -> force it to a number (QPS, GB, users).
- Trade-offs listing only benefits -> every option must name its cost.
- No failure section -> fail Gate 2 of the review until one exists.

## Verdicts

- **Ship** — all dimensions >= 3, no S1 flags. Minor notes as follow-ups.
- **Fix then ship** — specific identified defects, enumerated, each with the fix. List them as blocking.
- **Redesign** — a dimension scored 1, or 3+ S1 flags, or the shape contradicts requirements. State what the redesign must resolve.

## Output

Report file `docs/architecture/reviews/YYYY-MM-DD-<target>.md` with: summary, scores table (dimension / score / evidence / one-line rationale), blocking findings, non-blocking findings, verdict, and what to re-review after fixes. Score table first — readers should get the verdict in 30 seconds, evidence on demand.
