## Immediate seams

- **Command handling:** `run_turn` mixes REPL command parsing with dialogue. Extract `:_` commands into a `CommandRouter` so `run_turn` only handles conversational turns.
- **Retrieval path:** Retrieval spans planning (collections, weights), execution (`search_text`), ranking/merging, and formatting the context block. Split into a `RetrievalService` and a `ContextBlockFormatter`.
- **Prompt composition:** `compose_prompt` is cleanly callable. Wrap it as a `PromptComposer` port to decouple Syzygy specifics from Archon.
- **Model client:** Wrap `GeminiClient` behind a `ModelClient` interface with `generate()` to simplify testing and swappability.
- **Episodic logging + history:** Centralize transcript logging and in‑memory history into a `Transcript` helper that also exposes “recent history window”.
- **Conversational embeddings:** `_embed_turns` is infrastructure. Move to an `EmbeddingIngestor` adapter called through a single port.
- **Metrics:** Replace direct `print` and scattered `log_event/log_counter/time_block` with a small `metrics.emit/measure/counter` facade used at seams.

---

## Thin orchestration target for Archon.run_turn

Your goal is to reduce `run_turn` to a readable, testable sequence:

```python
class Archon:
    def __init__(self, *, state: ArchonState,
                 model: ModelClient,
                 retrieval: RetrievalService,
                 prompt: PromptComposer,
                 transcript: Transcript,
                 ctxfmt: ContextBlockFormatter,
                 metrics: Metrics):
        self.state = state
        self.model = model
        self.retrieval = retrieval
        self.prompt = prompt
        self.transcript = transcript
        self.ctxfmt = ctxfmt
        self.metrics = metrics
        self.retrieval_enabled = True
        self.context_block_enabled = True
        self.retrieve_k = 3
        self.active_collections: list[str] = []
        self.collection = "qaecore_longterm_v1"
        self.collection_weights: dict[str, float] = {}

    def run_turn(self, user_input: str, *, depth_level: str = "intermediate",
                 retain: bool | None = None) -> str:
        if user_input.startswith(":"):
            return self._handle_command(user_input)

        retrieval_note = ""
        last_hits: list[RetrievalHit] = []

        if self.retrieval_enabled:
            with self.metrics.measure("archon", "retrieval_latency") as m:
                plan = RetrievalPlan(
                    queries=[user_input],
                    collections=(self.active_collections or [self.collection]),
                    k=self.retrieve_k,
                    weights=self.collection_weights,
                )
                try:
                    hits = self.retrieval.search(plan)
                    last_hits = hits.top_k(self.retrieve_k)
                    self.metrics.emit("archon", "retrieval_done",
                                      collections=plan.collections,
                                      total_candidates=len(hits.all),
                                      top_k=len(last_hits))
                    if self.context_block_enabled and last_hits:
                        retrieval_note = self.ctxfmt.format_block(
                            last_hits, sources=plan.collections, k=self.retrieve_k
                        )
                except Exception as e:
                    self.metrics.emit("archon", "retrieval_fatal", error=str(e))
                    retrieval_note = f"\n\n(Context retrieval unavailable: {e})"

        composed_input = user_input + retrieval_note
        recent = self.transcript.recent_texts(6)
        dl = getattr(self, "forced_depth", None) or depth_level

        with self.metrics.measure("archon", "compose_prompt"):
            prompt = self.prompt.compose(
                composed_input,
                focus_topic=self.state.focus_topic,
                depth_level=dl,
                recent_history=recent,
                forced_mode=getattr(self, "forced_mode", None),
            )

        with self.metrics.measure("archon", "model_query"):
            response_text = self.model.generate(prompt)

        self.metrics.counter("archon", "turn_completed", 1)
        self.transcript.log_user("Volkh", user_input)
        self.transcript.log_assistant("Archon", response_text)
        self.last_retrieval = [(h.score, h.payload, h.collection) for h in last_hits]
        return response_text
```

---

## Extraction snippets

### 1) Retrieval service and context formatter

