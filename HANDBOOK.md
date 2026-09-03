# Project Handbook — everything about system-design

The complete record: what this project is, why it exists, how it works, what it measurably does, who it serves, how it competes, how it will grow, and how to keep it alive. Written for the maintainer, prospective contributors, and anyone evaluating the project.

---

## 1. What this project is

**One line:** a staff engineer's system design brain for your coding agent.

**Two lines:** an Agent Skills folder (`system-design/`) that makes AI coding agents design, map, review, and evolve software systems with capacity math, failure analysis, right-sizing, and cost accounting — the behaviors of a senior engineer, enforced as gates rather than suggestions.

**Repository:** `DAAS2/system-design-skill` (MIT, Agent Skills open standard, installable in 40+ tools). **Launch status: repo still private at time of writing — the distribution claim below is untestable until it goes public and v1.0.0 is tagged/released (launch-sequence Day 0).**

### Elevator pitches, by audience

- **Working engineer:** "Your agent designs like it read one blog post. This skill makes it design like someone who's been paged."
- **Interview candidate:** "A system design mock interviewer and grader that doesn't soften the verdict, installed in your coding agent."
- **Tech lead:** "It maps your actual codebase, reviews your design docs with a scored rubric, and plans migrations with rollback at every phase."
- **Skeptic:** "Numbers first, failures walked, over-engineering deleted, cost estimated. Then it writes the doc so your team can review it."

---

## 2. The problem it solves

Two failure modes define AI-generated architecture:

1. **Scale theater** — agents propose Kafka, Kubernetes, and microservices for products that fit on one Postgres. It's the "Claude suggested Kafka for my todo app" meme, and it's not a joke — it's the default behavior.
2. **Hand-waving** — no numbers, no failure modes, no non-goals, no cost. "It's scalable because we use microservices."

**Why now:** agents are writing architecture daily, the Agent Skills open standard (2025-12) made skills portable across 40+ tools, and the system design knowledge base (DDIA, Alex Xu, SRE, the classic papers) is settled enough to distill into checklists an agent will actually enforce.

**What makes this project different from all prior art:** it is codebase-first. Everything else designs greenfield whiteboards; this one maps what you actually run, reviews what you actually wrote, and plans the migration you actually owe your team.

---

## 3. What the skill does

### Six modes (auto-detected from the request)

| Mode | Trigger example | Output artifact |
|---|---|---|
| design | "design a URL shortener for 100M daily reads" | `docs/design/YYYY-MM-DD-<name>.md` — ADR-style doc + Mermaid diagram |
| map | "what does our architecture actually look like?" | `docs/architecture/as-is.md` — components, flows, data stores, risk register, every claim cites a file path |
| review | "review this design doc / PR / ADR" | scored report across 10 dimensions + verdict (ship / fix-then-ship / redesign) |
| evolve | "our monolith's payment code blocks releases" | phased migration plan (strangler fig, outbox, dual-write + backfill + cutover) with rollback per phase |
| interview | "mock system design interview, grade me hard" | curveball-injecting coaching + mid/senior/staff grading with cited evidence |
| component | "SQL or NoSQL?", "Kafka vs SQS?", "cache strategy?" | decision-table answer: default, when to deviate, cost of the choice |

### The four gates (design / review / evolve only)

1. **Numbers** — capacity math runs first via the bundled `botec.py` calculator; every component traces to a number. "91 TB / 5 yr ⇒ single Postgres is out."
2. **Stress-test** — all 12 failure injections walked: dependency down, 10x spike, hot key, cache stampede, retry storm, split-brain, poison message, slow consumer, region loss, clock skew, cascading failure, metastable failure.
3. **Right-sizing** — tier-checked (prototype → planetary); over-tier components are deleted or justified with numbers, not adjectives.
4. **Cost** — rough monthly bill + cost per 1k requests; price catalog included; cost decides ties.

### How it works technically

- **Progressive disclosure:** ~270 tokens of metadata always in context (the expanded, trigger-hardened description is the load-bearing string); the 148-line SKILL.md loads on trigger; 14 reference files load on demand. Idle cost ≈ nothing.
- **One lean skill, not 22 sub-skills:** the competitor's approach is a building-block wiki with per-component skills; this is a mode router + on-demand references. Leaner, cheaper, easier to audit.
- **`scripts/botec.py`:** stdlib-only capacity calculator (QPS/storage/bandwidth/servers/cache + "decisions these numbers force" heuristics) with golden tests.
- **No network, no keys, no telemetry.** Safe to install sight-unseen (see SECURITY.md).
- **LLM-era content:** references include RAG pipelines, vector search, LLM serving physics (KV cache math, continuous batching), agent architectures, GPU scheduling — the layer most system design material predates.

