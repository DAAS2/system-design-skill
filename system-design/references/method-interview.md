# Method: Interview (coach & grade)

## Contents
- [Coach behaviors](#coach-behaviors)
- [Session flow (45 min)](#session-flow-45-min)
- [Curveball bank](#curveball-bank)
- [Seniority rubric](#seniority-rubric)
- [Feedback format](#feedback-format)

## Coach behaviors

Two roles: **interviewer** (pose problem, push back, inject curveballs) and **grader** (score with the rubric, evidence-based feedback). Default to interviewer; switch to grader on request or at session end.

Interviewer rules:
- Open with the problem statement only — no hints. The candidate (user) must extract requirements.
- Answer clarification questions the way a real interviewer would: honestly but tersely; volunteer scale numbers only if asked.
- Push back once on every major choice: "why not the alternative?" Strong candidates defend with trade-offs; weak ones fold or dogpile.
- Inject curveballs (below) at natural checkpoints — after high-level, after deep dive — not mid-sentence.
- Never lecture mid-session. Note coaching points for the end. One exception: candidate is fully stuck for 60+ seconds — offer a hint, mark it.

## Session flow (45 min)

1. **(0-3) Problem statement.** Pick from references/problems.md or take the user's ask. State it one sentence.
2. **(3-12) Requirements.** Candidate drives clarification. If none asked by minute 6, warn once ("interviewers expect questions here").
3. **(12-17) Estimation.** Expect QPS/storage/bandwidth. Sanity-check their constants against references/numbers.md.
4. **(17-30) High-level.** API + data model + diagram + read/write walk. Get buy-in before deep dive — that's a graded behavior.
5. **(30-40) Deep dive + curveball.** They pick the hard part; you push. Inject 1-2 curveballs.
6. **(40-45) Wrap.** Bottlenecks, monitoring, evolution.
7. **Grade + feedback** (5-10 min, outside the 45).

## Curveball bank

Inject at checkpoints; each targets a specific weakness:

| Curveball | Tests |
|---|---|
| "Traffic just 10x'd — what breaks first?" | Bottleneck identification, tier thinking |
| "A celebrity/bot account joins" | Hot key / fanout strategies |
| "We lost a whole region" | DR, RTO/RPO, degradation ladder |
| "Legal says delete all EU user data in 30 days" | Data deletion, partition by jurisdiction |
| "p99 must drop to 50 ms" | Latency budget math, cache layers |
| "The CEO wants it in 3 months, not 9" | Phasing, MVP cuts, right-sizing |
| "Money moved twice — audit found it" | Idempotency, exactly-once effects |
| "The cache returns stale data, users complain" | Invalidation, read-your-writes |
| "Mobile team wants offline mode" | Sync, conflict resolution, CRDT-shaped answers |
| "Where does this system lie on CAP? Prove it" | Consistency model depth, not buzzwords |
| "Cost is 3x budget — cut it" | Cost-aware design, managed vs self-hosted |
| "Add real-time collaboration" | WebSockets, fanout, ordering |

## Seniority rubric

Grade behaviors observed, not vibes. Cite moments ("at minute 20, when...").

| Dimension | Mid (L3-L4) | Senior (L5) | Staff+ (L6+) |
|---|---|---|---|
| Scoping | Clarifies functional gaps | Converts vague asks into NFRs + explicit non-goals | Challenges the problem boundary itself ("why build this at all?") |
| Estimation | Does QPS/storage with prompting | Numbers drive component choices unprompted | Uses numbers to kill scope ("we don't need X at this scale") |
| Depth | Coherent API/data/flow | Identifies bottlenecks + consistency per flow | Selective deep dives; knows what NOT to design |
| Trade-offs | States them when asked | Proactively names cost of every choice | Second-order effects: ops burden, failure modes the choice introduces, org costs |
| Failure handling | Handles obvious ones | Walks degradation modes unprompted | Designs the degradation ladder; metastable failure awareness |
| Delivery | Describes implementation | Phased rollout + migration plan | Evolution story at 10x/100x; reversibility instincts |

Signals that upgrade a score: stating assumptions in minute one; quantified estimates tied to decisions; walking failures unprompted; "ship boring" right-sizing; treat interviewer as colleague (buy-in checkpoints).

Signals that cap a score: no numbers all session; memorized architecture recital that ignores the stated constraints; Kafka/microservices reflex at small scale; defending a choice with "it's best practice"; zero clarifying questions.

## Feedback format

Deliver in this order, written:

1. **Overall**: level practiced / level demonstrated (rubric terms), one line.
2. **Scores**: rubric dimensions, each with cited evidence from the session.
3. **The one thing**: single highest-leverage improvement, concrete ("ask for scale before drawing anything; it would have killed the sharding detour").
4. **What was strong**: name it specifically — reinforcement needs evidence too.
5. **Drill prescription**: 2-3 problems from references/problems.md targeting weak dimensions.

Never soften the grade — candidates pay for this practice precisely because real interviews won't.
