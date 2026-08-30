# Numbers: estimation constants

Source of truth for every estimate. Never invent a constant — take it from here, and say when you rounded. (Lineage: Jeff Dean's latency numbers, System Design Interview ch. 2, Google SRE, 2026 hardware updates including LLM serving.)

## Latency numbers every programmer should know

| Operation | ~Latency (2026) |
|---|---|
| L1 / L2 / L3 cache reference | 0.7 ns / 2.5 ns / 8 ns |
| Mutex lock, uncontended | ~25 ns |
| Main memory reference | ~90 ns |
| Compress 1 KiB (LZ4/Zippy) | 1-3 us |
| NVMe SSD, 4 KiB random read | 20-100 us |
| Read 1 MiB sequentially: memory / SSD / HDD | ~10 us / ~100 us / ~6 ms |
| HDD seek (mechanical floor) | ~10 ms |
| Same-DC network round trip | 200-500 us |
| Cross-zone round trip | ~1 ms |
| Cross-region RTT (US<->EU / US-East<->US-West) | 70-150 ms / ~40-70 ms |
| Redis GET, same DC | 0.2-1 ms |
| Simple indexed Postgres query | 1-5 ms |
| S3 PUT small object | 10-50 ms |
| TLS handshake + one HTTPS round trip | 50-250 ms |
| LLM API call: short answer / long-context prefill / reasoning | ~3 s / ~10 s / ~30 s+ |

Rules of thumb: an LLM call is 10^4-10^6x a Redis hit — architect LLM paths async/cache-first. Anything cross-region on a request path costs >= 70 ms; a p99 < 100 ms SLO forbids cross-region hops.

## Availability nines

| Availability | Downtime/year | Error budget (30d) | Notes |
|---|---|---|---|
| 99% ("two nines") | 3.65 days | 43.2 min | Dev environments, internal tools |
| 99.9% | 8.76 hours | 4.32 min | Normal SaaS default |
| 99.99% | 52.6 min | 25.9 s | Needs multi-AZ, real on-call |
| 99.999% | 5.26 min | 2.59 s | Needs redundancy everywhere, no human in the loop |
| 99.9999% | 31.5 s | 0.26 s | Careful engineering + luck |

Each additional nine costs roughly 10x effort/money. Composite: a chain of N components each 99.9% yields 99.9%^N — five in series drops below 99.5%. State nines per user-facing flow, not per component.

## Powers of two & sizes

| Power | Value |
|---|---|
| 2^10 / 2^20 / 2^30 | 1 K / 1 M / 1 B (approx) |
| 2^40 / 2^50 | 1 TiB / 1 PiB |

Data sizes: char 1 B (2 in Java/UTF-16), uint32 4 B, uint64/timestamp 8 B, UUID 128 B, typical DB row 0.5-1 KiB, tweet ~300 B + media, URL record ~500 B, photo ~2-5 MB, minute of HD video ~50-100 MB. Small objects in object stores have per-object overhead — batch small objects.

## Traffic math

- **DAU -> QPS**: daily events / 86,400. 1M users doing 1 event/day each = ~12 QPS average.
- **Peak factor**: 2-3x typical consumer traffic, up to 10x for login-spike/product-launch workloads.
- **Read:write ratios**: URL shortener ~100:1, feed ~100:1, chat ~1:1 (writes dominate pipelines), payments ~10 writes:1 read (write-heavy).
- **Little's Law**: concurrency = throughput x latency. 10k QPS at 200 ms avg = 2,000 in-flight requests — size thread pools, connections, queues for this, or the queue forms inside your latency.

## Storage math

- Daily growth = writes/day x record size x replication factor (3x typical).
- 5-year horizon = daily x 365 x 5, apply growth compounding if > 1.2x/yr.
- Always include: replication, indexes (~1-1.5x data), logs/telemetry (often bigger than the data).
- Cache hot set: 80/20 rule — 20% of daily-written objects serve ~80% of reads.

## Reference service capacities (order of magnitude, per node)

| Service | Throughput |
|---|---|
| Stateless web/API node | 1-10k RPS |
| Postgres/MySQL, simple indexed ops | 5-10k QPS read replica / 1-5k writes primary |
| Postgres/MySQL, complex queries/joins | 100-1k QPS |
| Redis / Memcached | 100k-1M ops/s |
| Kafka broker (batched, sequential) | 100k-1M msg/s; ~hundreds of MB/s |
| Cassandra/DynamoDB node | ~10k writes/s sustained |
| Elasticsearch query (filtered, indexed) | 100s-1k QPS per node |
| CDN edge hit | effectively unbounded horizontally |
| HNSW vector query | 1-10 ms at 95-99% recall (1-100M vectors) |
| vLLM-class LLM serving node (1 GPU) | ~1-10k output tok/s aggregate (batched, model-dependent) |

Treat these as ceiling-ish defaults; real numbers depend on record size, hardware, and tuning. The purpose is sanity-checking, not benchmarking.

## Estimation etiquette

- Round to 1-2 significant digits: "about 40 TB", not "41.3 TB".
- Show the formula, then the answer: `1M writes/day x 500 B x 3 = 1.4 GB/day`.
- Tie every number to a decision; a number that changes nothing is decoration.
- When a number is a guess, mark it: "(assumes 2 min avg session — verify)".