---

## 4. Evidence it works

### Eval suite (iteration 1, 2026-08-30)

20 fresh agent sessions (10 evals × 2 arms), 10 blind judge sessions, behavior-by-behavior scoring with quoted evidence:

| Eval | Max | With-skill | Baseline |
|---|---|---|---|
| design-url-shortener | 7 | 7 | 4.5 |
| design-rate-limiter | 5 | 5 | 4 |
| right-size-pushback | 4 | 4 | 3.5 |
| map-codebase | 7 | 7 | 4 |
| review-flawed-design | 6 | 6 | 5 |
| evolve-monolith-extract | 7 | 7 | 6 |
| component-sql-vs-nosql | 4 | 4 | 4 |
| estimate-capacity | 4 | 4 | 3.5 |
| design-rag-pipeline | 6 | 6 | 6 |
| interview-coach | 6 | 6 | 5.5 |
| **Total** | **56** | **56 (100%)** | **46 (82%)** |

**Headline loss for baseline:** recommended Kafka + multi-region active-active + a read/write microservice split for a 5k-rps URL shortener (see the griller). Headline wins for the skill: artifacts that exist, diagrams that render, numbers that force decisions, failure walks, and the interview "one thing".

**Honest limits:** one model, one date; auto-trigger not tested (skill was force-loaded); judges were independent but read both outputs. Reproduce with `./evals/run.sh` — that's the point of shipping the suite.

### Example outputs (verbatim, from the eval runs)

`examples/` contains six real artifacts plus the griller: URL shortener design, rate limiter design, as-is map of a small e-commerce repo, checkout design review, payments extraction plan, interview grading, and the baseline-vs-skill tear-down.

---

## 5. Users

### Segments

| Segment | Motivation | Frequency of use | Willingness to star | Notes |
|---|---|---|---|---|
| **Working engineers (mid+)** using AI agents | Stop over-engineered suggestions; design docs that survive review | Weekly | High — this is the core audience | Daily CRUD work is solved by the component mode; design/review modes are the flagship |
| **System design interview candidates** | Practice + hard grading | Intense for weeks, then churn (they pass and leave) | Medium — transactional | Largest ready-made market (ByteByteGo/Grokking scale); interview mode is the hook |
| **Staff/principal architects** | Map/review/evolve on real repos | Monthly | High if impressed | Deepest users; will file the best issues |
| **Tech leads / engineering managers** | Migration planning, design doc standards | Monthly | Medium | Care about artifacts and cost |
| **PMs / non-engineers** | "Explain our architecture" | Rarely | Low | Skill is too technical for them alone |

### Honest demand math

- Global skill-installer population across all agents: hundreds of thousands, not millions.
- Realistic ceiling for this skill: 20-50k people ever try it; 5-15k keep it installed.
- **1k GitHub stars ≈ 1-2% of everyone who ever sees the repo** ⇒ needs ~50-100k impressions ⇒ requires a real launch, not just quality (see §7).
- Baseline behavior of a great repo without distribution: ~100-300 stars in year one. The 64-star competitor is the calibration point.

### Persona workflows (how people actually use it)

- **"Maria, backend engineer, 3 years in":** asks "SQL or NoSQL for our ticketing platform?" → gets a decision-table answer with the cost of the choice, in seconds. Weekly: "review this design" before sending to her tech lead. Monthly: "map our checkout service" before an incident review.
- **"Dev, prepping for Meta L5":** "mock system design interview, grade me hard" every evening for three weeks. The coach poses problems, injects curveballs, grades with evidence, prescribes drills. After the offer: uninstalls. That's fine — churn is the business model of the category.
- **"Priya, staff engineer":** runs map mode on a service she inherited, then evolve mode for the payments extraction she's been asked to plan. Uses the failure-mode table as a review checklist in every design she reads.

---

## 6. Competitive landscape

| | Plain agent | Building-block wikis (proyecto26) | Books/courses (Xu, DDIA) | **This skill** |
|---|---|---|---|---|
| Works on existing codebases | No | No | No | **Yes (map/review/evolve)** |
| Enforces capacity math | Rarely | Suggested | Taught, not enforced | **Hard gate + calculator** |
| Failure-mode walk | Rarely | Checklist | Taught | **Hard gate, 12 injections** |
| Kills over-engineering | No | Advises | Taught | **Hard gate + tier table** |
| Costs the design | No | Sometimes | Rarely | **Gate + price catalog** |
| Artifacts | Chat | Docs | Whiteboard | **Files in docs/, diffable** |
| LLM-era content | Partial | Partial | Mostly absent | **Dedicated reference** |
| Install surface | n/a | 22 skills, Claude-centric | n/a | **1 skill, 40+ tools** |

