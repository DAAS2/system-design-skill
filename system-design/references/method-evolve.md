# Method: Evolve (migration & scaling evolution)

## Contents
- [When to use](#when-to-use)
- [Step 1: Confirm the forcing function](#step-1-confirm-the-forcing-function)
- [Step 2: Require the as-is map](#step-2-require-the-as-is-map)
- [Step 3: Define the target state](#step-3-define-the-target-state)
- [Pattern library](#pattern-library)
- [Step 4: Phase the rollout](#step-4-phase-the-rollout)
- [Step 5: Risk table](#step-5-risk-table)
- [Step 6: Write the plan](#step-6-write-the-plan)

## When to use

"We're hitting scale on X", "migrate from A to B", "break out the payments service", "add multi-region", "move off Mongo". Evolve mode is for changing systems that exist and must keep serving traffic while they change.

## Step 1: Confirm the forcing function

Name the forcing function and its evidence before designing anything:

| Forcing function | Evidence to demand | If absent |
|---|---|---|
| Scale | Actual QPS/p99/storage numbers, not projections | It's premature — say so and stop |
| Cost | Current monthly bill and growth curve | Optimization is speculative |
| Feature velocity | PR cycle time, team contention stats | Org problem, not architecture problem |
| Risk/compliance | Audit finding, incident report, regulation deadline | Real — prioritize |
| Tech debt / EOL | Concretely broken things, support deadlines | Triage honestly |

If the forcing function can't be evidenced, the honest output is "don't migrate yet; here's the tripwire metric and threshold that should trigger this work." Write the tripwire down — that's a deliverable too.

## Step 2: Require the as-is map

Never plan an evolution against an imagined system. If `docs/architecture/as-is.md` doesn't exist, run method-map first. The plan must reference real components and real data flows, and the map's risk register should inform the migration ordering.

## Step 3: Define the target state

One page: target architecture (diagram), what improves and by how much (measurable: p99, $/mo, deploy frequency, blast radius), what gets worse (there is always something — name it), and the exit criteria ("rollback to old path possible until N weeks of clean metrics").

## Pattern library

Choose per problem. Compose them; real migrations use 3-4 patterns together.

| Pattern | Mechanism | Use for | Key risk |
|---|---|---|---|
| **Strangler fig** | Route/inject façade in front of old system; peel functionality incrementally | Replacing a monolith or legacy system | Façade becomes permanent; keep peeling |
| **Expand-contract** (parallel change) | Add new shape alongside old; migrate readers; drop old | Schema/API changes with consumers | Forgetting the contract phase; track consumers |
| **Dual-write + backfill + cutover** | Write old+new stores; backfill history; verify; switch reads; stop old writes | Data store migrations | Divergence between stores — need checksums + repair |
| **CDC (change data capture)** | Tail the DB log (Debezium etc.) to feed new store/index | When dual-write code can't be added everywhere | Log-format coupling; ordering |
| **Backfill via replay** | Re-derive new store from source-of-truth log/events | Systems already evented | Event schema evolution over the replay window |
| **Feature-flag cutover** | Toggle new path per-user/percentage | Any user-visible change; kill switch for every phase | Flag debt — set removal date |
| **Blue-green / canary** | Two environments or weighted traffic | Deploy-level risk control | Data migrations don't fit blue-green (state!) |
| **CQRS transition** | Build read models from events; move reads over gradually | Read-path extractions (search, feeds, analytics) | Eventual consistency surprises downstream |
| **Shard split** | Double shard count, split each shard, rebalance | Outgrowing partition count | Hot shards during rebalance; reshard under low traffic |
| **Reindex-in-place** | Build new index alongside; alias switch | Search/index migrations | Indexing lag; alias atomicity |
| **Frozen zone / branch by abstraction** | Interface first, swap implementation behind it | Library/framework swaps | Interface design rush |

Ordering rule: **make the change reversible at every phase until the last possible moment.** The final irreversible step (e.g., deleting the old column) comes last, after clean-metric soak time.

## Step 4: Phase the rollout

Skeleton every plan into phases; each phase needs: action, verification (metric/checksum/traffic %), rollback procedure, and soak duration.

```
Phase 0 — Instrument: dashboards + alerts on current system. (Cannot migrate what you can't see.)
Phase 1 — Expand: add new schema/service/index; old path untouched. Rollback: delete new.
Phase 2 — Shadow: exercise new path with mirrored traffic; compare outputs (diff/count checksums). Rollback: stop mirroring.
Phase 3 — Migrate data: backfill; verify counts + sampled content equality. Rollback: re-run backfill.
Phase 4 — Cut over reads (canary % -> 100). Rollback: flip read flag back.
Phase 5 — Cut over writes. Rollback: dual-write kept warm, flip write flag back.
Phase 6 — Contract: remove old path, dual-write code, flags. Now it's irreversible. Soak first (weeks, not days).
```

Adapt: not every migration needs every phase, but every removal of a rollback path must be a deliberate, dated decision.

## Step 5: Risk table

Mid-migration failure modes — walk these explicitly:

| Risk | Mitigation |
|---|---|
| Old/new divergence during dual-write | Outbox or CDC instead of app dual-write; periodic checksum diff + repair job |
| Backfill overloads prod | Rate-limit backfill; run against replica; batch + off-peak |
| Hidden consumer of old schema/API | Search code + traffic before Phase 6; keep old read-only for a grace period |
| Divergent traffic during soak | Define "clean" numerically (error delta < X for N days) |
| Migration code itself has a bug | Shadow phase exists to catch this; never skip straight to cutover |
| Two writers during writer cutover | Single-writer discipline or fencing (lease/token) during transition |
| Team pressure to skip phases | Put phase gates in writing with owner sign-off |

## Step 6: Write the plan

Write `docs/architecture/YYYY-MM-DD-<evolution-name>.md` (template in output-templates.md): forcing function + evidence, as-is reference, target state, chosen patterns + why, phase table, risk table, tripwires and rollback owners, and a "do not start until" list (e.g., instrumented dashboards exist).

The plan must be executable by an engineer who joins the team tomorrow. If a phase can't be verified, it isn't a phase — it's hope.
