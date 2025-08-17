---

## Decomposition strategy

- **Strangler pattern:** Keep archon.py as Archon-Legacy; stand up a thin façade that routes to new modules. Migrate feature-by-feature behind identical CLI.
- **Ports and adapters:** Separate domain logic (conversation, state, doctrine) from infrastructure (Gemini client, Qdrant, files). Define interfaces, plug adapters later.
- **Command pipeline:** Model each REPL command as a command object/handler. The loop stays dumb; handlers do the work.
- **Event spine:** Emit structured events (TurnStarted, RetrievalCompleted, ModelResponded, StatePersisted) so you can observe and test seams.
- **Characterization tests:** Lock current behavior with golden transcripts before refactor. Compare normalized outputs/metrics to guard regressions.

---

## Target module map (incremental)

```
quantum_aeon_fluxor/
  archon__supervisor_agent/
    archon_legacy.py              # frozen, only delegations remain
    archon_api.py                 # façade used by CLI
    boot.py                       # loads codex, wiring, flags
    repl.py                       # minimal loop, no business logic
    router.py                     # label+command routing
    state.py                      # (extract/retain) state model
    codex_binding_loader.py       # already drafted
    codex_enforcer.py             # already drafted
    commands/
      base.py
      focus.py
      insight.py
      retrieval.py
      collections.py
      embed_last.py
      toggle_flags.py
    modes/
      executor.py                 # Mode dispatch surface
    domains/
      registry.py                 # Domain routing to modules
    persistence/
      memory_port.py              # ports: episodic, blobs, vectors
      hermetic_adapter.py         # adapters to Hermetic Engine
      qdrant_adapter.py           # adapters to Qdrant helpers
    reasoning/
      registry.py                 # pleroma strategy plug-ins
    metrics/
      events.py                   # event dataclasses, emit()
      sinks.py                    # JSONL writer (ties to your metrics)
```

Keep the mythic names at the package level; use clear, import‑safe internals.

---

## Migration steps (10 focused passes)

1. **Freeze and façade**
   - Rename current to archon_legacy.py.
   - Create archon_api.py with the minimal public surface used by main.py/qaf-cli (start(), handle_turn(), shutdown()).
   - archon_api delegates to legacy for now.

2. **Extract state and config**
   - Move all state classes into state.py (or confirm they’re there).
   - Centralize env/config reads into boot.py; pass config objects, not globals.

3. **Split REPL loop**
   - Create repl.py with a tight loop:
     - read → parse labels/command → enforcer.validate → router.dispatch → persist → emit events.
   - Keep zero logic in the loop.

4. **Command handlers**
   - Create commands/base.py with an interface:
     ```python
     class CommandHandler(Protocol):
         def match(self, line: str) -> bool: ...
         def execute(self, line: str, ctx: Context) -> str: ...
     ```
   - Move each of: :focus, :insight, :retrieval, :collections, :k, :search, :state, :autoembed, :embed_last into its file. Delegate any persistence to adapters.

5. **Persistence ports/adapters**
   - Define ports in persistence/memory_port.py:
     ```python
     class EpisodicPort(Protocol):
         def log_interaction(self, speaker, text): ...
     class BlobPort(Protocol):
         def write_blob(self, blob, tags, meta): ...
     class VectorPort(Protocol):
         def ensure_collection(self, name, dims): ...
         def upsert(self, vectors, payloads): ...
         def search(self, vector, k): ...
     ```
   - Implement adapters that wrap memory_logger.py, longterm.py, qdrant_store.py.

6. **Model client adapter**
   - Wrap GeminiClient.py behind a simple interface (generate(), embed_batch()) to decouple reasoning from vendor client.

7. **Doctrine gate**
   - Integrate codex_binding_loader + codex_enforcer in router.dispatch:
     - Before executing a handler or composing a model prompt, check mandates/modes/domains.
     - On violation, return a Meta‑Comment/fix prompt instead of executing.

8. **Reasoning plugin registry**
   - Move LogicalFlowStrategy + BaseStrategy into reasoning/ with a registry:
     ```python
     Strategy = Protocol; registry: Dict[str, Strategy]
     def register(name, strat): ...
     def run(name, ctx, input): ...
     ```
   - Archon selects strategy by state or label; easy to add “creative/associative” next.

9. **Metrics at seams**
   - Replace scattered prints with metrics/events.emit():
     - turn_started/ended, retrieval_done, model_call, state_saved, ingest/embed events already exist; reuse your JSONL sink.

10. **Cutover via flags**
   - Feature flag in boot.py:
     - ARCHON_NEW=0 → archon_api delegates to legacy.
     - ARCHON_NEW=1 → archon_api uses new repl/router/handlers.
   - Migrate commands one by one by toggling handler registration.

---

## Safety nets and tests

- **Golden transcript harness**
  - Record a set of sessions with retrieval off and on.
  - Re‑run via both legacy and new façade; normalize outputs (strip timestamps/IDs); diff with tolerance for minor variation.
- **State invariants**
  - Unit tests: :focus sets state.focus_topic; :insight creates InsightCandidate and persists.
- **Latency budgets**
  - Assert p75/p95 envelopes for turn phases (prompt compose, model call, persist) using your metrics CLI.

---

## Minimal code skeletons

#### archon_api.py (façade)

```python
from .boot import BootConfig, boot_system
from .repl import run_loop

class ArchonAPI:
    def __init__(self, cfg: BootConfig):
        self.ctx = boot_system(cfg)

    def start(self):
        pass  # any warm-up

    def handle_turn(self, line: str) -> str:
        return run_loop.step(self.ctx, line)

    def shutdown(self):
        pass
```

#### router.py

```python
from .codex_enforcer import CodexEnforcer
from .commands.base import CommandHandler

class Router:
    def __init__(self, handlers: list[CommandHandler], enforcer: CodexEnforcer):
        self.handlers = handlers
        self.enforcer = enforcer

    def dispatch(self, line: str, ctx) -> str:
        labels = ctx.label_parser.extract(line, ctx)  # your existing label logic
        verdict = self.enforcer.enforce_and_prompt(labels, move_payload=None)
        if isinstance(verdict, dict) and verdict.get("type") == "meta_prompt":
            return verdict["message"]
        for h in self.handlers:
            if h.match(line):
                return h.execute(line, ctx)
        return ctx.reasoner.reply(line)  # default model path
```

#### metrics/events.py

```python
from dataclasses import dataclass
from time import perf_counter

@dataclass
class Event:
    name: str
    data: dict

def emit(name: str, **data):
    # write JSONL line to your metrics stream
    ...
```

---

## Immediate next actions

- **Create archon_legacy.py + façade** and switch main.py to ArchonAPI.
- **Extract REPL + router + 3 core handlers** (:focus, :insight, :retrieval) to prove the seam.
- **Wrap Hermetic/Qdrant/Gemini behind ports/adapters** for those handlers only.
- **Integrate codex enforcer** in router; verify doctrine prompts trigger correctly.
- **Run a golden transcript A/B** on those commands; confirm no regressions; then continue migrating handlers in small batches.