**Fairness note:** proyecto26/system-design-skills (64★) is well-built and was the first mover; its building-block composition is a legitimate approach. Our differentiation is codebase-first modes and the enforcement gates, plus a leaner install surface. The market is early; both can win.

**The long-term threat:** baseline models improve. The 82% baseline will climb. The durable moat is not the knowledge (models know DDIA) — it's the *method*: gates that block, artifacts that persist, evidence that cites. Keep the method as the product, not the trivia.

---

## 7. Marketing & distribution playbook

### Positioning & messaging

Primary hook (viral): **"Your agent wanted to give you Kafka. This skill gives you Postgres."**

Supporting hooks:
- "A staff engineer's system design brain for your coding agent."
- "It read your codebase, mapped your architecture, and found four S1 risks before your on-call did."
- "My agent gave my interview answer a 2.5/10 and cited the transcript. I needed that."
- The griller: "Same prompt, two agents — watch one of them get torn apart."

### Launch sequence (week one)

**Day 0 — prep:**
- [x] Repo polished: README, hero SVG, badges, examples, evals, INSTALL.md, installers
- [ ] GitHub repo created, pushed, About description + topics filled
  (description suggestion: *"System design for coding agents: map, design, review & evolve architectures with capacity math, failure stress-tests, and right-sizing gates."*)
  (topics: system-design, agent-skills, claude-code, opencode, cursor, codex, architecture, distributed-systems, llm, rag, skills)
- [ ] Release v1.0.0 tag + GitHub Release notes
- [ ] `examples/design-griller-baseline-vs-skill.md` rendered to a screenshot for social posts
- [ ] Eval table rendered as one image

**Day 1 — Show HN + Reddit:**
- [ ] **HN "Show HN":** title: *"Show HN: I gave my AI coding agent a staff engineer's system design brain"* — first comment carries the griller screenshot + eval table + install one-liner. Best time: ~7-9am ET weekday. Be present in the thread for 6+ hours, answer everything, don't be defensive.
- [ ] **r/ClaudeAI** + **r/OpenCode** (or r/opencode) + **r/ChatGPTCoding**: "My agent kept proposing Kafka. I wrote a skill that stops it." + griller link.
- [ ] **r/systemdesign**: the interview-coach angle + grading example.
- [ ] **r/ExperiencedDevs**: the pain-point angle (agent over-engineering) — text post with the griller.

**Day 2 — X/Twitter + newsletters:**
- [ ] Thread: 1) the meme (agents → Kafka), 2) the before/after quote, 3) eval numbers, 4) install link. Tag: @VercelLabs skills, relevant builders (anthropics, opencode team).
- [ ] Submit to newsletters: TLDR Newsletter, Bytes (YTZ), This Week in AI, AI Engineer (Latent Space), System Design Newsletter (ByteByteGo-adjacent audiences).
- [ ] lobste.rs submission.

**Day 3+ — directories & awesome-lists (this is where installs compound):**
- [ ] ComposioHQ/awesome-claude-skills (4k★, PR)
- [ ] VoltAgent/awesome-agent-skills (PR)
- [ ] travisvn/awesome-claude-skills, Samarth0211/awesome-claude-skills-2026 (PR)
- [ ] Skills directories: clskills.in (submit), skills.sh (verify auto-index), claudepluginhub, claudeskills.info
- [ ] agentskills.io community listing if available

**Week 2+ — content flywheel:**
- [ ] Blog post (publish on your own site + dev.to + Medium): *"I ran 20 blind agent sessions to prove a skill makes agents design like seniors"* — methodology + results + griller.
- [ ] Short YouTube/short-form video: "Watch an AI recommend Kafka for 2,000 users — and a skill say no with math."
- [ ] Every issue labeled `good first issue` keeps momentum; every eval PR gets a shout-out.
- [ ] Monthly release cadence (v1.1, v1.2...) keeps the repo alive in feeds; each release = one social post.

### What NOT to do

- Don't spam subreddits daily; one strong post per community.
- Don't trash proyecto26 publicly; it invites a dogpile on you.
- Don't buy stars; the GitHub trust graph is how the repo compounds.
- Don't claim "50k stars incoming" anywhere — it reads as hustle, not quality.

---

## 8. Star strategy (honest)

