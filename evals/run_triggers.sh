#!/usr/bin/env bash
#
# run_triggers.sh — test whether the skill FIRES on real user phrasing.
#
# The behavioral evals (run.sh) force-load the skill, so invocation itself is
# never measured. This script scaffolds the trigger test: for each labelled
# query in trigger_evals.json, ask a fresh agent — given the skill's actual
# description — whether it would load the skill for that query. Repeat 3x per
# query, tally the trigger rate, compare against the threshold.
#
# Usage:
#   ./run_triggers.sh            # checks + worksheet + prompts + scoring rules
#   ./run_triggers.sh --checks   # validate trigger_evals.json structure only
#   ./run_triggers.sh --prompts  # print the per-query prompts to paste
#   ./run_triggers.sh --judge    # print the scoring rules + tally template
#
# Windows: run inside Git-Bash.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVALS="$ROOT/evals"
MODE=""

case "${1:-}" in
  "") MODE="all" ;;
  --checks) MODE="checks" ;;
  --prompts) MODE="prompts" ;;
  --judge) MODE="judge" ;;
  *) echo "error: unknown flag $1 (--checks | --prompts | --judge)" >&2; exit 1 ;;
esac

checks() {
  echo "== Trigger eval checks =="
  python "$ROOT/tools/validate_trigger_evals.py"
}

prompts() {
  (cd "$EVALS" && python - <<'PY'
import json, pathlib, re, sys

root = pathlib.Path("..") / "system-design"
skill = (root / "SKILL.md").read_text(encoding="utf-8")
desc = ""
fm = skill.split("---")[1]
m = re.search(r"description:\s*(.+)", fm)
if m:
    desc = m.group(1).strip()
if not desc:
    print("error: could not extract description from SKILL.md", file=sys.stderr)
    sys.exit(1)

spec = json.load(open("trigger_evals.json"))
print("== Trigger prompts ==")
print("For each case, paste this into a FRESH session that has the skill")
print("installed at its normal path. Do not force-load it; we are testing")
print("whether the description alone would cause a load.\n")
template = """QUERY:
{query}

Before answering the query itself: a skill named "system-design" is
installed, with this description on file:

---
{desc}
---

STEP 1 (answer this first): Would you load that skill to work on the query
above? Answer exactly YES or NO, then one line why.
STEP 2: Answer the query as you normally would.
"""
n = 0
for set_name in ("train", "validation"):
    for case in spec[set_name]:
        n += 1
        print(f"--- {n}. [{set_name}] {case['id']}  (should_trigger: {str(case['should_trigger']).lower()}) ---")
        print(template.format(query=case["query"], desc=desc))
PY
)
}

judge() {
  (cd "$EVALS" && python - <<'PY'
import json

spec = json.load(open("trigger_evals.json"))
thr = spec["threshold"]
reps = spec["repetitions"]

print("== Scoring trigger runs ==")
print(f"Per case: rate = YES count / {reps} repetitions.")
print()
print("Set metrics:")
print("  trigger-rate      = mean(rate | should_trigger=true)   -> want HIGH")
print("  false-load-rate   = mean(rate | should_trigger=false)  -> want LOW")
print()
print("PASS (minimum): trigger-rate >= %.2f AND false-load-rate <= %.2f, per set." % (thr, thr))
print("GOOD (target):  trigger-rate >= 0.80 AND false-load-rate <= 0.20, per set.")
print()
print("Fill the tally (3 runs per case), then compute the rates:\n")
print("| case | set | should_trigger | r1 | r2 | r3 | rate |")
print("|---|---|---|---|---|---|---|")
for set_name in ("train", "validation"):
    for case in spec[set_name]:
        st = "yes" if case["should_trigger"] else "no"
        print(f"| {case['id']} | {set_name} | {st} | | | | |")
print()
print("Train set tunes the description; validation set is the held-out verdict.")
print("Publish your table as a PR to evals/README.md — trigger behavior is")
print("model-specific and every data point keeps the description honest.")
PY
)
}

case "$MODE" in
  all) checks; prompts; judge ;;
  checks) checks ;;
  prompts) prompts ;;
  judge) judge ;;
esac
