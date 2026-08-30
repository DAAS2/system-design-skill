#!/usr/bin/env bash
#
# run.sh — reproduce the skill's eval suite in one command.
#
# This script does what is deterministic (calculator golden tests, skill
# structure validation) and scaffolds what needs an agent: for each of the
# 10 evals it creates a baseline/ and with-skill/ folder with the prompt
# ready to paste, then prints the judging checklist for each arm.
#
# Usage:
#   ./run.sh            # full reproduction: checks + scaffold + prompts
#   ./run.sh --checks   # only the deterministic checks
#   ./run.sh --prompts  # only print the 10 eval prompts (no scaffold)
#   ./run.sh --judge    # print the grading instructions + checklists
#
# Windows: run inside Git-Bash.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVALS="$ROOT/evals"
OUT="$EVALS/out"
MODES=(checks prompts judge)

MODE=""
case "${1:-}" in
  "") MODE="all" ;;
  --checks) MODE="checks" ;;
  --prompts) MODE="prompts" ;;
  --judge) MODE="judge" ;;
  *) echo "error: unknown flag $1 (--checks | --prompts | --judge)" >&2; exit 1 ;;
esac

checks() {
  echo "== Deterministic checks =="
  (cd "$EVALS/../system-design/scripts" && python -m unittest test_botec -v 2>&1 | tail -2)
  python "$ROOT/tools/validate_skill.py"
  (cd "$EVALS" && python -c "import json; json.load(open('evals.json')); print('evals.json: OK')")
}

scaffold() {
  echo
  echo "== Scaffolding eval folders =="
  (cd "$EVALS" && python - <<'PY'
import json, pathlib
out = pathlib.Path("out")
spec = json.load(open("evals.json"))
for e in spec["evals"]:
    for arm in ("baseline", "with-skill"):
        d = out / e["id"] / arm
        d.mkdir(parents=True, exist_ok=True)
        (d / "prompt.md").write_text(e["prompt"] + "\n", encoding="utf-8")
    print(f"  {e['id']}: baseline/ + with-skill/ ready")
print()
print("For each eval, in a FRESH agent session:")
print("  1. baseline:    paste prompt.md into an agent WITHOUT the skill installed")
print("  2. with-skill:  paste prompt.md into an agent WITH the skill installed")
print("  3. save each answer as response.md in its folder")
print("  4. run ./run.sh --judge to grade both arms")
PY
)
}

prompts() {
  echo "== The 10 eval prompts =="
  (cd "$EVALS" && python - <<'PY'
import json
spec = json.load(open("evals.json"))
for i, e in enumerate(spec["evals"], 1):
    print(f"\n--- {i}. {e['id']} ({e['mode']}) ---")
    print(e["prompt"])
PY
)
}

judge() {
  echo "== Judging instructions =="
  echo "For each eval: read the baseline and with-skill response.md files."
  echo "Score every expected behavior below per arm:"
  echo "  1 = clearly present with substance, 0.5 = partial, 0 = absent."
  echo "Demand evidence (quote the line that earns the point)."
  echo
  (cd "$EVALS" && python - <<'PY'
import json
spec = json.load(open("evals.json"))
for i, e in enumerate(spec["evals"], 1):
    print(f"--- {i}. {e['id']} ---")
    for j, b in enumerate(e["expected_behaviors"], 1):
        print(f"  {j}. {b}")
    print(f"  Max: {len(e['expected_behaviors'])}")
PY
)
  echo
  echo "Compare totals. Publish your results as a PR to evals/README.md —"
  echo "different models behave differently, and every data point helps."
}

case "$MODE" in
  all) checks; scaffold; prompts; judge ;;
  checks) checks ;;
  prompts) prompts ;;
  judge) judge ;;
esac