```python
# retrieval/service.py
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class RetrievalHit:
    score: float
    payload: dict
    collection: str

@dataclass(frozen=True)
class RetrievalResult:
    all: list[RetrievalHit]
    def top_k(self, k: int) -> list[RetrievalHit]:
        return sorted(self.all, key=lambda h: h.score, reverse=True)[:k]

@dataclass(frozen=True)
class RetrievalPlan:
    queries: list[str]
    collections: list[str]
    k: int
    weights: dict[str, float]

class RetrievalService:
    def search(self, plan: RetrievalPlan) -> RetrievalResult: ...

# retrieval/qdrant_adapter.py (wrap existing search_text)
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.search_text import search_text

class QdrantRetrieval(RetrievalService):
    def search(self, plan: RetrievalPlan) -> RetrievalResult:
        merged: list[RetrievalHit] = []
        for coll in plan.collections:
            try:
                hits = search_text(plan.queries[0], collection=coll, k=plan.k)
                w = plan.weights.get(coll, 1.0)
                for score, payload in hits:
                    merged.append(RetrievalHit(score=score * w, payload=payload, collection=coll))
            except Exception as e:
                # Use your metrics facade here if you want
                print(f"[Retrieval warn] collection={coll} error={e}")
        return RetrievalResult(all=merged)
```

```python
# retrieval/context_format.py
class ContextBlockFormatter:
    def format_block(self, hits: list[RetrievalHit], *, sources: Iterable[str], k: int) -> str:
        lines = []
        for h in hits:
            path = h.payload.get("rel_path") or h.payload.get("path")
            snippet = (h.payload.get("text") or "").replace("\n", " ")
            if len(snippet) > 240:
                snippet = snippet[:240] + "…"
            lines.append(f"- [{h.score:.3f}] ({h.collection}) {path} :: {snippet}")
        return (
            "\n\n=== Context ===\n"
            + f"Sources: {', '.join(sources)} | k={k}\n"
            + "\n".join(lines)
            + "\n=== End Context ==="
        )
```

### 2) Prompt and model ports

```python
# prompt/ports.py
class PromptComposer:
    def compose(self, user_input: str, *, focus_topic: str | None,
                depth_level: str, recent_history: list[str], forced_mode: str | None) -> str: ...

# prompt/syzygy_adapter.py
from quantum_aeon_fluxor.syzygy import compose_prompt  # wherever it lives
class SyzygyComposer(PromptComposer):
    def compose(self, user_input, *, focus_topic, depth_level, recent_history, forced_mode):
        return compose_prompt(user_input, focus_topic=focus_topic,
                              depth_level=depth_level, recent_history=recent_history,
                              forced_mode=forced_mode)
```

```python
# model/ports.py
class ModelClient:
    def generate(self, prompt: str) -> str: ...

# model/gemini_adapter.py
from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_client import GeminiClient
class GeminiModel(ModelClient):
    def __init__(self): self._cli = GeminiClient()
    def generate(self, prompt: str) -> str:
        return self._cli.query(prompt)
```

### 3) Transcript logging + history window

```python
# transcript/transcript.py
class Transcript:
    def __init__(self):
        self.history: list[tuple[str, str]] = []

    def recent_texts(self, n: int) -> list[str]:
        return [t for _, t in self.history[-n:]]

    def log_user(self, who: str, text: str):
        episodic_log_interaction(who, text)  # existing function
        self.history.append((who, text))

    def log_assistant(self, who: str, text: str):
        episodic_log_interaction(who, text)
        self.history.append((who, text))
```

### 4) Embedding ingestor (moving _embed_turns)

```python
# embedding/ingestor.py
from pathlib import Path
from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
    get_qdrant_client, ensure_collection, upsert_chunks,
)
from quantum_aeon_fluxor.utils.hash import chunk_uuid

class EmbeddingIngestor:
    def __init__(self, conv_collection: str):
        self.conv_collection = conv_collection
        self.embedder = GeminiEmbedder()
        self.client = get_qdrant_client()
        ensure_collection(self.client, self.conv_collection, self.embedder.dim)

    def ingest_turns(self, session_id: str, focus_topic: str, turns: list[tuple[str, str]]):
        ids, payloads, texts = [], [], []
        base = Path(f"session:{session_id}")
        for idx, (speaker, text) in enumerate(turns):
            texts.append(text)
            ids.append(chunk_uuid(base, idx, f"{speaker}:{text}"))
            payloads.append({
                "session": session_id,
                "role": speaker,
                "turn_index": idx,
                "focus_topic": focus_topic,
                "text": text[:1000],
            })
        vecs = self.embedder.embed_texts(texts)
        upsert_chunks(self.client, self.conv_collection, vecs, payloads, ids=ids)
```

