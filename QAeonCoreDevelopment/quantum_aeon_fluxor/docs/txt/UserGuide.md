# Quantum Aeon Fluxor — User Guide (v0.2.0)

A concise guide to the QAF architecture, components, and how to run and index your corpus.

## Overview

The Quantum Aeon Fluxor (QAF) is an AI research framework for consciousness, meta-cognition, and emergent insight. It implements:

- Archon (Gemini-based top agent) and a conversation loop
- Syzygy prompt framework and an adapter
- Hermetic Engine persistent memory (episodic + long-term blobs)
- Vector retrieval stack using Qdrant and Gemini embeddings

## Naming conventions

- Import-safe package names use lowercase with underscores; parentheses replaced by double underscores.
- Mythic display names are preserved via `__display_name__` and a myth map.
- Use `display_name()` to render mythic names.

Examples:

- `Syzygy(ConversationalFramework)` → `syzygy__conversational_framework`
- Display name map: [myth_map.json](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/myth_map.json)
- Helper: [display.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/display.py)

## Repository layout

Root: [quantum_aeon_fluxor](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor)

- Archon (Supervisor Agent): [archon__supervisor_agent](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/archon__supervisor_agent)
  - Orchestrator: [archon.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/archon__supervisor_agent/archon.py)
  - State model: [state.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/archon__supervisor_agent/state.py)
- Syzygy (Conversational Framework): [syzygy__conversational_framework](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/syzygy__conversational_framework)
  - Prompt kernels: [qacore_prompt_engine.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/syzygy__conversational_framework/Integration_Prototyping/qacore_prompt_engine.py)
  - Bridge/adapter: [bridge.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/syzygy__conversational_framework/bridge.py)
- Hermetic Engine (Persistent Data): [hermetic_engine__persistent_data](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data)
  - Episodic log: [memory_logger.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/emergent_chironomicon__coherent_vectors/memory_logger.py)
  - Gemini client: [GeminiClient.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/conduits__clients/Gemini/GeminiClient.py)
  - Long-term blobs: [longterm.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/longterm.py)
  - Embeddings: [gemini_embedder.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/embedding/gemini_embedder.py)
  - Qdrant helpers: [qdrant_store.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/retrieval/qdrant_store.py)
  - Folder indexer: [index_folder.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/indexing/index_folder.py)
- Reasoning (Pleroma): [pleroma__reasoning](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/pleroma__reasoning)
  - Base: [BaseStrategy.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/pleroma__reasoning/BaseStrategy.py)
  - Logical flow: [LogicalFlowStrategy.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/pleroma__reasoning/LogicalFlowStrategy.py)
- Entrypoint & integration
  - CLI/main: [main.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/main.py)
  - QAeCore+Gemini demo: [qacore_gemini_integration.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/qacore_gemini_integration.py)

## Dependencies and scripts

- Project config: [pyproject.toml](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/pyproject.toml)
- Managed by `uv`.

Runtime deps:
- `google-generativeai`, `python-dotenv`, `pydantic`, `qdrant-client`

Scripts:
- `qaf-cli` → conversation REPL / Archon
- `qaf-index` → legacy/basic folder indexer (pure deterministic chunk → embed → upsert)
- `qaf-ingest` → enhanced ingestion (profiles, concurrency, retries, auto‑tuning aware)
- `qaf-search` → vector search CLI
- `qaf-metrics` → metrics & tuning summary CLI
- `qaf-calibrate` → embedding batch/worker calibration & tuning file generator

## Environment variables

Core:
- `GOOGLE_API_KEY` (required): Google AI key for Gemini chat + embeddings
- `GEMINI_EMBED_MODEL` (optional): defaults to `gemini-embedding-001` (3072 dims)
- `QDRANT_URL` (required): Qdrant REST endpoint including `:6333` (e.g. `https://...cloud.qdrant.io:6333`)
- `QDRANT_API_KEY` (required): Qdrant Cloud API key

