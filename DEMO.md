# DEMO.md — three prompts, three minutes

Installing is not proof. Paste these three prompts into your agent (with the skill
installed) and watch what comes back. Each links to a real artifact the skill produced
in the eval runs, so you know what "good" looks like before you compare.

**Setup (once):**

```bash
npx skills add DAAS2/system-design-skill --agent '*'
```

Then open a fresh session in any repo — an existing codebase makes prompts 2 and 3 land harder.

---

## 1. The oblique component question

```
Is Postgres enough for our workload, or do we need something fancier?
```

**What to look for:** it should refuse to answer until it has your numbers — DAU, read/write
per user, retention — then run the capacity math and give a decision-table answer: the default,
when to deviate, what the choice costs. No workload numbers from you = one clarifying question,
not a generic essay.

**Reference answer style:** `references/tradeoffs.md` (the decision tables it answers from) ·
baseline-vs-skill comparison: [`examples/design-griller-baseline-vs-skill.md`](examples/design-griller-baseline-vs-skill.md)

## 2. The repository map

```
What does our architecture actually look like? Map it.
```

**What to look for:** an as-is map in `docs/architecture/as-is.md` — components, request flows,
data stores, a risk register — where **every claim cites a file path** from your repo, plus a
"Not read / unknown" honesty section instead of confident guesses.

**Reference output:** [`examples/as-is-map-demo-app.md`](examples/as-is-map-demo-app.md) (a real map of the eval fixture repo)

## 3. The hard grade

```
Grade this system design interview answer like an L6 bar — be brutal. [paste a transcript or your last answer]
```

**What to look for:** a mid/senior/staff rubric score **with cited evidence** (it quotes your
answer back at you), curveballs injected while you answer if you do it interactively, and
exactly **one** highest-leverage fix — not a list of seven co-equal suggestions.

**Reference output:** [`examples/interview-grading-chat-system.md`](examples/interview-grading-chat-system.md)

---

## The one-minute version

If you only try one thing: ask **"how would you architect a ticket booking system?"**
before and after installing. Before: a component zoo with no numbers. After: capacity math
first, all 12 failure injections walked, a tier assignment, and a design doc on disk.

Full reproduction of the published eval numbers: [`evals/run.sh`](evals/run.sh) ·
trigger-behavior tally: [`evals/run_triggers.sh`](evals/run_triggers.sh)
