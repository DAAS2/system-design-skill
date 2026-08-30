# Classic problems: 28 designs and their key insight

Check this list before designing — most "design X" requests map to a known problem. Use the insight as the deep-dive entry point, not as a script: the constraints of the actual request override the classic answer.

| # | Problem | Core insight (what actually matters) |
|---|---|---|
| 1 | URL shortener | Read-heavy 100:1. Real problem = ID generation (base62 of Snowflake counter — collision-free) + read caching. 301 vs 302 is a product call (speed vs analytics) |
| 2 | Rate limiter | Algorithm = accuracy vs memory; sliding window counter default. Distributed state in Redis (atomic Lua). 429 + Retry-After contract |
| 3 | Chat (WhatsApp/Slack) | Persistent connections + connection registry; per-channel ordering; offline inbox + multi-device sync; group fanout is the cost driver |
| 4 | News feed | Push (fanout-on-write) vs pull vs hybrid; celebrities via pull-on-read; feed cache + ranking as separate pipeline |
| 5 | Notification service | At-least-once + idempotent consumers; aggregation/dedup windows; per-user preferences; provider backpressure; DLQ |
| 6 | Distributed message queue | Separate metadata plane from data plane; log storage design; pull vs push; exactly-once = dedup + idempotent consumer |
| 7 | Key-value store (Dynamo) | Consistent hashing + vnodes, quorum R/W (R+W>N), vector clocks, hinted handoff, Merkle-tree anti-entropy |
| 8 | Web crawler | Politeness (per-domain token bucket), URL frontier (priority + freshness), dedup (Bloom), robots.txt, host-sharded workers |
| 9 | Typeahead | Precompute top-k per trie node offline; query is a prefix walk + local rank; async index build decoupled from serving |
| 10 | Video platform (YouTube) | The byte path IS the design: transcoding DAG, ABR ladder, CDN offload (>99% of bytes), metadata is trivial by comparison |
| 11 | Ride hailing (Uber) | Geospatial index (geohash/H3/quadtree) + supply-demand matching loop; location writes dominate volume; in-memory matching, DB as source of truth |
| 12 | Twitter search | Inverted index + early termination; two-tier index (recent vs archive); scatter-gather fan-out to index shards |
| 13 | Ticket/seat booking | Consistency-first: reservation holds with expiry (pessimistic) or version-check (optimistic); hot-partition mitigation for on-sales; idempotent booking saga |
| 14 | Job scheduler | Lease-based task acquisition (TTL, requeue on expiry); at-least-once + idempotent execution; fairness; DLQ |
| 15 | Payment system | Idempotency keys as THE primitive; double-entry ledger (append-only, balanced); reconciliation safety net; saga across PSPs |
| 16 | Ad click aggregation | Dedup retried events; late events (watermarks); windowed pre-aggregation + batch reconciliation for exactness |
| 17 | Metrics monitoring | Time-series cardinality explosion kills stores (tags = series); write-optimized TSDB (LSM); downsampling + retention tiers; alert evaluation pipeline |
| 18 | File sync (Dropbox) | Chunk-level content-addressed blocks + delta sync; metadata service separate from block storage; conflict resolution policy |
| 19 | Webhook delivery | Signed payloads (HMAC), exponential backoff + full jitter retries, DLQ after N, per-endpoint isolation so one bad consumer can't clog |
| 20 | Feature flags | Local SDK evaluation from pushed snapshots (microsecond path); kill switch semantics; flag lifecycle/hygiene is the long-term problem |
| 21 | Unique ID generator | Snowflake 64-bit (ts-node-seq): sortable + decentralized + clock-skew handling; vs DB range allocation (Leaf) — coordination vs complexity |
| 22 | Distributed lock / leader election | Leases + fencing tokens; ZooKeeper/etcd as reference; lock without fencing = split-brain corruption waiting |
| 23 | Leaderboard / top-K | Exact: Redis sorted set (bounded scale); streaming approximate: count-min sketch + heap; heavy-hitter partitioning |
| 24 | Hotel/inventory reservation | Optimistic vs pessimistic per contention; overbooking as product decision; idempotency; partition by resource ID |
| 25 | Stock exchange | Deterministic single-threaded sequencing; state-machine replication; event-sourced order log; recovery = replay |
| 26 | Proximity / maps | Geohash/quadtree partitioning; tile servers; precomputed route hierarchies (contraction) vs on-demand |
| 27 | Object storage (S3) | Metadata plane vs data plane split; erasure coding (1.5x vs 3x replication); strong metadata + eventual data consistency trade |
| 28 | Email/digital wallet (Ledger) | Append-only double-entry; balances derived, never mutated; reconciliation jobs; idempotent external transfers |

Adjacent modern problems (deep versions in llm-infra.md): RAG pipeline, vector search service, LLM inference platform, AI agent orchestration, feature store, real-time analytics dashboard.

Using this table: match the request to a row (or 2-3 composed), state the match aloud ("this is a booking-core problem like #13 plus a notifications problem like #5"), then let the request's specific constraints bend the classic insight. Never recite the row — anchor on it and reason.
