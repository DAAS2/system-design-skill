#!/usr/bin/env python3
"""Validate skill structure and frontmatter against Agent Skills conventions.

Checks:
  - SKILL.md exists, opens with '---' frontmatter, parses as YAML
  - name: kebab-case, <=64 chars, no reserved words (claude/anthropic)
  - description: non-empty, <=1024 chars, no XML tags
  - SKILL.md body <= 500 lines
  - every references/ file mentioned in SKILL.md exists on disk
  - no README.md inside the skill folder (docs live in references/)

Run from repo root: python tools/validate_skill.py
"""

import re
import sys
from pathlib import Path

MAX_LINES = 500
MAX_NAME = 64
MAX_DESC = 1024
RESERVED = ("claude", "anthropic")

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    skill_dir = root / "system-design"
    skill_md = skill_dir / "SKILL.md"

    check(skill_md.is_file(), "SKILL.md missing at system-design/SKILL.md")
    if not skill_md.is_file():
        print("\n".join(failures))
        return 1

    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Frontmatter must start at line 1
    check(lines and lines[0].strip() == "---", "frontmatter must open with --- on line 1")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        failures.append("frontmatter not closed with ---")
        print("\n".join(failures))
        return 1

    fm_text = "\n".join(lines[1:end])
    try:
        import yaml  # type: ignore

        fm = yaml.safe_load(fm_text) or {}
    except ImportError:
        # Minimal fallback parser: key: value lines only
        fm = {}
        for ln in fm_text.splitlines():
            m = re.match(r"^(\w[\w-]*):\s*(.*)$", ln)
            if m and not m.group(2).startswith(">"):
                fm[m.group(1)] = m.group(2).strip()
        print("note: PyYAML not installed, using minimal frontmatter parser")

    name = str(fm.get("name", ""))
    desc = str(fm.get("description", ""))

    check(bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name)),
          f"name must be kebab-case, got {name!r}")
    check(len(name) <= MAX_NAME, f"name must be <= {MAX_NAME} chars")
    check(not any(r in name.lower() for r in RESERVED), "name contains reserved word")
    check(bool(desc.strip()), "description must be non-empty")
    check(len(desc) <= MAX_DESC, f"description must be <= {MAX_DESC} chars (got {len(desc)})")
    check("<" not in desc and ">" not in desc, "description must not contain XML tags")

    body_lines = len(lines) - end - 1
    check(body_lines <= MAX_LINES, f"SKILL.md body must be <= {MAX_LINES} lines (got {body_lines})")

    check(not (skill_dir / "README.md").exists(),
          "no README.md inside skill folder (repo README lives outside)")

    # Referenced files must exist
    refs = sorted((skill_dir / "references").glob("*.md"))
    check(bool(refs), "references/ is empty or missing")
    ref_names = {f"references/{p.name}" for p in refs}
    for mention in ref_names:
        check(mention in text, f"SKILL.md never mentions {mention} (orphan reference)")

    for m in re.findall(r"references/[\w.-]+\.md", text):
        check((skill_dir / m).is_file(), f"SKILL.md references missing file: {m}")
    for m in re.findall(r"scripts/[\w.-]+\.py", text):
        check((skill_dir / m).is_file(), f"SKILL.md references missing script: {m}")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"OK: {name}")
    print(f"  description: {len(desc)}/{MAX_DESC} chars")
    print(f"  body: {body_lines}/{MAX_LINES} lines")
    print(f"  references: {len(refs)} files, all mentioned in SKILL.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
