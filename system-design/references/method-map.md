# Method: Map (codebase reverse-engineering)

## Contents
- [Purpose](#purpose)
- [Step 1: Inventory](#step-1-inventory)
- [Step 2: Trace request flows](#step-2-trace-request-flows)
- [Step 3: Map data stores](#step-3-map-data-stores)
- [Step 4: Map infra and delivery](#step-4-map-infra-and-delivery)
- [Step 5: Identify risks](#step-5-identify-risks)
- [Step 6: Write the as-is doc](#step-6-write-the-as-is-doc)
- [Suggested commands](#suggested-commands)

## Purpose

Produce an evidence-based picture of what a codebase actually is: components, data flows, and risks. Never assume — every claim in the output cites a file path. Output goes to `docs/architecture/as-is.md`. This map is the prerequisite for review and evolve modes.

## Step 1: Inventory

Establish the skeleton before tracing anything:

- **Entry points**: HTTP routers, CLI mains, workers, cron definitions, serverless handlers, message listeners.
- **Frameworks + runtime**: web framework, ORM, job runner, language runtime, package manifest (requirements/pyproject, package.json, go.mod, pom...).
- **Declarative infrastructure**: docker-compose, k8s manifests, Terraform, Procfile, CI pipelines — these state the intended topology.
- **Configuration**: env vars consumed (`.env.example`, config modules) — reveals external dependencies (DB URLs, queue endpoints, API keys).
- **Module layout**: top-level directories and their apparent responsibility.

Produce a one-screen inventory table: component / location / technology / role.

## Step 2: Trace request flows

For each entry point from Step 1, follow the call chain: route -> middleware -> handler -> service/domain -> data store or external call. Stop at process boundaries.

Record:
1. The synchronous request path(s) — the 3-5 most important.
2. Asynchronous paths — anything through a queue, scheduler, or background worker.
3. External calls — third-party APIs, payment providers, email/SMS, LLM providers.
4. Real-time channels — websockets, SSE, long-polling.

Note where the chain crosses a network boundary (service-to-service HTTP/queue) vs in-process function calls. In-process = one container; cross-network = separate deployment unit.

## Step 3: Map data stores

For every store (Postgres, MySQL, Mongo, Redis, Elasticsearch, S3-compatible, SQLite files, embedded):

- Who writes it, who reads it (module/class level).
- Schema/source of truth — entities, migrations dir, OR-mapped models.
- Access patterns: the queries/indices that dominate (look for query builders, raw SQL, indexes in migrations).
- Consistency relationships: places where two stores must agree (cache + DB, search index + DB, read model + write model). How is agreement maintained (invalidation, CDC, TTL, prayer)?
- Data volumes if discoverable (retention jobs, partitioning, archival code).

The store map is where architecture debt hides: dual-writes without outbox, caches without invalidation, search indexes rebuilt by hand.

## Step 4: Map infra and delivery

From manifests and CI config: environments, deploy targets (VM, containers, serverless), CI/CD pipeline stages, migration strategy, secrets handling, observability present or absent (metrics, structured logs, traces, alerting rules).

If observability is absent, that is itself a finding — "no one can see this system fail."

## Step 5: Identify risks

Scan for the standard topology risks. Each risk = evidence (file:line) + why it hurts + severity (S1-S3).

| Risk | Signature to look for |
|---|---|
| Single point of failure | Single instance deployments, one DB primary with no replica, one region, one AZ |
| Hidden synchronous coupling | Service A calling B inline on the user's request path |
| Dual-write inconsistency | Writing DB then cache/queue/index as two separate calls |
| Missing idempotency | Handlers that mutate on every delivery; no dedup keys |
| Unbounded queues/workers | Queues with no DLQ; workers without concurrency limits |
| N+1 / fan-out on hot path | Loops issuing queries/calls per item |
| No timeout/retry policy | HTTP clients with default (infinite) timeouts |
| Secret sprawl | Keys in repo, .env committed, secrets in CI logs |
| Missing observability | No metrics/tracing libs, print-based logging |
| Schema migration risk | Manual migration steps, no down-migrations |
| Cache without invalidation | TTL-only caches over mutable data |
| Single-region data + global users | Latency math that doesn't close |

## Step 6: Write the as-is doc

Write `docs/architecture/as-is.md` using the template in `references/output-templates.md`:

1. System summary (3 sentences: what it does, for whom, at what scale if known)
2. C4-style container diagram (Mermaid) — follow the snippet in output-templates.md
3. Component inventory table
4. Request flow walk-throughs (read + write)
5. Data store map
6. Infra + delivery
7. Risk register (table: risk / evidence / severity / first fix)
8. Open questions (things the code can't answer)

## Suggested commands

Adapt per language. Run from repo root.

```
# Entry points
rg -n "@(app|router)\.(get|post|put|delete)|@Controller|@RestController" --type ts
rg -n "APIRouter|@app\.route|include_router|FastAPI|@api_view" --type py
rg -n "func main\(" --type go

# HTTP clients (external calls + coupling)
rg -n "http\.Client|fetch\(|axios|requests\.(get|post)|RestTemplate|WebClient" -l

# Message/queue usage
rg -n "kafka|sqs|sns|rabbitmq|pubsub|bullmq|celery|sidekiq|@RabbitListener" -i -l

# Data stores
rg -n "psql|postgres|mysql|mongo|dynamodb|ioredis|redis|elasticsearch|S3|s3Client" -i -l
ls migrations/ db/migrate/ prisma/ 2>/dev/null

# Scheduled/background work
rg -n "cron|@Scheduled|Celery|sidekiq|worker" -i -l
```

Rules: cite paths, not vibes. If the repo is huge, sample the module tree and the two or three flows that matter most to the request. State what you did NOT read.
