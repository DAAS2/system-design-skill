# Cost & right-sizing: tiers, prices, anti-patterns

Cost is a design constraint with the same standing as latency and availability. Two tools here: the **tier table** (right-sizing gate) and the **price catalog** (cost gate).

## Contents
- [The tier table](#the-tier-table)
- [Component tax](#component-tax)
- [Rough price catalog (2026, approximate)](#rough-price-catalog-2026-approximate)
- [Cost anti-patterns](#cost-anti-patterns)
- [Cost estimation method](#cost-estimation-method)

## The tier table

Classify the system by scale, then hold components to the tier default. Anything above the tier default needs written justification tied to a number.

| Tier | Users/day | Shape (tier default) |
|---|---|---|
| 0 — Prototype | < 1k | One monolith, managed DB, no queue, no cache, no HA. One VM/PaaS. Backups yes |
| 1 — Traction | 1k-50k | 2+ app nodes behind LB, managed DB + replica, Redis cache, managed queue for email/jobs, CDN for assets |
| 2 — Growth | 50k-500k | Read replicas, real cache strategy, async pipelines, multi-AZ, SLOs + dashboards, rate limiting, search index if search-shaped |
| 3 — Scale | 500k-5M | Partitioning decisions (native first), idempotency everywhere, multi-region reads or active-passive DR, event streaming, dedicated OLAP |
| 4 — Platform | 5M-50M | Multi-region writes or geo-partitioning, consensus where the domain demands, data platform team, self-managed where economics force it |
| 5 — Planetary | 50M+ | Custom infra economics, edge compute, bespoke storage — the interesting problems return |

The table's job is to prevent **scale theater**: designing tier-4 architecture for tier-1 traffic. Over-engineering isn't extra safety — it's extra failure surface, slower shipping, and ops cost with no return.

## Component tax

Every component charges rent beyond its price:

| Component | Hidden tax |
|---|---|
| Kafka | Cluster ops, partition planning, consumer group management, schema governance — a platform unto itself |
| Microservices | Distributed txns, network failure handling, observability, platform team, deploy coordination |
| Kubernetes | Control-plane expertise, upgrade treadmill, security surface — often heavier than the app |
| Multi-region | Data conflict strategy, replication cost, failover drills, region-aware routing |
| Custom sharding | Rebalancing pain, cross-shard ops, app complexity — earn it with a number first |
| Self-hosted DB | Backup/restore drills, upgrades, failover, on-call — a team's worth |

Rule: the tax is payable, but only when the tier forces it.

## Rough price catalog (2026, approximate)

Ballpark for gate-4 estimates. Label every estimate "approximate — verify current pricing." Managed convenience multiplies raw cost 2-5x — that's usually correct for small teams (see tradeoffs.md managed-vs-self-hosted).

| Item | Rough price |
|---|---|
| VM 4 vCPU / 16 GB | $30-70/mo reserved, ~$70-140 on-demand (varies by cloud/region) |
| Managed Postgres (2 vCPU, 8 GB, multi-AZ) | $100-250/mo |
| Managed Postgres HA at tier-3 scale | $1-5k+/mo |
| Redis/ElastiCache small node | $30-80/mo |
| Object storage | ~$0.02/GB-mo standard; ~$0.004-0.01 infrequent/cold |
| Egress (the silent killer) | ~$0.05-0.12/GB; 10 TB/mo out = $500-1,200/mo |
| CDN | ~$0.01-0.08/GB delivered |
| SQS-ish queues | ~$0.40/million requests |
| Managed Kafka | $200-1,000+/mo entry |
| Load balancer | $15-30/mo + LCU usage |
| Serverless (Lambda-class) | $0.20/million requests + GB-s |
| LLM API tokens | Rough order: small models ~$0.1-0.5 /M tokens, frontier ~$1-10 /M in / $2-15 /M out (verify!) |
| GPU (H100-class on-demand) | $2-4/hr/GPU cloud; $1-2 spot/committed |
| Domain + certificates | ~$10-60/yr (certs free: Let's Encrypt / cloud ACME CAs) |

Costs that surprise teams, in order of frequency: **egress**, idle autoscaled environments, orphaned volumes/snapshots, LLM tokens (uncontrolled agents), cross-AZ traffic (fractions of a cent x millions), and managed-DB backup storage.

## Cost anti-patterns

- **Scale theater** — Kafka + k8s + microservices at tier 1 (see tier table).
- **Egress blindness** — serving media/ML responses from origin instead of CDN; cross-region replication without budgets.
- **Idle fleet** — dev/staging running 24/7; autoscale groups with min=3 for a tier-0 app.
- **No per-feature cost attribution** — can't see which feature burns the money.
- **Unbounded LLM spend** — no caching, no routing, no token budgets per workflow.
- **Over-provisioned DBs** — "just in case" 64 GB instance for a 2 GB database.
- **Dual systems during migration that never end** — evolution plans without contract phase (see method-evolve.md).

## Cost estimation method

1. Enumerate billable resources from the design (nodes, DB, cache, storage, egress, queue ops, third-party APIs, LLM tokens).
2. Multiply by catalog prices; sum. State assumptions ("1.4 GB/day ingest, 3-year retention, 10% monthly egress").
3. Normalize: **cost per 1k requests** and **cost per user per month** — numbers a PM can reason with.
4. Sanity-check against the tier: cost wildly above tier norms usually means over-engineering; wildly below usually means forgotten HA/backup/storage lines.
5. Record in the design doc: table + total + the top 2 cost levers ("CDN offload cuts bill ~40%").