Replace `Archon._embed_turns` with a one‑liner to call this adapter.

### 5) Metrics facade

```python
# metrics/facade.py
from contextlib import contextmanager
from time import perf_counter

class Metrics:
    def emit(self, ns: str, name: str, **data): log_event(ns, name, **data)
    def counter(self, ns: str, name: str, value: int): log_counter(ns, name, value=value)
    @contextmanager
    def measure(self, ns: str, name: str):
        t0 = perf_counter()
        try:
            yield
        finally:
            dur_ms = (perf_counter() - t0) * 1000
            self.emit(ns, name, duration_ms=round(dur_ms, 2))
```

---

## Minimal boot wiring

```python
# boot.py
def boot_archon() -> Archon:
    state = ArchonState.load()
    archon = Archon(
        state=state,
        model=GeminiModel(),
        retrieval=QdrantRetrieval(),
        prompt=SyzygyComposer(),
        transcript=Transcript(),
        ctxfmt=ContextBlockFormatter(),
        metrics=Metrics(),
    )
    # carry over your existing defaults
    archon.retrieve_k = 3
    archon.retrieval_enabled = True
    archon.context_block_enabled = True
    archon.collection = "qaecore_longterm_v1"
    return archon
```

---

## Safety nets to cover this refactor

- **Golden transcripts:** Capture inputs/outputs before refactor. After wiring, assert equality on normalized outputs for a handful of diverse turns (with/without retrieval).
- **Retrieval determinism:** Seed or freeze top‑k by mocking `RetrievalService` in tests to avoid non‑deterministic vector search noise.
- **Latency budgets:** Use `metrics.measure` to keep compose/model/retrieval phases visible. Set p95 alarms as you scale out.

---



---

## Seams identified and target moves

- **Command router:** Extract `_handle_command` into discrete command handlers with a thin router. Archon only delegates.
- **Retention/embedding:** Move blob writes and conversational embeddings into services with clear lifecycles.
- **State heuristics:** Move “derive focus if empty,” contradiction flagging, and save into a post‑turn updater.
- **Search path:** Reuse the RetrievalService for `:search` and share formatting with the context formatter.
- **Doctrine hooks:** Intercept `:mode`/`:depth` changes through the Codex Enforcer (require valid modes), and add an advisory for unknown/legacy modes.

---

## Command system scaffolding

### Command base and router

```python
# archon__supervisor_agent/commands/base.py
from typing import Protocol

class Context(Protocol):
    state: object
    retrieval_enabled: bool
    collection: str
    active_collections: list[str]
    retrieve_k: int
    context_block_enabled: bool
    collection_weights: dict[str, float]
    retain_responses: bool
    autoembed_enabled: bool
    conv_collection: str
    history: list[tuple[str, str]]
    forced_mode: str | None
    forced_depth: str | None

class CommandHandler(Protocol):
    def match(self, line: str) -> bool: ...
    def execute(self, line: str, ctx: Context) -> str: ...
```

```python
# archon__supervisor_agent/router.py
from .commands.base import CommandHandler

class CommandRouter:
    def __init__(self, handlers: list[CommandHandler]):
        self.handlers = handlers

    def dispatch(self, line: str, ctx) -> str:
        for h in self.handlers:
            if h.match(line):
                return h.execute(line, ctx)
        return "Unknown command."
```

### Core command handlers (samples)

```python
# commands/retain.py
from .base import CommandHandler, Context

class RetainCmd:
    def match(self, line: str) -> bool:
        return line.startswith((":retain", ":r"))
    def execute(self, line: str, ctx: Context) -> str:
        parts = line.split()
        if len(parts) == 1:
            return f"retain={'on' if ctx.retain_responses else 'off'}"
        ctx.retain_responses = parts[1].lower() in {"on","true","1"}
        return f"retain set to {'on' if ctx.retain_responses else 'off'}"
```