Observability & Metrics:
- `QAECORE_METRICS_DIR` (optional): directory for JSONL metric streams (default: `./metrics`)
- `QAECORE_METRICS_ROTATE_DAILY` (flag): if set, rotate per day: `<stream>-YYYYMMDD.jsonl`

Auto‑Tuning / Calibration:
- `QAECORE_DISABLE_TUNING` (flag): skip applying `.qaf_tuning.json` during ingest (use explicit CLI values)
- `QAECORE_TUNING_DRIFT_THRESHOLD` (float, default `0.10`): relative change in chunk_size/overlap triggering retune suggestion

Optional local `.env` supported (best‑effort load) — do not commit secrets.

## Quick start

### Conversation example

```text
qaf-cli conversation
:collection qaecore_noetic_v1
:retrieval on
:focus Boundaries across time/self/sentience
Could you summarize the prototype inquiries we have explored?
:insight "Boundaries unify temporal resonance, identity continuity, and sentience thresholds"
:session S1
:autoembed on
:embed_last 4 qaecore_conversations_v1
```

### Index and search example

```powershell
qaf-index "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data\Aonic Aura(Raw Data)" --collection qaecore_noetic_v1
qaf-search "noncognitivism heat death meaning" --collection qaecore_noetic_v1 --k 5
```

### Ingest books/papers (pdf/epub/txt/md)

```powershell
# Dry run: list files that would be processed
qaf-ingest "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data\Aonic Aura(Raw Data)\Books" --collection qaecore_library_v1 --dry-run

# Ingest and also write parsed text copies for inspection
qaf-ingest "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data\Aonic Aura(Raw Data)\Books" --collection qaecore_library_v1 --write-parsed

# Aggressive profile with concurrency and larger batches (pre‑tuning override)
qaf-ingest "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data\Aonic Aura(Raw Data)\Books" \
  --collection qaecore_library_v1 --profile aggressive \
  --workers 8 --embed-concurrency 6 --embed-batch-size 48 --upsert-batch-size 1000

# Recreate collection & skip unchanged chunks using local cache manifest
qaf-ingest "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data\Aonic Aura(Raw Data)\Books" --collection qaecore_library_v1 --recreate --profile books
```

1) Set environment (PowerShell example):

```powershell
setx GOOGLE_API_KEY "YOUR_GOOGLE_KEY"
setx QDRANT_URL "https://<cluster-id>.<region>.gcp.cloud.qdrant.io:6333"
setx QDRANT_API_KEY "YOUR_QDRANT_KEY"
```

2) Conversation mode (Archon REPL):

```powershell
qaf-cli conversation
```

3) Index a folder into Qdrant with Gemini embeddings:

```powershell
qaf-index "c:\Users\kayno\QAeCore\QAeonCoreDevelopment\quantum_aeon_fluxor\hermetic_engine__persistent_data" --collection qaecore_longterm_v1
```

## Archon

### REPL commands

- `:retain [on|off]` — toggle long-term memory writes (default off)
- `:retrieval [on|off]` — toggle retrieval (default on)
- `:collection <name>` — set Qdrant collection used for retrieval
- `:collections [list|add <name>|remove <name>|clear]` — manage multi-collection retrieval
- `:k <n>` — set top-k results merged across active collections (default 3)
- `:search <query>` — embed and search the active collection (shows Top 5)
- `:k <n>` — set merged top-k across active collections
- `:context [on|off]` — show/hide the structured context block in prompts
- `:weights [list|set <collection> <weight>|clear]` — adjust per-collection weights (1.0 default)
- `:state` — print full JSON state
- `:focus <topic>` — set focus topic in state; `:focus` with no args shows current
- `:insight <summary>` — register an InsightCandidate and persist state
- `:session <id>` — set thread/session ID for this conversation
- `:autoembed [on|off]` — automatically embed the last turn(s) into conversations collection
- `:embed_last [N] [collection]` — embed the last N turns into the conversations collection (default N=2)

