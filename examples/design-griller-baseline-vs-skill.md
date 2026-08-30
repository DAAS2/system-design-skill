> Real outputs from the eval suite (iteration 1 — see `evals/README.md`). Same prompt, same model, fresh sessions: one with the skill installed, one without. Published verbatim except light trimming and the critique below.

# The design griller: what a baseline agent builds vs. what the skill does

**The prompt, verbatim:**

> *"Design a URL shortener for a new product. We expect around 100M daily link resolutions and 1M new links per day."*

Both answers did real work. One of them would survive a design review. The other is exactly the kind of architecture that gets a repo renamed to "legacy" within a year.

## What the baseline agent built (excerpts)

> "Split **read** and **write** paths so the hot redirect path can be scaled and optimized independently." — Read Service + Write Service microservice split at **~5,000 peak rps**

> Event queue → "(Kafka)" → Analytics/warehouse — **Kafka for ~2.5 MB/s of analytics events**

> "A relational DB also works fine at this scale... but NoSQL gives simpler horizontal scale-out headroom." → **a sharded NoSQL KV store for 2 TB of data and 12 writes/sec**

> "CDN / LB (edge, geo-routing)" + multi-region active-active reads, per the design's later sections — **geo-replication for a product that fits in one Postgres**

> "Out of scope: No full analytics warehouse initially... auth for creation exists but is not the focus." — **a two-item non-goal list**

> "Access is Zipfian... Target >90% cache hit rate." — **hot-key and cache-stampede behavior never analyzed**

## What the skill produced (excerpts)

> ```
> Read QPS avg / peak                1,157.4 / 3,472.2
> Write QPS avg / peak               11.6 / 34.7
> Storage over 5 yr (growth x1/yr)   2.49 TiB
> App nodes @ 5,000 RPS/node         2 (min 2 for HA)
> Decisions these numbers force:
>   - no thresholds crossed: prefer the boring tier-appropriate design
> ```

> "2.49 TiB / 5 yr (x3 replication) => single managed Postgres primary + replica is comfortably in scope. **No sharding, no NoSQL.**"

> "12 write QPS => the write path is trivial; the interesting write-side problems are ID uniqueness and abuse, not throughput."

> "No Kafka, no k8s, no microservices, no CDN v1."

> "Rejects random 7-char base62 with birthday-bound math (~1.9M collision links at 1M links/day x 5yr), chooses Snowflake 64-bit → base62 11-char, names range allocation (Leaf) as the revisit trigger."

> "No stampede by construction (nothing expires): immutable slugs + cache-forever means no TTL storm; single-flight bounds misses." — plus per-key hot-slug math (~1.2k QPS/key is "noise")

> Seven explicit non-goals (custom aliases, expiry, auth, per-click analytics, content scanning, multi-region writes, GDPR), a 12-injection failure table, a cost estimate, and a named evolution path at 10x.

## The tear-down

| Baseline claim | The griller's verdict |
|---|---|
| Read/write service split "to scale independently" | **Scale theater.** At 3.5k peak rps a two-node monolith handles it. You added a network hop to your hot path to solve a problem your own numbers ruled out. |
| Kafka for analytics events | **A platform, not a tool, at this scale.** ~2.5 MB/s egress. A managed queue or even a log file with a scheduled flusher does it. The Kafka tax (cluster ops, partition planning, consumer groups) buys nothing here. |
| NoSQL sharded KV "for scale" | **The wrong store for the right reason.** 2.49 TiB/5yr and 12 writes/sec is one managed Postgres with headroom. You designed the sharding you'd need at 100x your stated traffic. |
| Multi-region active-active | **The most expensive solution to a problem you don't have.** Cross-region writes need a conflict strategy, failover drills, and replication cost — for a read path that's already caching at the edge. |
| Non-goals: two items | **Scope discipline is the design.** A real non-goal list is what keeps the review short. |
| "Zipfian, so cache it" | **Caching is a consistency system, not a speed hack.** What happens when the hot slug's cache entry expires and 50k requests hit the origin? The skill answers it by construction; the baseline never asked. |

## Why this matters

The baseline answer isn't bad for a whiteboard. It names real components and does real math. But it fails the review the moment an engineer asks *"what breaks first at 10x?"* and *"what did you pay for this?"* — because the answers are "everything" and "a lot."

The skill's answer survives because every component traces to a number, the failure modes are walked before anyone walks them on-call, and the non-goals are explicit. **That's the difference between an architecture and a wish.**

---

*Want to see the skill do this to your own agent's design? Install it (see README → Install) and ask: "review this design: <paste>". The review mode scores it across 10 dimensions and names the blocking findings.*