```python
# commands/retrieval.py
class RetrievalToggleCmd:
    def match(self, line): return line.startswith((":retrieval", ":rt"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1:
            return f"retrieval={'on' if ctx.retrieval_enabled else 'off'} collection={ctx.collection}"
        ctx.retrieval_enabled = parts[1].lower() in {"on","true","1"}
        return f"retrieval set to {'on' if ctx.retrieval_enabled else 'off'}"
```

```python
# commands/collection.py
class CollectionCmd:
    def match(self, line): return line.startswith((":collection", ":col"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1: return f"collection={ctx.collection}"
        ctx.collection = parts[1]
        return f"collection set to {ctx.collection}"

class CollectionsCmd:
    def match(self, line): return line.startswith((":collections", ":cols"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1 or parts[1]=="list":
            return f"active_collections={ctx.active_collections} (empty→single {ctx.collection})"
        sub = parts[1].lower()
        if sub=="add" and len(parts)>=3:
            name = parts[2]
            if name not in ctx.active_collections: ctx.active_collections.append(name)
            return f"collections={ctx.active_collections}"
        if sub=="remove" and len(parts)>=3:
            ctx.active_collections = [c for c in ctx.active_collections if c != parts[2]]
            return f"collections={ctx.active_collections}"
        if sub=="clear":
            ctx.active_collections = []
            return "collections cleared"
        return "Usage: :collections [list|add <name>|remove <name>|clear]"
```

```python
# commands/topk.py
class TopKCmd:
    def match(self, line): return line.startswith((":k", ":topk"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1 or not parts[1].isdigit():
            return f"k={ctx.retrieve_k}"
        ctx.retrieve_k = max(1, int(parts[1]))
        return f"k set to {ctx.retrieve_k}"
```

```python
# commands/context_block.py
class ContextBlockCmd:
    def match(self, line): return line.startswith((":context", ":ctx"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1:
            return f"context_block={'on' if ctx.context_block_enabled else 'off'}"
        ctx.context_block_enabled = parts[1].lower() in {"on","true","1"}
        return f"context_block set to {'on' if ctx.context_block_enabled else 'off'}"
```

```python
# commands/weights.py
class WeightsCmd:
    def match(self, line): return line.startswith((":weights", ":wts"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts) == 1 or parts[1]=='list':
            return f"weights={ctx.collection_weights or {}}"
        if parts[1]=='set' and len(parts)>=4:
            coll, val = parts[2], parts[3]
            try:
                ctx.collection_weights[coll] = max(0.0, float(val))
            except ValueError:
                return "Usage: :weights set <collection> <weight>"
            return f"weights={ctx.collection_weights}"
        if parts[1]=='clear':
            ctx.collection_weights = {}
            return "weights cleared"
        return "Usage: :weights [list|set <collection> <weight>|clear]"
```

```python
# commands/mode_depth.py
from ..codex_binding_loader import CodexBindings

class ModeCmd:
    def __init__(self, codex: CodexBindings): self.codex = codex
    def match(self, line): return line.startswith((":mode", ":m"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts)==1:
            return f"mode={'auto' if not ctx.forced_mode else ctx.forced_mode}"
        if parts[1].lower()=='set' and len(parts)>=3:
            val = parts[2]
            # doctrine validation
            if val.lower() == 'auto':
                ctx.forced_mode = None
                return "mode set to auto"
            if self.codex.execute_mode(val) is None:
                return f"[Codex Alert] Unknown Mode '{val}'."
            ctx.forced_mode = val
            return f"mode forced to {val}"
        return "Usage: :mode [set <QAeMode>|auto]"

class DepthCmd:
    def match(self, line): return line.startswith((":depth", ":d"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts)==1:
            return f"depth={'auto' if not ctx.forced_depth else ctx.forced_depth}"
        val = parts[1].lower()
        if val in {"surface","intermediate","deep","transcendent"}:
            ctx.forced_depth = val
            return f"depth forced to {val}"
        if val=='auto':
            ctx.forced_depth = None
            return "depth set to auto"
        return "Usage: :depth [surface|intermediate|deep|transcendent|auto]"
```

