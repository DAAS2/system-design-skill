---
name: Bug report
about: The skill produced a wrong, over-engineered, or hand-wavy design
labels: bug
---

**What did you ask?**
The prompt, verbatim. If a codebase was involved, note its rough shape (language, size, stores).

**What did it do wrong?**

<!-- Examples: "recommended Kafka for 2k users", "no capacity math anywhere", "missed the cache stampede in the stress test", "cited a file that doesn't exist" -->

- [ ] Over-engineered for the stated scale
- [ ] Under-engineered (missed an obvious failure)
- [ ] Numbers wrong or missing
- [ ] Wrong mode triggered
- [ ] Artifact malformed
- [ ] Other

**What did you expect instead?**

**Which agent + model?** (Claude Code / opencode / Codex / Cursor / ... and model, if known)

**Output excerpt** (paste the relevant part)

---
A bad design produced *with* the skill is the most valuable bug report this repo can get. Consider also pasting the same prompt's output *without* the skill if you have it.
