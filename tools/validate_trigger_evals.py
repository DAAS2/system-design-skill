#!/usr/bin/env python3
"""Validate evals/trigger_evals.json structure. Run: python tools/validate_trigger_evals.py"""

import json
import sys
from pathlib import Path

MODES = {"design", "map", "review", "evolve", "interview", "component"}
REQUIRED = ("id", "query", "should_trigger", "rationale")


def check_set(evals: list, set_name: str, seen: set) -> list:
    failures = []
    if not evals:
        failures.append(f"{set_name}: must be a non-empty list")
        return failures
    for i, e in enumerate(evals, 1):
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            failures.append(f"{set_name} #{i} missing fields {missing}")
            continue
        if e["id"] in seen:
            failures.append(f"duplicate trigger id {e['id']}")
        seen.add(e["id"])
        if not isinstance(e["should_trigger"], bool):
            failures.append(f"{e['id']}: should_trigger must be a bool")
        if e["should_trigger"]:
            if e.get("expected_mode") not in MODES:
                failures.append(f"{e['id']}: expected_mode must be one of {sorted(MODES)}")
        elif "expected_mode" in e:
            failures.append(f"{e['id']}: should-not cases must not carry expected_mode")
        if not e.get("rationale", "").strip():
            failures.append(f"{e['id']}: rationale required (keeps the set auditable)")
    return failures


def main() -> int:
    path = Path(__file__).resolve().parent.parent / "evals" / "trigger_evals.json"
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: trigger_evals.json is not valid JSON: {e}")
        return 1

    failures = []
    seen: set = set()
    failures += check_set(spec.get("train", []), "train", seen)
    failures += check_set(spec.get("validation", []), "validation", seen)

    trues = sum(1 for s in ("train", "validation") for e in spec.get(s, []) if e.get("should_trigger"))
    falses = sum(1 for s in ("train", "validation") for e in spec.get(s, []) if not e.get("should_trigger", True))
    if not (0 < spec.get("threshold", 0) < 1):
        failures.append("threshold must be in (0, 1)")
    if spec.get("repetitions", 0) < 1:
        failures.append("repetitions must be >= 1")
    if trues < 4 or falses < 4:
        failures.append(f"need >= 4 should-trigger and >= 4 should-not cases (got {trues}/{falses})")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"OK: trigger evals — {trues} should-trigger, {falses} should-not, train+validation split")
    return 0


if __name__ == "__main__":
    sys.exit(main())
