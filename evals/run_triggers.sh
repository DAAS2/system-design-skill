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
#   ./run_triggers.sh                # checks + prompts + scoring rules
#   ./run_triggers.sh --checks       # validate trigger_evals.json structure only
#   ./run_triggers.sh --prompts      # print the per-query prompts to paste
#   ./run_triggers.sh --judge        # print the scoring rules + tally template
#   ./run_triggers.sh --auto --tool opencode [--reps N] [--set all|train|validation]
#                    [--timeout S] [--only id1,id2]
#       Invoke the agent CLI per case, parse YES/NO + behavioral skill-load
#       evidence, tally, and write evals/out/triggers/results-<tool>-<date>.{json,md}.
#       Supported tools: opencode (`run`), claude (`-p`), codex (`exec`),
#       gemini (positional); unknown tools fall back to `<tool> run <prompt>`.
#       reps defaults to 1 (protocol target: 3 — publish n with the table).
#       --only re-runs specific case ids and merges into today's results —
#       use it to re-run timed-out cases.
#   Windows Git-Bash: cd /c/Projects/skill/system_design_skill  (forward slashes!)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVALS="$ROOT/evals"
MODE=""

case "${1:-}" in
  "") MODE="all" ;;
  --checks) MODE="checks" ;;
  --prompts) MODE="prompts" ;;
  --judge) MODE="judge" ;;
  --auto) MODE="auto" ;;
  *) echo "error: unknown flag $1" >&2; exit 1 ;;
esac

auto() {
  TOOL="opencode"; REPS=1; SET="all"; TIMEOUT=420; ONLY=""
  shift || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --tool) TOOL="$2"; shift 2 ;;
      --reps) REPS="$2"; shift 2 ;;
      --set) SET="$2"; shift 2 ;;
      --timeout) TIMEOUT="$2"; shift 2 ;;
      --only) ONLY="$2"; shift 2 ;;
      *) echo "error: unknown --auto option $1" >&2; exit 1 ;;
    esac
  done
  echo "== Trigger evals — automated run =="
  echo "tool: $TOOL · reps: $REPS · set: $SET · timeout/call: ${TIMEOUT}s${ONLY:+ · only: $ONLY}"
  echo
  python - "$TOOL" "$REPS" "$SET" "$TIMEOUT" "$ROOT" "$ONLY" <<'PY'
import json, pathlib, re, subprocess, sys, datetime, shutil, tempfile

tool, reps, only_set, timeout, root, only_arg = (
    sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), pathlib.Path(sys.argv[5]), sys.argv[6])
only_ids = [i.strip() for i in only_arg.split(",") if i.strip()]
spec = json.loads((root / "evals" / "trigger_evals.json").read_text(encoding="utf-8"))
skill = (root / "system-design" / "SKILL.md").read_text(encoding="utf-8")
desc = re.search(r"description:\s*(.+)", skill.split("---")[1]).group(1).strip()

def build_cmd(prompt):
    if tool == "claude":
        return ["claude", "-p", prompt]
    if tool == "codex":
        return ["codex", "exec", prompt]
    if tool == "gemini":
        return ["gemini", prompt]
    if tool == "opencode":
        return ["opencode", "run", prompt]
    return [tool, "run", prompt]

if not shutil.which(build_cmd("x")[0]):
    print(f"error: `{tool}` CLI not found on PATH", file=sys.stderr)
    sys.exit(2)

TEMPLATE = """QUERY:
{query}

Before answering the query itself: a skill named "system-design" is installed, with this description on file:

---
{desc}
---

STEP 1 (answer this first): Would you load that skill to work on the query above? Answer exactly YES or NO, then one line why.
STEP 2: Answer the query as you normally would."""

sets = ["train", "validation"] if only_set == "all" else [only_set]
# The agent's cwd must NOT be inside any git repo: trigger-run agents do real
# work (maps, ADRs, capacity plans) and will write artifacts into whatever
# project root they find. Use a neutral temp dir.
workdir = pathlib.Path(tempfile.mkdtemp(prefix="trigger-run-"))
print(f"agent workspace: {workdir}")
stamp = datetime.date.today().isoformat()
res_path = workdir / f"results-{tool}-{stamp}.json"

# --only re-runs specific case ids and merges into today's existing results
prev_rows = []
if only_ids and res_path.is_file():
    prev_rows = json.loads(res_path.read_text(encoding="utf-8")).get("rows", [])
