# Components: building-block catalog

Each block: what it does, when to reach for it, the numbers that matter, common mistakes. Use for component questions and for populating designs with concrete choices.

## Contents
- [Load balancer](#load-balancer)
- [CDN](#cdn)
- [Cache (Redis-class)](#cache-redis-class)
- [Relational DB](#relational-db)
- [Wide-column / KV store](#wide-column--kv-store)
- [Search engine](#search-engine)
- [Object storage](#object-storage)
- [Message queue / log](#message-queue--log)
- [API gateway](#api-gateway)
- [Rate limiter](#rate-limiter)
- [ID generator](#id-generator)
- [WebSocket / real-time tier](#websocket--real-time-tier)
- [Auth](#auth)
- [Observability stack](#observability-stack)
- [Job scheduler](#job-scheduler)

## Load balancer

- L4 (TCP) for raw throughput; L7 (HTTP) for routing by path/header, TLS termination, sticky sessions.
- Algorithms: least-connections > round-robin for mixed-latency workloads; consistent hashing for cache-affinity routing; least-outstanding-requests (LOR) for tail latency (slow nodes get less).
- Numbers: a modern L7 LB node handles 100k+ RPS; health checks 2-5s intervals with failure thresholds.
- Mistakes: no draining on deploy (connection resets), health check hitting a cheap endpoint that doesn't represent readiness, single LB without failover IP (anycast/VIP).

## CDN

- Reach: static assets always; API responses when cacheable (public data or per-user with care); video via segmented delivery (HLS/DASH).
- Design the cache key (path + vary headers), TTL policy (immutable content = long TTL + versioned URLs), purge strategy (soft/hard), origin shield to protect origin from misses.
- Numbers: 90%+ offload typical for media; miss cost = shield + origin round trip.
- Mistakes: cookies/headers in the cache key collapsing the hit rate; no stale-while-revalidate; caching per-user data publicly (leaks).

## Cache (Redis-class)

- 100k-1M ops/s/node; treat ~10-50 GiB working set as single-node ceiling (cluster beyond). Persistence (AOF/RDB) if cache-rebuild cost is high.
- Eviction: allkeys-lru default; volatile-lru for mixed keys; know your hit-rate target (> 90% or the cache is decoration).
- Patterns per tradeoffs.md (cache-aside default); stampede protection per stress-tests.md #4.
- Mistakes: caching unbounded key spaces (no TTL), using KEYS in prod (SCAN), treating Redis as a source of truth without persistence semantics.

## Relational DB

- Postgres/MySQL. Single primary: ~1-5k write QPS (workload-dependent, more on fast NVMe), read replicas scale reads with replication lag (async = ms-seconds).
- Default for tier 0-3 data. Partitioning native (Postgres declarative partitioning) before sharding; sharding via Citus/Vitess/app-layer at tier 3-4.
- Numbers: complex join query 5-100 ms; OLAP on OLTP = wrong tool.
- Mistakes: no connection pooling (server processes/threads exhaust — pgbouncer/orm pool mandatory at scale), N+1s from ORM laziness, missing indexes on hot queries, unbounded transactions holding locks.

## Wide-column / KV store

- Cassandra/DynamoDB/Bigtable. Write-optimized (LSM), linear scale by partition key, 10k+ writes/s/node sustained.
- DynamoDB: on-demand vs provisioned capacity math; hot partition key limits (originally 1k WCU/s per key — design keys to spread); single-digit ms at p99 when modeled right.
- Mistakes: table design not driven by query patterns (the classic Cassandra failure), careless secondary indexes (GSIs cost + consistency), compaction strategy ignored.

## Search engine

- Elasticsearch/OpenSearch/Solr: inverted index, tokenization/analysis chain, scoring (BM25), aggregations.
- Index design = fields + analyzers + shards; shard count sizing (aim < ~30-50 GB/shard); replica shards for read scale.
- Numbers: filtered queries 10s-100s ms on millions of docs; refresh interval (1s default) bounds freshness.
- Mistakes: aggregations on high-cardinality text fields, unbounded index growth without lifecycle management (ILM), treating ES as primary store (keep source of truth elsewhere, reindex capability).

## Object storage

- S3/GCS/Azure Blob: 11 nines durability, effectively infinite, ~$0.02/GB-mo class-dependent; PUT 10-50 ms, GET first-byte 10-100 ms.
- Patterns: presigned URLs for client direct upload (never proxy large files through app servers), multipart upload > 100 MB, lifecycle to cold tiers, event notifications to queues.
- Mistakes: proxying big files through the API tier (bandwidth + latency), no lifecycle policy (cost creep), listing-heavy access patterns (prefix design matters).

## Message queue / log

- Selection table in tradeoffs.md. Kafka: partitions = parallelism unit; size partitions for peak consumer throughput (consumer per partition); retention by time/size enables replay; consumer groups rebalance on membership change.
- Numbers: 100k-1M msg/s/broker batched; end-to-end latency ~ms tens.
- Mistakes: unpartitioned topic for a high-throughput ordered stream (single-partition bottleneck), no DLQ, consumers assuming exactly-once, schema evolution unplanned (use a schema registry).

## API gateway

- Fronts: TLS, authN offload, rate limiting, request shaping, routing, observability. Offload cross-cutting concerns from services.
- Managed (AWS API GW, Cloudflare, Kong, Envoy) at tier <= 3; custom rarely justified.
- Mistakes: business logic creeping into the gateway; per-request latency added by chains of plugins (measure).

## Rate limiter

- Algorithms: fixed window (cheap, boundary bursts), sliding log (exact, memory-heavy), **sliding window counter (default)**, token bucket (burst + steady rate control).
- Distributed: counters in Redis (atomic via Lua), or in-process + async sync (approximate, cheap); enforce per-key (user/IP/API key) + global.
- Respond 429 + Retry-After; fail-open vs fail-closed on limiter outage is a product decision (availability vs abuse).
- Mistakes: rate limiting after auth (unauthenticated floods pass), forgetting per-tenant fairness (one whale tenant starves others).

## ID generator

- Options: DB auto-increment (simple, single-writer ceiling, leaks counts in URLs), UUIDv4 (random, no coordination, 128-bit, index-hostile as PK), UUIDv7 (time-ordered, better), **Snowflake-style** (64-bit = timestamp|node|seq; sortable, decentralized; needs clock-skew handling + node-ID assignment), range allocation (Leaf/segment: DB hands out ID blocks).
- Mistakes: shard-hostile random PKs destroying write locality; exposing sequential IDs publicly (enumeration).

## WebSocket / real-time tier

- Stateful connections: sticky routing (connection registry: user -> node), separate deployment from request/response tier, connection counts per node bounded by memory (~10k-100k/node depending on stack).
- Delivery: per-user inbox queues, presence service, heartbeat/idle management; mobile push via APNs/FCM when disconnected.
- Mistakes: trying to run WS tier statelessly, no fallback to polling, fanout through the same tier that serves HTTP.

## Auth

- Sessions (server-side state, cookie) vs JWT (stateless, revocation pain — keep access tokens short + refresh tokens revocable). Internal service-to-service: mTLS with workload identity (SPIFFE-style) at tier 4+.
- Numbers: bcrypt/argon2 verify ~100-250 ms (by design); token validation should be local (JWKS cache).
- Mistakes: JWTs that can't be revoked for logout, secrets in repos, no per-tenant authorization checks (IDOR class bugs — authN is not authZ).

## Observability stack

- Three pillars: metrics (cheap, alertable — RED: rate/errors/duration per endpoint; USE: utilization/saturation/errors per resource), logs (structured, correlated by request ID), traces (distributed path, sample 1-100%).
- SLO discipline: SLI -> target -> window -> error budget; multi-window burn-rate alerts (fast burn 2%/1h, slow burn 5%/6h) beat threshold spam.
- Mistakes: alerting on causes not symptoms, no request-ID correlation, dashboards without an owner or runbook links.

## Job scheduler

- Delayed/scheduled work: priority + delay queues with leases (worker acquires task with TTL; crashed worker's lease expires, task requeued); idempotency on execute (at-least-once); fairness across tenants; DLQ after N attempts.
- Managed (Cloud Tasks/Scheduler, SQS+delay, Temporal for workflows/durable execution) vs homegrown — homegrown is a classic time sink; prefer managed until workflow complexity demands Temporal-class durable execution.
- Numbers: worker throughput = tasks / (avg exec time) — size pool via queue depth alerting (lag).
