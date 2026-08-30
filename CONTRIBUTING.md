# Contributing to system-design

Thanks for helping make AI agents design systems like senior engineers. Contributions of every size are welcome — especially corrections with sources.

## The fastest ways to help

1. **Fix a number.** Every constant in `references/numbers.md` and `references/cost.md` should be sourced and current. If you have a better number, open a PR that states the value, the source, and the date.
2. **Add a failure injection.** `references/stress-tests.md` defines the 12 injections. A 13th that catches a real class of disaster is a great PR — include the antidote.
3. **Add a red flag.** `references/method-review.md` — red flags need: the signature to look for, why it hurts, and the fix.
4. **Run the evals and publish your results.** Different models behave differently; more data makes the claims honest. See `evals/README.md`.
5. **Report a bad design.** If the skill produced an over-engineered or hand-wavy design for your prompt, open an issue with the prompt and output. These are gold.

## Ground rules

- **Structure is load-bearing.** The skill must stay: one `SKILL.md` under 500 lines, references exactly one level deep, no README inside the skill folder. CI enforces this (`python tools/validate_skill.py`).
- **No external dependencies.** `scripts/botec.py` is stdlib-only by design — it must run on any machine with Python 3.8+.
- **No time-sensitive facts without a "verify" label.** Cloud prices and quotas drift; label them approximate.
- **No secrets, no network calls, no prompt-injection surface.** The skill must be safe to install sight-unseen (users should still audit — see SECURITY.md).
- **Terse, imperative voice.** The references are instructions to an agent, not prose for humans.

## Before you open a PR

```
cd system-design/scripts && python -m unittest test_botec   # calculator golden tests
python tools/validate_skill.py                               # structure + frontmatter
```

Both must pass. If you changed capacity math, update the golden values in `test_botec.py` and show the arithmetic in the PR description.

For anything that changes the method (gates, modes, rubric), open an issue first so we can discuss — method changes ripple through every reference file.
