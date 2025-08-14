# Quantum Aeon Fluxor — User Guide (v0.1.0)

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
- `qaf-cli` → `quantum_aeon_fluxor.main:main`
- `qaf-index` → `quantum_aeon_fluxor.hermetic_engine__persistent_data.indexing.index_folder:index_folder`

## Environment variables

- `GOOGLE_API_KEY` (required): Google AI key for Gemini chat + embeddings
- `GEMINI_EMBED_MODEL` (optional): defaults to `gemini-embedding-001` (3072 dims)
- `QDRANT_URL` (required): Qdrant REST endpoint including `:6333` (e.g. `https://...cloud.qdrant.io:6333`)
- `QDRANT_API_KEY` (required): Qdrant Cloud API key

## Quick start

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
  - Chunking: `max_chars=2000`, `overlap=200`
  - Payloads: `path`, `rel_path`, `chunk_index`

## Security

- Do not commit secrets/API keys. Use environment variables or a local `.env` (ignored from VCS).
- Redaction markers in the repo indicate sensitive values; never copy them into code.

## Roadmap

- Conversation commands (`:retain`, `:state`, `:search`)
- Qdrant search CLI and Archon retrieval hook
- Adversarial agent harness
- MCP integration for persistent docs server

## Changelog

- 2025-08-13 — Initial scaffold: Archon, state, memory, Syzygy bridge, Qdrant indexing, CLI.