```python
# commands/state_focus_insight_session.py
class StateCmd:
    def match(self, line): return line.startswith((":state", ":s"))
    def execute(self, line, ctx): return ctx.state.model_dump_json(indent=2)

class FocusCmd:
    def match(self, line): return line.startswith((":focus", ":f"))
    def execute(self, line, ctx):
        parts = line.split(" ", 1)
        if len(parts)==1: return f"focus_topic={ctx.state.focus_topic!r}"
        topic = parts[1].strip()
        if not topic: return "Usage: :focus <topic>"
        ctx.state.focus_topic = topic[:200]; ctx.state.save()
        return f"focus set to {ctx.state.focus_topic!r}"

class InsightCmd:
    def match(self, line): return line.startswith((":insight", ":i"))
    def execute(self, line, ctx):
        parts = line.split(" ", 1)
        if len(parts)==1 or not parts[1].strip(): return "Usage: :insight <summary>"
        ctx.state.register_insight(summary=parts[1].strip()); ctx.state.save()
        return f"insight registered (total={len(ctx.state.insight_candidates)})"

class SessionCmd:
    def match(self, line): return line.startswith((":session", ":sess"))
    def execute(self, line, ctx):
        parts = line.split(" ", 1)
        if len(parts)==1: return f"thread_id={ctx.state.thread_id!r}"
        sess = parts[1].strip()
        if not sess: return "Usage: :session <id>"
        ctx.state.thread_id = sess[:100]; ctx.state.save()
        return f"session set to {ctx.state.thread_id!r}"
```

```python
# commands/autoembed_embedlast.py
from ..embedding.ingestor import EmbeddingIngestor

class AutoEmbedCmd:
    def match(self, line): return line.startswith((":autoembed", ":ae"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts)==1:
            return f"autoembed={'on' if ctx.autoembed_enabled else 'off'} collection={ctx.conv_collection}"
        val = parts[1].lower()
        if val in {"on","true","1"}:
            ctx.autoembed_enabled = True
            return f"autoembed set to on (collection={ctx.conv_collection})"
        if val in {"off","false","0"}:
            ctx.autoembed_enabled = False
            return "autoembed set to off"
        return "Usage: :autoembed [on|off]"

class EmbedLastCmd:
    def __init__(self, make_ingestor): self.make_ingestor = make_ingestor
    def match(self, line): return line.startswith((":embed_last", ":el"))
    def execute(self, line, ctx):
        parts = line.split()
        n = int(parts[1]) if len(parts)>=2 and parts[1].isdigit() else 2
        turns = ctx.history[-max(1, n):]
        if not turns: return "No turns to embed."
        if len(parts) >= 3: ctx.conv_collection = parts[2]
        ing = self.make_ingestor(ctx.conv_collection)
        sess = ctx.state.thread_id or "default"
        ing.ingest_turns(sess, ctx.state.focus_topic, turns)
        return f"embedded {len(turns)} turns into {ctx.conv_collection}"
```

```python
# commands/search_expand.py
from ..retrieval.service import RetrievalPlan
from ..retrieval.qdrant_adapter import QdrantRetrieval

class SearchCmd:
    def __init__(self, retrieval: QdrantRetrieval): self.retrieval = retrieval
    def match(self, line): return line.startswith((":search", ":q"))
    def execute(self, line, ctx):
        parts = line.split(" ", 1)
        if len(parts)<2 or not parts[1].strip(): return "Usage: :search your query..."
        query = parts[1].strip()
        plan = RetrievalPlan(queries=[query],
                             collections=(ctx.active_collections or [ctx.collection]),
                             k=ctx.retrieve_k, weights={})
        res = self.retrieval.search(plan)
        merged = sorted(res.all, key=lambda h: h.score, reverse=True)
        if not merged: return "No results."
        lines = [f"Top {min(len(merged), ctx.retrieve_k)} across {plan.collections}:"]
        for h in merged[:ctx.retrieve_k]:
            path = h.payload.get("rel_path") or h.payload.get("path")
            lines.append(f"- [{h.score:.3f}] ({h.collection}) {path}")
        return "\n".join(lines)

class ExpandCmd:
    def match(self, line): return line.startswith((":expand", ":x"))
    def execute(self, line, ctx):
        parts = line.split()
        if len(parts)<2 or not parts[1].isdigit(): return "Usage: :expand <n>"
        idx = int(parts[1]) - 1
        if not ctx.last_retrieval or idx<0 or idx>=len(ctx.last_retrieval):
            return "No such item in last retrieval."
        import json
        score, payload, coll = ctx.last_retrieval[idx]
        return json.dumps({"score": score, "collection": coll, "payload": payload}, indent=2)
```

