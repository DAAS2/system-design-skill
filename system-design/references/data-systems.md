# Data systems: replication, partitioning, consistency, transactions

Distilled from Designing Data-Intensive Applications (Kleppmann), the Dynamo/Spanner/Aurora/Bigtable papers, and production practice. Use for deep dives on the data layer. Cross-reference: tradeoffs.md for quick decisions, components.md for concrete systems.

## Contents
- [Storage engines](#storage-engines)
- [Replication](#replication)
- [Partitioning](#partitioning)
- [Consistency models](#consistency-models)
- [Transactions and isolation](#transactions-and-isolation)
- [Distributed transactions and sagas](#distributed-transactions-and-sagas)
- [Idempotency and delivery semantics](#idempotency-and-delivery-semantics)
- [Consensus, leases, fencing](#consensus-leases-fencing)
- [CAP and PACELC, correctly used](#cap-and-pacelc-correctly-used)
- [Event streaming and derived data](#event-streaming-and-derived-data)
- [Analytics storage](#analytics-storage)

## Storage engines

- **B-tree** (Postgres/MySQL): sorted pages, in-place updates, read-optimized. Write amplification from page splits; good for read-heavy + point updates.
- **LSM-tree** (RocksDB/Cassandra/Bigtable SSTables): append + memtable + compaction. Write-optimized; reads may check multiple levels; compaction stalls are the operational hazard (Cassandra/elastic issues class).
- Rule: write-heavy append-shaped workloads -> LSM; read-heavy with updates -> B-tree. Columnar (below) for analytics.

## Replication

| Topology | Mechanics | Failure handling | Use |
|---|---|---|---|
| Single-leader | Writes -> leader, replicated to followers (sync/semi/async) | Failover: promote a follower; split-brain + lost-writes risks on async | Default for relational DBs |
| Multi-leader | Multiple write nodes, mutual replication; conflicts happen | Conflict resolution: LWW (lossy), CRDT merge, app-specific merge | Multi-region writes, offline-first |
| Leaderless / quorum | Writes/reads to W/R of N nodes; R+W>N gives strong-ish reads (Dynamo/Cassandra) | Read repair, anti-entropy (Merkle trees), hinted handoff | Massive write availability, tunable consistency |

Sync vs async is a durability-latency dial: async replication can lose the last acked writes on leader loss — say so in money paths. Semi-sync is the common middle.

Failover hard parts: knowing the leader is dead (heartbeats lie), fencing the old leader (see below), and replica lag on promotion. Statement: "failover is where single-leader systems actually fail."

## Partitioning

- **Range** partitions: preserve range scans; monotonic keys (timestamps, sequential IDs) create a write hotspot — salt or compound-prefix if so.
- **Hash** partitions: even load; destroys range queries; combined with **consistent hashing + virtual nodes** for smooth rebalancing (add/remove a node moves ~1/N keys).
- **Shard key choice**: the query-routing question. Best key: the one every hot query already filters by (usually user_id/tenant_id). Secondary indexes under sharding: local (scatter-gather reads) vs global (fast reads, slow coordinated writes) — see tradeoffs.md.
- Rebalance with minimal movement; never hash-mod-N (changing N moves everything); fixed pre-split partitions (a la Dynamo/vnodes) or dynamic splitting (HBase-style).
- Denormalize to keep queries shard-local; cross-shard joins are a redesign smell.

## Consistency models

Strongest to weakest; know which one each flow needs — they are per-operation choices, not system-wide tattoos.

1. **Linearizable** — acts like one copy, real-time order. Cost: consensus round trip on every write + read. Use for: inventory decrement, unique username, ledger.
2. **Sequential** — one order, all clients agree, no real-time guarantee. Cheaper; usually enough.
3. **Causal** — preserves happens-before (replies after posts, always). Vector clocks / version markers.
4. **Eventual** — replicas converge; window of divergence. Use for: likes, view counts, feeds, profile edits.
5. **Session guarantees** (client-side stickiness tier): read-your-writes, monotonic reads, consistent prefix. Deliver via sticky routing (same replica) or version tokens. Cheapest UX fix for "I just saved it, where is it?"

## Transactions and isolation

Isolation ladder (single DB):

| Level | Prevents | Still permits |
|---|---|---|
| Read committed | Dirty reads/writes | Non-repeatable reads, phantoms, **write skew** |
| Snapshot / repeatable read (MVCC) | Non-repeatable reads | **Write skew**, phantoms (partially) |
| Serializable (2PL or SSI) | All anomalies | - |

**Write skew** is the classic trap: two transactions read the same state, make disjoint writes that together violate an invariant (both on-call doctors go off duty; two account sign-ups claim the same handle). Fixes: explicit row locking (`SELECT ... FOR UPDATE` on the shared rows), materialized conflict rows, or serializable isolation.

Design guidance: default snapshot isolation; escalate per-flow to serializable where invariants are money-adjacent. Note Postgres RR is actually snapshot isolation; true serializable is SSI.

## Distributed transactions and sagas

- **2PC**: blocking, coordinator is a SPOF, latency-heavy. Across microservices, avoid; within one DB, it's just a transaction — use freely.
- **Sagas**: sequence of local transactions + compensating actions on failure. Intermediate states visible — design the UX ("pending", "cancelling"). Variants: choreography (events, decentralized, harder to trace) vs orchestration (central coordinator, clearer, add a component).
- **Transactional outbox**: in the same local DB transaction, write the domain event to an outbox table; a relay (poller or CDC/Debezium) publishes to the stream. Kills dual-write. Non-negotiable where events must reflect committed state.
- **Event-carried state transfer**: services keep local copies of data they need from events of others — removes sync cross-service reads at the cost of eventual consistency.

## Idempotency and delivery semantics

- **At-least-once + idempotent processing == exactly-once effects** (MillWheel/Kafka EOS pattern). "Exactly-once delivery" is not a thing; exactly-once *effects* are.
- Mechanics: idempotency keys with dedup store (Stripe-style: key + stored response), deterministic request IDs, natural idempotency where possible (upsert by stable key, commutative counters).
- Consumers: assume redelivery; assume reordering within partitions at rebalance windows; make handlers side-effect-idempotent or transactionally deduplicated.
- Ordering is per-partition (Kafka) or per-queue — partition by the entity whose order matters (user_id), not by round-robin.

## Consensus, leases, fencing

- Consensus (Raft/Paxos/ZAB): a quorum agrees on a single ordered log. Use for: leader election, configuration/metadata, locks. Cost: fsync + extra round trips per write; quorum must be available.
- **Fencing tokens**: every lease/lock grant includes a monotonic token; storage rejects writes with stale tokens. Without fencing, a paused-but-alive lock holder (GC pause, network lag) corrupts state after the lock expires — this is the distributed-lock bug (Kleppmann's "How to do distributed locking").
- Rule: locks/leases coordinate, tokens protect. Need both.
- Outsourced coordination (ZooKeeper/etcd/managed locks) beats hand-rolled for everything below tier 5.

## CAP and PACELC, correctly used

- CAP: under a network **partition**, choose consistency (reject some ops) or availability (serve possibly-stale/divergent ops). Partitions are rare but real; design the partition behavior deliberately instead of discovering it live.
- PACELC: without partitions, you still trade **latency vs consistency** — strong consistency costs a synchronous round trip on every write, forever. Spanner is "EC" (external consistency, pays latency); Dynamo is "PA/EL".
- Interview-grade framing: "for this flow, on partition we prefer X because business cost of Y is higher; normally we accept Z ms extra per write for W guarantee."

## Event streaming and derived data

- **Log as system of record**: append-only, replayable, ordered per partition. Producers/consumers decouple; reprocessing = new consumer from offset 0.
- Kappa over Lambda: one stream processing codepath with replay beats maintaining batch+speed dual pipelines — prefer it when the tech fits.
- CQRS: separate write model (normalized, transactional) from read models (denormalized per query shape, materialized from events). The read side is eventually consistent by construction — design features for it (pending states, version stamps), don't fight it.
- Event sourcing: state = fold of events; gives audit + time travel; costs: event schema versioning, snapshotting, query complexity. Use where audit is the requirement (payments, ledger), not as a default.

## Analytics storage

- **Warehouse** (BigQuery/Snowflake/Redshift): columnar, schema-on-write, huge scans, SQL. **Lake** (S3 + Parquet): raw, schema-on-read, cheapest. **Lakehouse** (Iceberg/Delta/Hudi): ACID + time travel + engine interop over object storage — the current convergence point.
- Columnar beats row for wide-table aggregates by 10-1000x; OLTP row stores are wrong tools for analytics.
- Stream-to-warehouse: partition by event date, compaction/late-arrival windows, and a separate serving layer (ClickHouse/Druid-class) when dashboard latency matters.
