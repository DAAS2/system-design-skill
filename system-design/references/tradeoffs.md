# Trade-offs: decision tables for technology choices

Answer component questions from these tables: recommended default, when to deviate, cost of the choice. Always tie to the caller's workload numbers when available.

## SQL vs NoSQL vs NewSQL

| Option | Choose when | Real cost |
|---|---|---|
| Relational (Postgres/MySQL) | Default. Transactions, complex queries, evolving schema, < ~1-5 TB hot, < ~5-10k write QPS primary | Vertical ceiling; sharding is manual pain |
| Document (Mongo/DynamoDB/Firestore) | Self-contained aggregates, flexible/nested shapes, huge write scale with simple access patterns | No joins across aggregates; consistency and migration discipline on you |
| Wide-column (Cassandra/Bigtable) | Massive write throughput, time-series/log-shaped, queries dominated by partition key | No ad-hoc queries; design the table per query pattern |
| KV (Redis/DynamoDB) | Latency-critical lookups, caches, sessions | No query flexibility; memory cost (Redis) |
| NewSQL (Spanner/CockroachDB/FoundationDB/Yugabyte) | Need SQL + horizontal scale + strong consistency, and can pay for it | Higher latency floor (consensus writes), cost, operational maturity |
| Graph (Neo4j) | Deep relationship traversal (fraud rings, social graphs) | Niche; don't reach without traversal queries |

Default: Postgres. Deviate on evidence (numbers), not fashion. One more note: "NoSQL because scale" is usually wrong — most systems fit comfortably on one relational primary until far past 1M users.

## Sync vs async replication

| | Sync | Async |
|---|---|---|
| Trade | Latency (wait for replica) | Possible data loss on failover |
| Use | Money, inventory, anything with "we cannot lose a write" | Feeds, analytics, caches, most content |
| Middle | Semi-sync (wait for one replica ack) — common production mode | |

## Push vs pull (fanout)

| | Push (fanout-on-write) | Pull (fanout-on-read) | Hybrid |
|---|---|---|---|
| Best for | Read-heavy, moderate write rates | Sparse reads, heavy writers (celebrities) | Feeds with mixed population: push for normal users, pull-on-read for whales |
| Cost | Write amplification (N writes per post), stale-follower complexity | Read latency + fan-in at read time | Complexity — two code paths, merge logic |

## Message queue selection

| | Kafka | SQS/pubsub-style | RabbitMQ | Pulsar |
|---|---|---|---|---|
| Model | Durable partitioned log | Job queue / topic | Flexible routing | Log + queues, tiered storage |
| Replay | Yes (offset rewind) — killer feature | No (ack deletes) | Limited | Yes |
| Ordering | Per partition | FIFO queues only, limited | Per queue | Per partition/key |
| Throughput | Very high | High (managed) | Medium | Very high |
| Ops burden | High if self-managed; manageable via Confluent/MSK | None (managed) | Medium | High |
| Choose when | Event pipelines, replay, stream processing, multiple consumers | Task offload, simplest possible decoupling | Complex routing, RPC-ish messaging | Geo-replication, compute/storage separation needs |

Default: managed queue (SQS/Pub/Sub) at tier <= 2; Kafka-family when replay/multiple-consumer/event-sourcing semantics appear (tier 3+).

## Cache strategies

| Strategy | Mechanism | When | Cost |
|---|---|---|---|
| Cache-aside | App reads cache, on miss reads DB and populates | Default | Stale window = TTL; stampede risk without coalescing |
| Read-through / write-through | Cache sits in front, manages DB | When cache library supports it | Write latency += cache+DB |
| Write-behind | Cache acks, flushes to DB later | Write bursts, tolerable loss | Data loss on cache crash before flush |
| Refresh-ahead | Cache pre-loads hot keys before expiry | Predictable hot set | Complexity, wasted refresh on cold keys |

Plus: TTL choice = staleness vs miss rate; hot-key protection = single-flight + local micro-cache; never cache without asking "what makes it stale?" (see data-systems.md).

## REST vs gRPC vs GraphQL

| | REST | gRPC | GraphQL |
|---|---|---|---|
| Choose for | Public APIs, simplicity, cacheability | Internal service-to-service, low latency, streaming | Client-driven mobile/web apps, aggregate graphs |
| Cost | Over-fetch chatter | Binary opacity, tooling; browser needs proxies | Server complexity: N+1 resolver trap, caching harder |

## Monolith vs microservices

Choose monolith by default. Split services when: team coordination is the bottleneck (not tech); a component has wildly different scaling/profile (heavy compute vs light CRUD); independent deploys are a proven need; fault isolation is required (e.g., one crashy analytics job shouldn't take checkout down).
Cost of microservices: distributed transactions (sagas/outbox), network failure handling, observability investment, platform team, service mesh questions. A modular monolith with clear internal boundaries captures 80% of the benefit at 20% of the cost.

## Batch vs stream

| | Batch | Stream |
|---|---|---|
| Latency | Hours | Seconds |
| Best for | Reprocessing, heavy joins, ML training, exactness | Alerts, live dashboards, event-driven UX |
| Cost | Stale windows | Event-time complexity (watermarks, late data, windows) |

Prefer single-technology with replay (Kappa) over dual lambda (batch+speed layer) when feasible.

## Read path scaling ladder

In order of cheapness: (1) indexes/query tuning, (2) read replicas, (3) cache layer (Redis), (4) CDN for cacheable responses, (5) denormalized read models (CQRS), (6) search engine for search-shaped queries. Don't skip to CQRS before indexes are right.

## Global vs local index (sharded data)

| | Local (shard-local) index | Global index |
|---|---|---|
| Write | Fast, local | Cross-shard coordination, slower |
| Read | Scatter-gather fan-out to all shards | Direct to one shard |
| Choose | Writes dominate; app can route queries (e.g., by user) | Reads dominate; arbitrary queries |

## 2PC vs saga

| | 2PC / distributed tx | Saga (local tx + compensations) |
|---|---|---|
| Guarantee | Atomic, all-or-nothing | Eventual; intermediate states visible |
| Cost | Blocking, coordinator SPOF, low availability | Compensating logic for every step; "cancel" UX |
| Use | Rarely across services — single DB when possible | Standard for cross-service workflows (order, payment, booking) |

Pair sagas with the **transactional outbox** (write event + state in one local transaction; relay publishes) to avoid dual-write bugs, and **idempotent consumers** for redelivery.

## Managed vs self-hosted

Managed wins when: team < ~20 engineers, undifferentiated component (DB, queue, k8s control plane), cost of ops > price delta. Self-host justifies when: scale makes managed pricing quadratic, compliance demands, or the component IS your product. Put the rule in the design doc — it's an architecture decision.
