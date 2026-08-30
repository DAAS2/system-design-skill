# Evals

Behavioral evals for the system-design skill. The claim under test: **with the skill, an agent designs like a senior engineer; without it, like a tutorial.**

## Method

1. Run each prompt in `evals.json` twice: baseline (no skill) and with-skill, fresh session each, same model.
2. Judge each run against the eval's `expected_behaviors` checklist: behavior present = 1, absent = 0. Half-points allowed for partial.
3. Judge blind if possible: shuffle outputs before grading.
4. Record per-eval scores and the totals; publish results below after each iteration of the skill.

## Deterministic checks

Not everything is subjective. CI runs the golden tests for the calculator:

```
cd system-design/scripts && python -m unittest test_botec
```

## Iteration log

### Iteration 1 — YYYY-MM-DD

_Replace after first real run. Record: with-skill score / baseline score per eval, judge notes, and what changed in the skill as a result._
