# LLM-era infrastructure: RAG, vector search, model serving, agents

For systems with AI components. Numbers here move fast — treat as 2026-era defaults and verify against current practice.

## Contents
- [LLM serving](#llm-serving)
- [KV cache math](#kv-cache-math)
- [Vector search](#vector-search)
- [RAG pipeline design](#rag-pipeline-design)
- [AI agent architecture](#ai-agent-architecture)
- [GPU scheduling](#gpu-scheduling)
- [Design implications for regular systems](#design-implications-for-regular-systems)

## LLM serving

**The physics**: prefill (processing the prompt) is compute-bound; decode (generating tokens) is memory-bandwidth-bound. This asymmetry drives everything:

- **Batching**: continuous batching (join/leave the batch every decode step, ORCA-style) gives 4-8x throughput over request-level batching. Every serious stack has it.
- **KV cache**: attention state per request; naive preallocation wastes 60-80% of memory. PagedAttention (vLLM) brings waste under ~4% — 2-10x more concurrent requests per GPU.
- **Prefix caching**: shared prompt prefixes (system prompts, few-shot, retrieved context) get their KV reused (RadixAttention/SGLang-style). Route requests with the same prefix to the same node for hit rate.
- **Disaggregation**: prefill and decode on separate pools (DistServe/Mooncake/llm-d pattern) with KV handoff — each side sized for its own physics.
- **Speculative decoding**: small drafter proposes, big model verifies in one pass; provably lossless (rejection sampling). EAGLE-class drafters give 3-6x latency cuts; only pays off while decode is memory-bound — gate it off at high batch.
- Engines: vLLM (default, broad ecosystem), TensorRT-LLM (max tok/s on H100-class, compiled per model), SGLang (prefix-heavy + structured output), llama.cpp (edge).

**Capacity thinking**: throughput = tokens/s/GPU x GPU count x utilization. A single 8xGPU node serves ~10-100k output tok/s aggregate depending on model size and batching. Front it with a **gateway**: token-based rate limiting, semantic caching (cache (model, prompt-hash, params) -> response), routing across model sizes.

## KV cache math

Per token KV bytes ~= 2 (K and V) x layers x kv_heads x head_dim x bytes_per_param.
Example 70B-class (80 layers, 8 KV heads, 128 head dim, FP16): 2 x 80 x 8 x 128 x 2 B = ~320 KiB per token; an 8k-token context holds ~2.6 GB of KV state per request pre-PagedAttention sharing. Consequence: context length x concurrency is the capacity dial; KV offloading (GPU -> CPU -> NVMe) trades latency for concurrency. State the formula and the dial in any LLM capacity estimate.

## Vector search

| Index | Mechanism | Strength | Cost |
|---|---|---|---|
| HNSW | Layered proximity graph | Best recall/latency, ~1-10 ms queries | RAM-heavy; deletes = soft + compaction |
| IVF (+PQ) | Cluster centroids, probe nearest | Disk-friendlier, simpler | Recall drop without careful nprobe |
| DiskANN | Graph on SSD | Billion-scale cheap | Newer, fewer managed options |

- The dial: recall vs latency vs memory. Tune (efSearch / nprobe) per workload; report recall@k with latency, never one without the other.
- **Filtered search**: pre-filter (integrated metadata filtering) beats post-filter (fetch k, then drop non-matching). Hybrid retrieval (BM25 + dense) + cross-encoder re-rank (50-200 ms) is the production default.
- Stores: pgvector (<= ~10M vectors, ACID with your data, no new DB — default for tier <= 2), Qdrant/Weaviate (filtering/hybrid built-in), Milvus (billions, ops burden), Pinecone (managed, lock-in). Eventual-consistent replication is fine — search is approximate anyway.
- Same embedding model at index and query time; embedding model change = full reindex (plan the migration like a schema change).

## RAG pipeline design

- **Ingestion**: parse -> chunk -> embed -> store (+ metadata: source, ACL, timestamp). Chunk ~500-1k tokens, 50-100 overlap, recursive/semantic splitting. Attach ACL at chunk level — leaking access control across chunk boundaries is the classic RAG security bug.
- **Query**: (optional transform: HyDE, decomposition) -> hybrid retrieve -> re-rank top-20 -> top-5 -> generate with grounding instructions + "I don't know" fallback.
- **Evaluation**: golden QA set (>= 100 real questions), RAGAS-style metrics (faithfulness, context recall, answer relevance); watch embedding drift; semantic cache for repeated queries.
- **Failure modes**: stale index vs source (CDC the reindex), retrieval quality decay (eval in CI), duplicate context flooding the window, ACL leaks, cost explosion from cache-less repeated prompts.
- Async everything: ingestion is a pipeline (queue + workers), query path is the only synchronous part.

## AI agent architecture

- **Workflows vs agents**: fixed orchestration (chains, routers, parallelizers, orchestrator-workers, evaluator loops) first; free-form agent loops only where the task is genuinely open-ended. Boring beats autonomous when reliability matters.
- Primitives: tool schemas as the API contract (typed, validated); durable state/checkpointing (agent = state machine over durable execution — Temporal-class); episodic + semantic memory stores; sandboxed tool execution; human-in-the-loop gates for irreversible actions; idempotent side effects; per-step cost/latency budgets.
- **Evaluation**: trajectory evals (did it take sane steps) + outcome evals (did it achieve the goal) — build the harness before shipping autonomy.

## GPU scheduling

- K8s + Kueue/Volcano for training/batch: gang scheduling (all-or-nothing) prevents half-scheduled deadlocks; topology-aware placement for NCCL locality.
- Ray/KubeRay for Pythonic serving/training elasticity. Slurm remains HPC default.
- Training reliability: frequent checkpointing to object storage + elastic restarts; slow-node detection (straggler diagnosis is an ops skill here).

## Design implications for regular systems

- An LLM call is seconds, not ms (numbers.md): request paths go async — queue, stream (SSE), poll status; UX shows progress; timeouts are 30-120 s not 3 s.
- LLM spend is a first-class cost line: token budget per feature, semantic caching, model routing (small for easy, big for hard), batch for offline.
- Non-idempotent + non-cheap: cache generations by (model, prompt-hash, params); retries can double-spend — dedup keys on generation endpoints.
- Observability: log prompts/outputs (sampled, PII-scrubbed), track quality metrics (eval scores) alongside latency — a "healthy" serving stack can still produce garbage.