Stars come from three things, in order: **a screenshot-able before/after**, **a one-command install**, and **proof** (evals). All three exist. What's missing is impressions (§7).

Realistic trajectory:
- Launch week, with a good Show HN: 150-400 stars.
- Month 1-2, awesome-list listings + newsletters compound: 400-800.
- Month 3-6, content flywheel + releases: 800-1,500 — **1k is achievable within ~6 months of a good launch**, and becomes likely if any single post lands big (HN front page is worth 300-800 alone).
- Without the launch: ~100-300/yr. Quality does not self-distribute.

---

## 9. Maintenance plan

- **Numbers drift is the existential risk.** `references/numbers.md` and `references/cost.md` carry prices and capacities; they will go stale. Policy: every PR touching a number requires a source + date; a yearly "numbers audit" issue is opened each January.
- **Roadmap:** v1.1 provider references (AWS/Azure/GCP managed-service mappings); v1.2 second eval iteration on a different model + more examples; v1.3 pluggable company-standards file. Backlog: LLM-serving capacity calculator, multi-region decision tree, ADR auto-writer.
- **Issue hygiene:** bug template captures the prompt + output + model — bad designs produced with the skill are the most valuable issues. `good first issue` labels for numbers-with-sources and eval PRs.
- **Versioning:** SemVer; method changes (gates/modes/rubric) = MAJOR, content = MINOR, corrections = PATCH. CHANGELOG.md maintained.
- **CI is the guardrail:** structure validation, frontmatter checks, botec golden tests, evals JSON, installer syntax — all run on every push.

---

## 10. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Baseline models improve, shrinking the eval gap | High | Medium | The method (gates/artifacts) is the product, not the trivia; keep gates strict |
| Numbers/prices go stale | High | Medium | Source+date rule on every number; yearly audit; "verify" labels |
| Interview users churn after passing | Certain | Low | They're one of four segments; the working-engineer segment doesn't churn |
| Skill feels verbose to casual users | Medium | Medium | Component mode is fast by design; document the modes so users pick the fast path |
| Competitor catches up on codebase modes | Medium | Medium | Moat = enforcement gates + artifact quality + eval transparency, not feature list |
| Prompt-injection via skill content (someone's malicious edit) | Low | High | SECURITY.md trust model; audit-before-install guidance; no network calls by design |
| Repo dies from no updates | Medium | High | Monthly cadence; CONTRIBUTING makes contributions cheap; roadmap is public |

---

## 11. Repository map

```
system-design-skill/
├── README.md                 # front door: pitch, demo, install, evals, FAQ
├── HANDBOOK.md               # this file — the complete project record
├── INSTALL.md                # 40+ tool install matrix, verification, troubleshooting
├── install.sh / install.ps1  # auto-detecting installers (14 targets, idempotent)
├── CHANGELOG.md              # SemVer history
├── CONTRIBUTING.md           # contribution guide + ground rules
├── SECURITY.md               # trust model + reporting
├── LICENSE                   # MIT
├── assets/hero.svg           # README banner
├── examples/                 # verbatim skill outputs: 6 artifacts + the griller
├── evals/
│   ├── evals.json            # 10 behavioral evals (prompt + expected behaviors)
│   ├── README.md             # methodology + iteration-1 results
│   ├── run.sh                # one-command reproduction (checks + scaffold + prompts + judge)
│   └── fixtures/             # demo-app codebase (map eval) + interview transcript
├── system-design/            # THE SKILL
│   ├── SKILL.md              # mode router + four gates (148 lines)
│   ├── scripts/botec.py      # capacity calculator (+ golden tests)
│   └── references/           # 14 files: 5 methods, 9 knowledge (see README)
├── tools/validate_skill.py   # structure + frontmatter enforcement
└── .github/                  # CI, issue templates, PR template
```

---

## 12. Metrics to track

- **Stars** (weekly velocity, not just total), **installs** (skills.sh reports, npx skills telemetry if enabled), **issues** (inflow + median time to close), **forks/contributors** (health), **eval PRs from other models** (the trust flywheel), **release-to-release star delta** (which releases move the needle).
- Success in 12 months: ≥1k stars, ≥1 community eval run from a different model, ≥1 issue-driven skill improvement, installs ≥ 10x stars.

---

## 13. Final word

This is a project with a real pain point, a defensible differentiation, and — unusually for the skills ecosystem — measured proof it works. The two things that decide whether it reaches the 1k-star goal are both outside the repo: **distribution** (§7) and **maintenance discipline** (§9). The repo is the easy part, and it's done. Go launch.