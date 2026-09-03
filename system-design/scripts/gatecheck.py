#!/usr/bin/env python3
"""gatecheck.py — machine-checkable gate contract for design-mode artifacts.

The four gates are prose obligations in SKILL.md; this script makes their
OUTPUTS checkable. It parses a produced design doc and exits non-zero when a
gate output is missing:

  G1 capacity      botec output or equivalent capacity math (QPS avg/peak)
  G2 failure table all 12 failure injections walked (distinct rows found)
  G3 tier          a tier assignment (0-5) from the right-sizing gate
  G4 cost monthly  an estimated monthly cost figure
  G4 cost per 1k   a cost-per-1k-requests (or per-user-month) figure
  scope            an explicit non-goals section
  evolution        an evolution / "breaks first at 10x" section

Usage:
  python gatecheck.py <design-doc.md>            # human-readable report
  python gatecheck.py <design-doc.md> --json     # machine-readable (CI)
  python gatecheck.py <doc.md> --mode design     # only design is implemented

Exit codes: 0 all checks pass, 1 gate failures, 2 usage/IO error.

Detection is anchored to the skill's own template (references/output-templates.md).
Run it on every design doc before review:  "the agent promised" becomes
"the file passes".
"""

import json
import re
import sys
from pathlib import Path

# regex patterns, tolerant of the format variance real eval outputs show:
# "Redis (dependency) down", "10× traffic spike", "hot-key", "split brain".
INJECTION_PATTERNS = [
    r"dependenc\w*\s*\)?\s*down",
    r"10\s*[x×]",
    r"hot[- ]key",
    r"stampede",
    r"retry storm",
    r"split.brain",
    r"poison",
    r"slow consumer",
    r"region loss",
    r"clock skew",
    r"cascad",
    r"metastable",
]


def sections(text: str) -> dict:
    """Split markdown into {lowercased-heading: body} by ## headings."""
    out: dict = {"_preamble": ""}
    current = "_preamble"
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            current = m.group(1).strip().lower()
            out.setdefault(current, "")
        else:
            out[current] = out.get(current, "") + line + "\n"
    return out


def find_sections(secs: dict, *needles: str) -> str:
    """Concatenate every section whose heading contains any needle."""
    return "\n".join(
        body for heading, body in secs.items()
        if heading != "_preamble" and any(n in heading for n in needles)
    )


def check_capacity(secs: dict, whole: str) -> tuple:
    # botec named (the skill mandates citing it) or QPS avg/peak figures present
    if "botec" in whole.lower():
        return True, "botec run and cited"
    if re.search(r"qps[^.\n]{0,60}\d", whole, re.I) and re.search(r"peak", whole, re.I):
        return True, "capacity figures present (QPS + peak)"
    return False, "no botec output block or QPS figures — Gate 1 requires cited capacity math"


def check_failures(secs: dict, whole: str) -> tuple:
    body = (find_sections(secs, "failure") or whole).lower()
    found = sum(1 for pat in INJECTION_PATTERNS if re.search(pat, body, re.I))
    if found >= 12:
        return True, "all 12 failure injections walked"
    return False, f"failure table covers {found}/12 injections — Gate 2 requires all 12"


def check_tier(secs: dict, whole: str) -> tuple:
    if re.search(r"\btier\s*[-:]?\s*[0-5]\b", whole, re.I):
        return True, "tier assignment present (0-5)"
    return False, "no tier assignment line — Gate 3 requires tier 0-5 with evidence"


def check_cost_monthly(secs: dict, whole: str) -> tuple:
    body = find_sections(secs, "right-sizing", "cost") or whole
    if re.search(r"(monthly cost|cost per month|per month|\$/mo)\b", body, re.I) and re.search(r"\$\s?\d", body):
        return True, "monthly cost estimate present"
    return False, "no monthly cost figure — Gate 4 requires a rough monthly bill"


def check_cost_per_1k(secs: dict, whole: str) -> tuple:
    body = find_sections(secs, "right-sizing", "cost") or whole
    if re.search(r"(per 1k|/1k\b|per 1,000|per user per month)", body, re.I):
        return True, "cost per 1k requests (or per user-month) present"
    return False, "no cost-per-1k line — Gate 4 requires a number teams can reason about"


def check_non_goals(secs: dict, whole: str) -> tuple:
    if find_sections(secs, "non-goal", "non goal", "out of scope"):
        return True, "non-goals section present"
    if re.search(r"non[- ]?goals", whole, re.I):
        return True, "non-goals named in body"
    return False, "no non-goals section — scope discipline is part of the design"


def check_evolution(secs: dict, whole: str) -> tuple:
    body = find_sections(secs, "evolution", "next step", "open question")
    if body and re.search(r"10x|next step|breaks first", body, re.I):
        return True, "evolution section present"
    if re.search(r"breaks first at 10x|next step at 10x", whole, re.I):
        return True, "evolution naming present"
    return False, "no evolution section — name what breaks first at 10x"


CHECKS = [
    ("capacity", check_capacity, "Gate 1 — numbers"),
    ("failure-table", check_failures, "Gate 2 — stress-test"),
    ("tier", check_tier, "Gate 3 — right-sizing"),
    ("cost-monthly", check_cost_monthly, "Gate 4 — cost"),
    ("cost-per-1k", check_cost_per_1k, "Gate 4 — cost"),
    ("non-goals", check_non_goals, "scope"),
    ("evolution", check_evolution, "10x path"),
]


def check_document(text: str) -> list:
    secs = sections(text)
    whole = text
    return [
        {"id": cid, "gate": gate, "ok": fn(secs, whole)[0], "detail": fn(secs, whole)[1]}
        for cid, fn, gate in CHECKS
    ]


def is_comparison_doc(text: str) -> bool:
    """Teardown/comparison documents (e.g. examples/design-griller-*.md) contrast a
    baseline and a skill output — they are not a single produced design, so the gate
    contract does not apply. Detection is content-based, not filename-based."""
    low = text.lower()
    has_verdicts = "what the baseline" in low or "baseline claim" in low
    has_marker = "tear-down" in low or "teardown" in low or "griller" in low
    return has_marker and has_verdicts


def main(argv: list) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if "--mode" in " ".join(flags) or any(a.startswith("--mode") for a in argv):
        mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "design"
        if mode != "design":
            print(f"gatecheck: mode '{mode}' is not implemented yet (design only)", file=sys.stderr)
            return 2
    if len(args) != 1:
        print(__doc__)
        return 2
    path = Path(args[0])
    if not path.is_file():
        print(f"gatecheck: file not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")

    if is_comparison_doc(text):
        msg = (
            "gatecheck: this is a baseline-vs-skill comparison/teardown document, not a "
            "produced design — the gate contract applies to design-mode artifacts only "
            "(the repo CI-checks examples/design-url-shortener.md and design-rate-limiter.md)"
        )
        if "--json" in flags:
            print(json.dumps({"file": str(path), "ok": None, "skipped": msg}, indent=2))
        else:
            print(msg)
        return 2

    results = check_document(text)
    ok = all(r["ok"] for r in results)

    if "--json" in flags:
        print(json.dumps({"file": str(path), "ok": ok, "checks": results}, indent=2))
    else:
        status = "PASS" if ok else "FAIL"
        print(f"gatecheck: {path} — {status}")
        for r in results:
            mark = "  ok  " if r["ok"] else " FAIL "
            print(f"  [{mark}] {r['id']:<13} {r['gate']:<20} {r['detail']}")
        if not ok:
            print("  a gate failure blocks the output — fix the doc, not the checker")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
