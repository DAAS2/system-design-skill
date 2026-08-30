---
name: Content contribution
about: New numbers, failure injections, red flags, classic problems, or eval results
labels: enhancement
---

**What are you adding?**

- [ ] Better number (with source + date)
- [ ] New failure injection (with antidote)
- [ ] New review red flag
- [ ] Classic problem + key insight
- [ ] LLM-era infrastructure content
- [ ] Eval run results

**Details**

**Sources** (required for numbers: link/paper/book + date)

**Checks run**
- [ ] `python tools/validate_skill.py` passes
- [ ] `python -m unittest test_botec` passes (if math changed, golden values updated with shown arithmetic)