Notes:
- When retrieval is on, each turn prints `[Retrieval] collection=<name> k=3` and embeds the top-3 snippets in the prompt context.
- Responses and user turns are logged to the episodic transcript by default.
- Conversational embeddings go to `qaecore_conversations_v1` by default with metadata: `session`, `role`, `turn_index`, `focus_topic`, and a short `text` snippet.

- State: [archon_state.json](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data) is auto-saved.
  - Fields: `phase`, `focus_topic`, `open_questions`, `working_hypotheses`, `contradictions`, `bias_flags`, `insight_candidates`
- Transcript: episodic logs via `episodic_log_interaction(speaker, text)` in [memory_logger.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/emergent_chironomicon__coherent_vectors/memory_logger.py)
- Long-term blobs: `write_blob(blob, tags, meta)` in [longterm.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/longterm.py)
- Prompting: [bridge.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/syzygy__conversational_framework/bridge.py) + [qacore_prompt_engine.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/syzygy__conversational_framework/Integration_Prototyping/qacore_prompt_engine.py)
- Model: [GeminiClient.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/conduits__clients/Gemini/GeminiClient.py) using `gemini-2.5-pro`

## Vector retrieval

- Embeddings (Gemini): [gemini_embedder.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/embedding/gemini_embedder.py)
  - Model: `gemini-embedding-001` (3072 dimensions)
- Qdrant helpers: [qdrant_store.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/retrieval/qdrant_store.py)
  - `ensure_collection(name, 3072)` (COSINE)
  - `upsert_chunks(vectors, payloads)`
  - `search_by_vector(query_vector, k)`
- Indexer CLI: [index_folder.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/indexing/index_folder.py)
  - Chunking: `max_chars=2500`, `overlap=200` (updated default for improved throughput)
  - Payloads: `path`, `rel_path`, `chunk_index`, `text` (snippet)
  - Stable IDs: deterministic UUIDv5 per chunk (prevents duplicates)
- Ingest CLI: [ingest.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/indexing/ingest.py)
  - `--profile {aggressive,books,conservative}` presets
  - `--workers`, `--embed-concurrency`, `--embed-batch-size`, `--upsert-batch-size`
  - Local cache manifest under `.ingest_cache/<collection>.json` (skip unchanged chunks)