rows = [] if not only_ids else [r for r in prev_rows if r["id"] not in only_ids]

timed_out = {"train": 0, "validation": 0}
for set_name in sets:
    for case in spec[set_name]:
        if only_ids and case["id"] not in only_ids:
            continue
        rows = [r for r in rows if r["id"] != case["id"]]
        answers, loaded_flags = [], []
        for rep in range(reps):
            prompt = TEMPLATE.format(query=case["query"], desc=desc)
            try:
                out = subprocess.run(build_cmd(prompt), encoding="utf-8", errors="replace",
                                     timeout=timeout, cwd=str(workdir),
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                resp = out.stdout or ""
            except subprocess.TimeoutExpired:
                resp = ""
                timed_out[set_name] += 1
                print(f"  TIMEOUT {case['id']} rep{rep + 1}", file=sys.stderr, flush=True)
            m = re.search(r"(?im)^\s*\**\s*(yes|no)\b", resp) or re.search(r"\b(yes|no)\b", resp[:600], re.I)
            ans = m.group(1).lower() if m else "?"
            # behavioral evidence: did the host actually load the skill?
            loaded = 'skill "system-design"' in resp.lower()
            answers.append(ans)
            loaded_flags.append(loaded)
        said_yes = sum(1.0 for a in answers if a == "yes") / reps
        loaded_yes = sum(1.0 for l in loaded_flags if l) / reps
        rows.append({"id": case["id"], "set": set_name, "should": case["should_trigger"],
                     "answers": answers, "loaded": loaded_flags,
                     "said_yes": said_yes, "loaded_yes": loaded_yes,
                     "timed_out": "?" in answers})
        correct = said_yes if case["should_trigger"] else 1 - said_yes
        flag = "ok " if correct >= 0.5 else "MISS"
        to = " (TIMED OUT)" if "?" in answers else ""
        print(f"  [{flag}] {case['id']:<28} want={'Y' if case['should_trigger'] else 'N'} "
              f"said={','.join(a.upper() for a in answers)} loaded={','.join('Y' if l else 'N' for l in loaded_flags)}{to}",
              flush=True)

def frac(set_name, want, key):
    sel = [r for r in rows if r["set"] == set_name and r["should"] == want and not r.get("timed_out")]
    return (sum(r[key] for r in sel) / len(sel)) if sel else float("nan")

print("\n== Results ==")
summary = {}
for set_name in sets:
    summary[set_name] = {
        "trigger_rate": round(frac(set_name, True, "said_yes"), 3),
        "false_load_rate": round(frac(set_name, False, "said_yes"), 3),
        "behavioral_load_rate": round(frac(set_name, True, "loaded_yes"), 3),
        "behavioral_false_load_rate": round(frac(set_name, False, "loaded_yes"), 3),
        "timed_out": timed_out[set_name],
    }
    s = summary[set_name]
    print(f"  {set_name:<11} trigger-rate {s['trigger_rate']:.2f} · false-load-rate {s['false_load_rate']:.2f} · "
          f"behavioral load {s['behavioral_load_rate']:.2f} / false {s['behavioral_false_load_rate']:.2f} · "
          f"timeouts {s['timed_out']}", flush=True)
thr = spec["threshold"]
verdict = all(summary[s]["trigger_rate"] >= thr and summary[s]["false_load_rate"] <= thr for s in sets)
print(f"  threshold {thr} — {'PASS' if verdict else 'FAIL'} (target: >=0.80 / <=0.20) — "
      f"metrics computed over resolved cases; timeouts excluded and reported", flush=True)

res = {"tool": tool, "date": stamp, "reps": reps, "threshold": thr, "summary": summary,
       "verdict": "PASS" if verdict else "FAIL", "rows": rows}
res_path.write_text(json.dumps(res, indent=2), encoding="utf-8")
md = ["| case | set | should | said | loaded | said_yes |", "|---|---|---|---|---|---|"]
md += [f"| {r['id']} | {r['set']} | {'yes' if r['should'] else 'no'} | {','.join(a.upper() for a in r['answers'])} | {','.join('Y' if l else 'N' for l in r['loaded'])} | {r['said_yes']:.2f} |" for r in rows]
md += ["", f"summary: `{json.dumps(summary)}` — verdict: **{res['verdict']}** (timeouts excluded from rates)"]
(workdir / f"results-{tool}-{stamp}.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nresults written: {res_path}", flush=True)
PY
}

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
  auto) auto "$@" ;;
esac
