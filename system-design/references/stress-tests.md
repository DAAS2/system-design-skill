# Stress tests: the 12 failure injections

Every design (design/review/evolve modes) must walk these. For each: does the design **survive** (no user impact), **degrade** (say exactly how), or **die** (redesign or accept explicitly)? Record the answers in the failure-mode table of the design doc.

## Contents
- [The injections](#the-injections)
- [How to run the walk](#how-to-run-the-walk)

## The injections

### 1. Dependency down
A downstream service/DB/third-party API goes fully down.
Antidotes: timeout per call (never infinite); circuit breaker to stop hammering; fallback (cached/stale/default data, queue-and-retry-later); bulkhead so one dead dependency doesn't consume all threads. Question to answer: which user journeys survive?

### 2. 10x traffic spike
Flash crowd, marketing win, or retry amplification.
Antidotes: autoscaling (with its warm-up lag — capacity doesn't appear instantly); load shedding by priority (drop batch/analytics before checkout); admission control; queues to absorb write bursts; static assets on CDN. Question: what is the shedding order?

### 3. Hot key / hot partition
One user/slug/hashtag/shard takes a disproportionate share of traffic.
Antidotes: replicate the hot item (cache everywhere, including in-process); key salting to spread writes; separate hot path from bulk path (celebrity handling in feeds); request coalescing. Question: at what multiplier of average does one key break the design?

### 4. Cache stampede
Cache expiry or flush sends the entire read load to the origin at once.
Antidotes: request coalescing/single-flight (one rebuild, others wait); stale-while-revalidate (serve stale during rebuild); probabilistic early refresh (refresh before expiry, randomized to smooth); warmup after flush. Question: what happens the moment the cache cluster restarts empty?

### 5. Retry storm
Clients retrying failures multiply load exactly when the system is weakest.
Antidotes: exponential backoff + full jitter (never synchronized retries); retry budgets/hedging caps; idempotent operations (safe to retry); fail fast with 429 + Retry-After instead of letting clients guess. Question: what is total request multiplier at 100% retry rate?

### 6. Network partition / split-brain
Nodes can't talk; two sides each believe they're healthy — two leaders, divergent writes.
Antidotes: quorum-based decisions (majority side proceeds, minority steps down); fencing tokens on every leader-held resource (monotonic token checked by storage so a stale leader can't corrupt); deterministic conflict resolution (CRDT/LWW/last-write-merge) for the chosen consistency level. Question: when the partition heals, what diverged and who repairs it?

### 7. Poison message
One malformed/edge-case event crashes the consumer and gets redelivered forever, blocking the queue.
Antidotes: dead-letter queue after N attempts with alerting; quarantine topic for inspection; schema validation at ingest; bounded parsing (reject > N MB). Question: can one bad event wedge the pipeline?

### 8. Slow consumer / backlog growth
Producers outpace consumers; latency to freshness grows unboundedly.
Antidotes: backpressure (bounded queues that push back to producers); consumer lag alerts + autoscaling of consumers; partitioning to parallelize; shed or sample at ingest when fidelity permits. Question: what's the acceptable lag, and what alerts before it's breached?

### 9. Region loss
A whole cloud region goes away (or is evacuated).
Antidotes: know your RTO/RPO targets first; multi-AZ is table stakes, multi-region is a choice (active-passive with async replication = RPO minutes; active-active = conflict story required); backups in a second region with **tested** restore; DNS/global LB failover; degradation ladder (read-only mode beats down). Question: what do users experience during the 5-30 min failover?

### 10. Clock skew
Server clocks disagree; ordering breaks, TTLs misbehave, leases misjudge.
Antidotes: never use wall clocks for ordering (use logical clocks/sequences/version numbers); NTP with monitored drift; lease expiry with safety margin; waiting out uncertainty (Spanner's TrueTime approach) when strict ordering matters. Question: where does this system silently depend on clocks agreeing?

### 11. Cascading failure
One slow dependency converts to total outage: threads pile up waiting, exhausted pools block health checks, liveness kills everything.
Antidotes: aggressive timeouts (budget: sum of hop budgets < user SLO); bulkheads (separate pools per dependency); circuit breakers; shed load at the edge rather than absorbing it; fail fast — a quick 503 beats a 30s hang. Question: trace it — dependency slows 10x: how long until the whole tier is down?

### 12. Metastable failure
The trigger (spike, flush, deploy) passes but the system stays saturated: cache misses -> slow responses -> retries -> more misses. It cannot self-recover.
Antidotes: shed load **below** capacity to break the cycle (overshoot protection); keep caches warm through deploys; rate-limit retries; ability to manually drop traffic and let the system drain. Question: after the trigger clears, what returns the system to steady state?

## How to run the walk

1. Go through all 12 in order; skip none silently (mark N/A with reason: "no queue in design -> 7, 8 N/A").
2. For each, name the mechanism (not aspiration): which component enforces the timeout? what exactly sheds?
3. Record in the failure-mode table: injection / behavior (survive-degrade-die) / mechanism / residual risk.
4. Any "die" either produces a design change now or a documented accepted risk with tripwire metric.
5. The walk often finds the missing component (a DLQ, a breaker, a budget) — add it to the design before finalizing.

Sources: Release It! (Nygard), Tail at Scale (Dean & Barroso), Google SRE, Dynamo/Spanner papers, metastable failure literature (Obstgarten et al.).