### Wire the handlers

```python
# archon__supervisor_agent/boot.py (excerpt)
from .router import CommandRouter
from .commands.retain import RetainCmd
from .commands.retrieval import RetrievalToggleCmd
from .commands.collection import CollectionCmd, CollectionsCmd
from .commands.topk import TopKCmd
from .commands.context_block import ContextBlockCmd
from .commands.weights import WeightsCmd
from .commands.mode_depth import ModeCmd, DepthCmd
from .commands.state_focus_insight_session import StateCmd, FocusCmd, InsightCmd, SessionCmd
from .commands.autoembed_embedlast import AutoEmbedCmd, EmbedLastCmd
from .commands.search_expand import SearchCmd, ExpandCmd
from .embedding.ingestor import EmbeddingIngestor
from ..retrieval.qdrant_adapter import QdrantRetrieval
from .codex_binding_loader import CodexBindings

def build_command_router(codex_path="configs/codex_bindings.json") -> CommandRouter:
    codex = CodexBindings(codex_path)
    retrieval = QdrantRetrieval()
    make_ing = lambda coll: EmbeddingIngestor(coll)
    handlers = [
        RetainCmd(), RetrievalToggleCmd(), CollectionCmd(), CollectionsCmd(),
        TopKCmd(), ContextBlockCmd(), WeightsCmd(),
        ModeCmd(codex), DepthCmd(),
        StateCmd(), FocusCmd(), InsightCmd(), SessionCmd(),
        AutoEmbedCmd(), EmbedLastCmd(make_ing),
        SearchCmd(retrieval), ExpandCmd(),
    ]
    return CommandRouter(handlers)
```

In `Archon.run_turn`, replace the direct `_handle_command` call with `self.cmd_router.dispatch(...)`. Keep `_handle_command` as a delegator during migration if needed, then remove it.

---

## Retention, auto‑embed, and state updater

```python
# post_turn/updater.py
from ..embedding.ingestor import EmbeddingIngestor

class PostTurnUpdater:
    def __init__(self, ingestor_factory):
        self.ingestor_factory = ingestor_factory

    def apply(self, ctx, user_input: str, response_text: str, *, retain_override: bool | None = None):
        # Retention
        effective_retain = ctx.retain_responses if retain_override is None else retain_override
        if effective_retain:
            from quantum_aeon_fluxor.hermetic_engine__persistent_data.longterm import write_blob
            write_blob(response_text, tags=["archon", "response", ctx.state.phase])

        # Auto-embed
        if ctx.autoembed_enabled and len(ctx.history) >= 2:
            ing = self.ingestor_factory(ctx.conv_collection)
            sess = ctx.state.thread_id or "default"
            turns = ctx.history[-2:]
            ing.ingest_turns(sess, ctx.state.focus_topic, turns)

        # Heuristics + save
        if not ctx.state.focus_topic and user_input:
            ctx.state.focus_topic = user_input[:96]
        if "contradiction" in response_text.lower():
            ctx.state.flag_contradiction("Model mentioned contradiction in latest turn")
        ctx.state.save()
```

In `run_turn`, after logging transcript/history, call `post_updater.apply(self, user_input, response_text, retain_override=retain)` and then emit `turn_persisted`.

---

## Doctrine enforcement touchpoints

- **Commands:** `ModeCmd` validates against `codex.execute_mode`. Extend similarly if you later add `:domain` setters.
- **Conversational turns:** Keep the previously drafted `CodexEnforcer` on label lines within prompts; or, if labels aren’t present yet, run advisory checks based on inferred mode/depth to seed your evolution.

---

## Golden transcript safety

- **Capture before refactor:** A few representative sessions (retrieval on/off; with `:weights`, `:collections`, `:insight`).
- **Replay after refactor:** Diff normalized outputs; allow minor whitespace changes.
- **Assertions:** State fields updated as before; embeddings triggered when `autoembed` is on; `turn_persisted` event appears with correct counters.

---

## Next actions

