#!/usr/bin/env python3
"""Validate evals/evals.json structure. Run: python tools/validate_evals.py"""

import json
import sys
from pathlib import Path

REQUIRED = ("id", "mode", "prompt", "expected_behaviors")


def main() -> int:
    path = Path(__file__).resolve().parent.parent / "evals" / "evals.json"
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: evals.json is not valid JSON: {e}")
        return 1

    evals = spec.get("evals")
    if not isinstance(evals, list) or not evals:
        print("FAIL: 'evals' must be a non-empty list")
        return 1

    seen = set()
    for i, e in enumerate(evals, 1):
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            print(f"FAIL: eval #{i} missing fields {missing}")
            return 1
        if not isinstance(e["expected_behaviors"], list) or not e["expected_behaviors"]:
            print(f"FAIL: eval #{i} ({e['id']}) expected_behaviors must be a non-empty list")
            return 1
        if e["id"] in seen:
            print(f"FAIL: duplicate eval id {e['id']}")
            return 1
        seen.add(e["id"])

    print(f"OK: {len(evals)} evals, all fields present")
    return 0


if __name__ == "__main__":
    sys.exit(main())