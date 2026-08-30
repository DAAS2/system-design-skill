> Real output, not a mockup. This document was produced end-to-end by the skill (eval run, iteration 1 — see evals/README.md). Published verbatim; only this note was added.

# Interview grade: "Design a chat system" (run-1)

**Target:** L6 senior · **Session length:** ~8 interviewer prompts, ~10 candidate lines (compressed transcript)

---

## 1. Overall

**Level practiced: Senior (L6). Level demonstrated: below mid (L3).**

This was not a design discussion; it was a component recital. The interviewer opened seven doors — scale, MVP phasing, consistency, fanout, duplicates, failover, CAP — and each was answered with a one-liner of fifteen words or fewer. Every signal that caps a rubric score is present: zero numbers, zero clarifying questions, Kafka/microservices/K8s reflex, "it's very high throughput" / "it just works" defenses. The one structurally correct idea in the session (offline inbox, "waits in Mongo, delivered on reconnect") came from the candidate's own skeleton — the raw material is there. The L6 gap is not knowledge; it is discipline: no questions, no math, no trade-offs, no failure walking.

---

## 2. Scores (rubric dimensions, cited evidence)

| Dimension | Grade | Evidence |
|---|---|---|
| **Scoping** | Below mid | Opened with "microservices, API gateway, message service, MongoDB, WebSockets" (L5) before a single clarifying question. Never asked: DAU, messages/day, group sizes, media, multi-device, retention, compliance, delivery SLOs, budget. Mid bar is "clarifies functional gaps" — zero gaps were clarified. |
| **Estimation** | Fail | Directly prompted for scale (L7); answered with a claim, not math: "a billion users… MongoDB sharded by user ID will handle that fine" (L9). No QPS, storage, bandwidth, fanout, or connection count anywhere. At the scale the candidate chose, the math is: 1B DAU × 50 msgs/day × 1 KB → **~580k write QPS avg / 1.7M peak, ~140 TiB storage/day (×3 replication), ~250 PiB over 5 yr, ~870 app nodes, ~9–19 TiB hot set** (botec.py). Those numbers would have forced the real conversation: partitioning, media path, retention tiering, fanout. |
| **Depth** | Below mid | No API surface, no data model (no message schema, no conversation key, no sequence numbers, no message-ID generation). The write path (L17) is a linear pipeline recital: gateway → Kafka → Mongo → socket. It skips the two things that make chat chat: the **connection registry** (which node holds B's socket?) and **per-conversation ordering**. Chat's real core: persistent connections + connection registry, per-channel ordering, offline inbox + multi-device sync, group fanout as the cost driver. Only the offline-inbox insight appears. |
| **Trade-offs** | Fail | Zero trade-offs stated. "MongoDB because it scales horizontally" (L5) — benefit only, no cost, no "why not Postgres / DynamoDB", no consistency implication. Kafka "to decouple everything" (L9) — no ordering, retention, or DLQ cost. Senior bar is *proactively naming the cost of every choice*; nothing was named. |
| **Failure handling** | Fail | Four failure injections, four one-liners: fanout → "Kafka handles it" (L25); duplicate → "probably a network glitch, client dedups" (L29); primary down → "automatic failover… just works" (L33); CAP → "AP, users care about availability" (L37). No degradation mode was ever walked. No timeouts, no circuit breakers, no DLQ, no retry budget, no partition story exist anywhere in the design. |
| **Delivery** | Fail at senior bar | Asked "what would you build first" (L11), answered "full architecture… Kubernetes from day one" (L13) — the direct inverse of phased rollout. Senior bar is a phased rollout + migration plan; the candidate actively rejected phasing ("rearchitecting later is expensive" — the myth strangler-fig exists to refute). No evolution story at 10x, no reversibility instincts. |

**Verdict: no dimension at senior; roughly one at mid (the write-path skeleton + offline inbox). Below-mid overall.**

---

## 3. The one thing

**Produce numbers before naming a single component.** When asked "what scale" (L7), the answer should have been: "I need DAU and messages/user/day first — from that I'll get QPS, storage, and fanout, and then we can talk about components." At the billion-user scale the candidate claimed, the numbers are ~580k write QPS and ~140 TiB/day — which immediately reveals fanout as the cost driver, makes the day-one-K8s answer look absurd, and forces the per-conversation ordering discussion. This one habit would have salvaged the rest of the session: it turns every "it just works" into a mechanism and every claim into a derivation. Everything else in this report is downstream of that.

---

## 4. What was strong (evidence, not vibes)

- The four-hop pipeline — gateway → queue → store → sockets — is the correct skeleton for a chat write path, and most candidates forget the async store entirely (L5, L17).
- "If B is offline, the message waits in Mongo and gets delivered on reconnect" (L17) is the single correct chat core insight: the offline inbox. It's exactly what problems.md row 3 calls the chat essence.
- Client-side dedup by message ID (L29) is half of the correct delivery answer (at-least-once + dedup).
- The instinct that "users care about availability" (L37) is the right *concern* — it was applied to the wrong layer, but the concern itself is real.

These are the bones of a mid candidate. The skeleton exists; the muscles (mechanisms, math, trade-offs) are missing.

---

## 5. The four answers, corrected

**Fanout (10M followers) — L25.** Kafka's throughput is irrelevant; the bottleneck is per-recipient work: 10M followers = 10M socket writes + 10M recipient writes per message, plus one hot partition key. The fix is the classic feed decision: **fanout-on-write for small groups, fanout-on-read (pull) for channels/celebrities**, with a connection registry to deliver only to *live* sockets and per-recipient write coalescing. The interviewer was handing you the celebrity-hot-key injection; "Kafka handles it" dodges the question.

**Duplicate message — L27.** Not "probably a network glitch." At-least-once semantics make duplicates *guaranteed*: retry on publish, consumer crash-after-write-before-ack, socket re-send on reconnect. Dedup belongs (a) server-side at ingest — idempotent write keyed on the client-generated message ID (unique constraint / compare-and-set), and (b) client-side at display as the safety net. Naming the three duplicate sources is the senior answer.

**Primary shard down at peak — L31.** Replica-set failover has an RTO of tens of seconds during which writes fail — at peak, that's a queue of retries arriving exactly when the cluster is weakest (retry storm → cascading failure). The answer: client timeouts + circuit breakers, a retry budget, capacity headroom so promotion doesn't overload the remaining replicas, and an explicit statement of what the user experiences (delivery delay, not loss).

**CAP — L37.** The soundbite is backwards for the message path. Chat splits: the **per-conversation message log is CP-ish** — ordered, durable, read-your-writes for the sender (you never want a lost or reordered message); **presence, typing, and delivery receipts are AP**. "Eventual consistency is what NoSQL gives us" (L21) is also a category error — consistency is a configuration property, not an engine property. The senior answer names the split and maps each layer to what users expect.

---

## 6. Drill prescription

1. **Chat, again — properly this time** (problems.md #3). Same problem, 30 minutes: clarify → estimate (DAU, msgs/user/day) → connection registry → per-channel ordering → offline sync → multi-device → group fanout cost. The point of redoing it is that 80% of the design was never attempted.
2. **News feed** (problems.md #4). Fanout-on-write vs pull-on-read and the celebrity path. This directly fixes the 10M-follower failure: a channel *is* a celebrity feed.
3. **Notification service** (problems.md #5). At-least-once + idempotent consumers, DLQ, provider backpressure, retry storms. This fixes the duplicate, poison-message, and failover-retry gaps simultaneously.

---

## 7. Appendix: what the math says (botec.py, 1B DAU @ 50 msgs/user/day, 1 KB)

| Metric | Value |
|---|---|
| Write QPS avg / peak | 578,704 / 1,736,111 |
| Read QPS avg / peak | 578,704 / 1,736,111 |
| Storage/day (×3 replication) | ~140 TiB |
| Storage over 5 yr | ~250 PiB |
| Hot set (20% of daily writes) | ~9–19 TiB |
| App nodes @ 2k RPS | ~870 |

None of this appeared in the session. The interview ended in the equivalent of the first three minutes of a real one.