- Search CLI: [search_cli.py](file:///c:/Users/kayno/QAeCore/QAeonCoreDevelopment/quantum_aeon_fluxor/hermetic_engine__persistent_data/retrieval/search_cli.py)
  - `qaf-search "query" --collection <name> --k 5 [--json]`

## Security

- Do not commit secrets/API keys. Use environment variables or a local `.env` (ignored from VCS).
- Redaction markers in the repo indicate sensitive values; never copy them into code.

## Roadmap
Completed (recent):
- Metrics subsystem (JSONL streams: `archon`, `gemini`, `ingest`, `calibrate`)
- Latency & counter events with CLI summary (`qaf-metrics`)
- Embedding ingest batching + concurrency + retry with structured latency
- Auto‑tuning ingestion (applies calibrated `batch_size`/`workers` when defaults used)
- Calibration tool (`qaf-calibrate`) generating `configs/.qaf_tuning.json` (dataset hash + stats + run_id)
- Drift detection & retune recommendation (chunk/overlap relative change)
- Tuning age tracking (age_days) + disable/force flags

Planned / Upcoming:
- Event filtering / grep in metrics CLI
- Archon turn‑level instrumentation (per‑turn retrieval & model timing aggregation)
- Retrieval quality metrics (similarity distribution, token usage stats)
- Reasoning strategy plugin registry
- Schema versioning for state & memory artifacts
- Evaluation harness / golden conversational tests
- Multi‑dimensional tuning sweeps (batch_size × workers grid)
- Advanced percentile reporting (p75/p99) and throughput histograms

## Changelog
2025-08-13 — Initial scaffold: Archon, state, memory, Syzygy bridge, Qdrant indexing, CLI.
2025-08-14 — Metrics foundation (`utils.metrics`), ingestion batching + concurrency, retries, latency events; `qaf-metrics` v1.
2025-08-15 — Calibration (`qaf-calibrate`), tuning recommendation file, auto‑apply tuning on ingest, drift detection, tuning age, `--show-tuning-only` summary flag, daily metrics rotation option.

---

## Observability & Metrics

The framework emits newline‑delimited JSON (JSONL) metric events (pure stdlib, no vendor lock‑in):

Streams:
- `archon` — conversation loop timing (prompt composition, model query, state save) (expanding soon)
- `gemini` — raw model client latencies
- `ingest` — indexing / embedding batches, tuning application, retries
- `calibrate` — embedding benchmark batches and final recommendation

Core event patterns:
- `<phase>:start` / `<phase>:end` with `duration_ms` + `status`
- `embed_batch` latency events (per batch) with `batch_size`
- `tuning_applied`, `tuning_mismatch`, `tuning_retune_recommended` (ingest)
- `recommendation` (calibration output)

View summaries:
```powershell
qaf-metrics                       # default summary (archon, gemini, ingest)
qaf-metrics --streams ingest --last 40
qaf-metrics --streams calibrate --raw --last 5   # raw JSON lines
qaf-metrics --show-tuning-only    # print only current tuning recommendation
```

Daily rotation (opt‑in) produces files like `ingest-20250815.jsonl` when `QAECORE_METRICS_ROTATE_DAILY` is set.

## Calibration & Auto‑Tuning Workflow

1. Run calibration on a representative folder (does NOT write to Qdrant):
```powershell
qaf-calibrate "path\to\raw_corpus" --sample 200 --batch-sizes 4 8 16 32 --workers 4 --progress
```
2. Inspect recommendation (saved to `configs/.qaf_tuning.json`):
```powershell
qaf-metrics --show-tuning-only
```
3. Ingest normally (leave defaults `--embed-batch-size 16 --workers 4`) and the tuned values auto‑apply if dataset hash and chunk params match. Override explicitly to bypass.
4. If you intentionally change `chunk_size` or `overlap` beyond `QAECORE_TUNING_DRIFT_THRESHOLD`, ingest emits a `tuning_retune_recommended` event.
5. Force re‑calibration ignoring existing tuning file:
```powershell
qaf-calibrate path\to\raw_corpus --force-retune
```

Tuning file fields:
```json
{
  "batch_size": 32,
  "workers": 4,
  "throughput_chunks_per_s": 185.4,
  "mean_batch_ms": 172.1,
  "stddev_batch_ms": 9.3,
  "sample": 200,
  "generated_at": "2025-08-15T10:42:11Z",
  "strategy": "throughput_then_stability",
  "chunk_size": 2500,
  "overlap": 200,
  "dataset_hash": "<sha1>",
  "run_id": "abc123def456"
}
```

Disable auto‑tuning entirely:
```powershell
$env:QAECORE_DISABLE_TUNING=1
qaf-ingest path --collection my_coll
```

Adjust drift sensitivity (e.g. 5%):
```powershell
$env:QAECORE_TUNING_DRIFT_THRESHOLD=0.05
```

## Ingestion Enhancements Overview

Features now included in `qaf-ingest` / indexer path:
- Deterministic chunk UUIDv5 (idempotent upserts; no duplicates on re‑run)
- Batch embedding with concurrency; per‑batch latency metrics
- Exponential retries for embedding failures (events: `embed:error`)
- Throughput & summary event (`ingest_summary`) (planned extension)
- Auto‑application of calibrated `batch_size` and `workers` when user leaves defaults
- Drift detection for chunk size / overlap changes with retune suggestion
- Age tracking of tuning recommendation (age_days) for maintenance scheduling

---