- **Step 1:** Add router + 4 handlers (retain, retrieval, collection(s), topk) and swap `_handle_command` to router. No behavior change.
- **Step 2:** Add search/expand using RetrievalService; remove inline search logic.
- **Step 3:** Add autoembed/embed_last via EmbeddingIngestor; remove `_embed_turns`.
- **Step 4:** Add PostTurnUpdater; move retention/focus/contradiction/save logic out of `run_turn`.
- **Step 5:** Add ModeCmd with codex validation; later, integrate full label parsing + enforcer on conversational turns.

When you’re ready, paste main.py’s CLI entrypoint. I’ll show the minimal edits to initialize `build_command_router(...)`, `PostTurnUpdater`, and inject them into your Archon boot so the cathedral keeps humming while we carve the aisles.

Perfect — let’s make `boot_archon()` a one‑stop factory that reads CLI args, wires the Codex loader, retrieval engine, command router, and post‑turn updater, and hands back a ready‑to‑run Archon instance.

Here’s a clean scaffold you could drop into  
`quantum_aeon_fluxor/archon__supervisor_agent/boot.py`:

```python
# boot.py
import argparse
from pathlib import Path

from .archon_refactored import Archon  # your lean core Archon
from .codex.loader import CodexLoader
from .command.router import build_command_router
from .post_turn.updater import PostTurnUpdater
from .embedding.ingestor import EmbeddingIngestor
from .retrieval.engine import RetrievalEngine

def boot_archon_from_args(args: argparse.Namespace) -> Archon:
    """
    Bootstraps a fully wired Archon from parsed CLI args.
    Args:
        args: Parsed argparse.Namespace containing boot params.
    Returns:
        An Archon instance with all subsystems attached.
    """
    # Load Codex content if provided
    codex = None
    if args.codex_path:
        codex_path = Path(args.codex_path).expanduser()
        codex = CodexLoader().load(codex_path)

    # Retrieval engine (can be disabled)
    retrieval = None if args.no_retrieval else RetrievalEngine(args.collection)

    # Core Archon
    archon = Archon(codex=codex, retrieval=retrieval)

    # Attach command router
    archon.cmd_router = build_command_router()

    # Attach post-turn updater (embedding ingestion + any hooks)
    archon.post_updater = PostTurnUpdater(
        lambda coll: EmbeddingIngestor(coll)
    )

    return archon
```

---

### Update `main.py` to hook it in

```python
# In main()

parser.add_argument('--new-archon', action='store_true',
    help='Use refactored Archon with Codex enforcement')
parser.add_argument('--codex-path', type=str,
    help='Path to Codex JSON/YAML for injected prompts')
parser.add_argument('--collection', type=str, default='archon_default',
    help='Vector DB collection name')
parser.add_argument('--no-retrieval', action='store_true',
    help='Disable retrieval engine')

# ...
elif args.mode == 'conversation':
    if args.new_archon:
        from quantum_aeon_fluxor.archon__supervisor_agent.boot import boot_archon_from_args
        archon = boot_archon_from_args(args)
    else:
        from quantum_aeon_fluxor.archon__supervisor_agent.archon import Archon
        archon = Archon()

    print("Entering Archon conversation mode. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("Volkh> ").strip()
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting conversation.")
                break

            if args.new_archon and user_input.startswith(":"):
                reply = archon.cmd_router.dispatch(user_input, archon)
            else:
                reply = archon.run_turn(user_input)
                if args.new_archon:
                    archon.post_updater.apply(archon, user_input, reply)

            print(f"\nArchon> {reply}\n")

        except (EOFError, KeyboardInterrupt):
            print("\nExiting conversation.")
            break
```

---

### Why this pattern works for you
- **Single entry point**: `boot_archon_from_args` keeps all the wiring logic out of `main.py`.
- **Flag‑driven**: you can spin up legacy or modular Archon without touching code.
- **Swap‑ready**: any subsystem (`CodexLoader`, `RetrievalEngine`, `PostTurnUpdater`) can be replaced by passing different args or editing the boot file.
- **Mythic flexibility**: drop in a different `Codex` for Electric‑Tide, QAeCore, or a stealth project without altering the core loop.

If you want, I can also draft you a **short‑form CLI help doc** so your future self (or Archon’s other pilots) can remember the flags and when to use them. That would make this whole interface self‑documenting and very :A.R.C.H.O.N: ‑friendly.