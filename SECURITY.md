# Security Policy

## Trust model

This repo is an Agent Skill — you are installing *instructions an AI agent will follow*. Treat that accordingly:

- **Audit before installing.** Read `system-design/SKILL.md` and the files in `system-design/references/`. There is no code beyond `system-design/scripts/botec.py`.
- **The one script is stdlib-only, offline, and deterministic.** `botec.py` does arithmetic and prints tables. It makes no network calls, reads no environment variables, and writes no files. Verify it yourself — that's the point of shipping it readable.
- **No secrets.** The skill never asks for credentials. The word "key" appears only in the idempotency-key and API-key-rate-limiting sense.
- **No external content.** References mention vendor names and paper titles as facts; they instruct the agent to fetch nothing.

## Reporting a vulnerability

If you find a way this skill's content could cause an agent to exfiltrate data, execute something harmful, or damage a repo it works in:

1. Use [GitHub's private vulnerability reporting](../../security/advisories/new) for this repo.
2. Do not open a public issue for it.

Include the file, the line, and a reproduction sketch. You'll get a response within a week.

## Scope

In scope: anything shipped in this repository. Out of scope: the behavior of AI models or agent platforms themselves, and whatever a user's own agent does with content we didn't ship.
