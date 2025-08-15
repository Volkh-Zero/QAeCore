from __future__ import annotations

from quantum_aeon_fluxor.archon__supervisor_agent.state import ArchonState
from quantum_aeon_fluxor.syzygy__conversational_framework import __display_name__ as SYZ_NAME  # noqa: F401
from quantum_aeon_fluxor.syzygy__conversational_framework.bridge import compose_prompt
from quantum_aeon_fluxor.hermetic_engine__persistent_data import (
    episodic_log_interaction,
    GeminiClient,
)
from quantum_aeon_fluxor.utils.metrics import time_block, log_event, log_counter
from quantum_aeon_fluxor.hermetic_engine__persistent_data.longterm import write_blob


class Archon:
    """Minimal Archon orchestrator.

    - Maintains state
    - Composes prompts via Syzygy
    - Optionally retrieves context from Qdrant
    - Queries Gemini
    - Logs episodic transcript
    - Writes optional long-term memory blobs when tagged
    - Optional conversational embedding into Qdrant
    """

    def __init__(self):
        self.state = ArchonState.load()
        self.client = GeminiClient()
        self.retrieval_enabled = True
        self.collection = "qaecore_longterm_v1"
        self.active_collections: list[str] = []  # when non-empty, use multi-collection
        self.retrieve_k: int = 3
        self.context_block_enabled: bool = True
        self.collection_weights: dict[str, float] = {}
        self.retain_responses = False
        # conversational embedding settings
        self.autoembed_enabled = False
        self.conv_collection = "qaecore_conversations_v1"
        self.history: list[tuple[str, str]] = []  # (speaker, text)
        self.last_retrieval: list[tuple[float, dict, str]] = []

    def _embed_turns(self, turns: list[tuple[str, str]]):
        """Embed given turns into Qdrant conv collection with metadata"""
        try:
            from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
            from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
                get_qdrant_client, ensure_collection, upsert_chunks,
            )
            from quantum_aeon_fluxor.utils.hash import chunk_uuid
            from pathlib import Path
            # prepare
            embedder = GeminiEmbedder()
            client = get_qdrant_client()
            ensure_collection(client, self.conv_collection, embedder.dim)
            # build payloads
            texts = []
            payloads = []
            ids = []
            sess = self.state.thread_id or "default"
            base = Path(f"session:{sess}")
            # note: historical variable removed; index derived from enumerate
            # include their index relative to current history length
            for idx, (speaker, text) in enumerate(turns):
                texts.append(text)
                pid = chunk_uuid(base, idx, f"{speaker}:{text}")
                ids.append(pid)
                payloads.append({
                    "session": sess,
                    "role": speaker,
                    "turn_index": idx,
                    "focus_topic": self.state.focus_topic,
                    "text": text[:1000],
                })
            vecs = embedder.embed_texts(texts)
            upsert_chunks(client, self.conv_collection, vecs, payloads, ids=ids)
            print(f"[Embedded] {len(texts)} turns into collection={self.conv_collection}")
        except Exception as e:
            print(f"[Embed error] {e}")

    def run_turn(self, user_input: str, *, depth_level: str = "intermediate", retain: bool | None = None) -> str:
        # Commands (prefixed by ':')
        if user_input.startswith(":"):
            return self._handle_command(user_input)

        # Optionally fetch retrieval context
        retrieval_note = ""
        if self.retrieval_enabled:
            from time import perf_counter
            t0 = perf_counter()
            try:
                from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.search_text import search_text
                collections = self.active_collections if self.active_collections else [self.collection]
                print(f"[Retrieval] collections={collections} k={self.retrieve_k}")
                merged: list[tuple[float, dict, str]] = []
                for coll in collections:
                    try:
                        hits = search_text(user_input, collection=coll, k=self.retrieve_k)
                        w = self.collection_weights.get(coll, 1.0)
                        for score, payload in hits:
                            merged.append((score * w, payload, coll))
                    except Exception as e:
                        log_event("archon", "retrieval_error", collection=coll, error=str(e))
                        print(f"[Retrieval warn] collection={coll} error={e}")
                merged.sort(key=lambda x: x[0], reverse=True)
                top = merged[: self.retrieve_k]
                self.last_retrieval = top
                log_event("archon", "retrieval_done", collections=collections, total_candidates=len(merged), top_k=len(top))
                if top and self.context_block_enabled:
                    ctx_lines = []
                    for score, payload, coll in top:
                        path = payload.get("rel_path") or payload.get("path")
                        snippet = (payload.get("text") or "").replace("\n", " ")
                        if len(snippet) > 240:
                            snippet = snippet[:240] + "…"
                        ctx_lines.append(f"- [{score:.3f}] ({coll}) {path} :: {snippet}")
                    retrieval_note = ("\n\n=== Context ===\n"
                                    + f"Sources: {', '.join(collections)} | k={self.retrieve_k}\n"
                                    + "\n".join(ctx_lines)
                                    + "\n=== End Context ===")
            except Exception as e:
                retrieval_note = f"\n\n(Context retrieval unavailable: {e})"
                log_event("archon", "retrieval_fatal", error=str(e))
            finally:
                from time import perf_counter as _pc
                dur_ms = (_pc() - t0) * 1000
                log_event("archon", "retrieval_latency", duration_ms=round(dur_ms,2))

        # Compose prompt using Syzygy bridge
        composed_input = user_input + retrieval_note
        # Prepare a brief history window for mode selection
        history_texts = [t for _, t in self.history[-6:]]
        dl = getattr(self, "forced_depth", None) or depth_level
        with time_block("archon", "compose_prompt"):
            prompt = compose_prompt(
                composed_input,
                focus_topic=self.state.focus_topic,
                depth_level=dl,
                recent_history=history_texts,
                forced_mode=getattr(self, "forced_mode", None),
            )

        # Query Gemini
        with time_block("archon", "model_query"):
            response_text = self.client.query(prompt)
        log_counter("archon", "turn_completed", value=1)

        # Log transcript and update in-memory history
        episodic_log_interaction("Volkh", user_input)
        episodic_log_interaction("Archon", response_text)
        self.history.append(("Volkh", user_input))
        self.history.append(("Archon", response_text))

        # Optional retention (opaque blob)
        effective_retain = self.retain_responses if retain is None else retain
        if effective_retain:
            write_blob(response_text, tags=["archon", "response", self.state.phase])

        # Auto-embed last Archon response (and/or last turn) if enabled
        if self.autoembed_enabled:
            self._embed_turns(self.history[-2:])  # last user+archon

        # Update state (simple heuristic placeholder)
        if not self.state.focus_topic and len(user_input) > 0:
            self.state.focus_topic = user_input[:96]
        if "contradiction" in response_text.lower():
            self.state.flag_contradiction("Model mentioned contradiction in latest turn")
        with time_block("archon", "state_save"):
            self.state.save()
        log_event("archon", "turn_persisted", focus_topic=self.state.focus_topic, insights=len(self.state.insight_candidates))
        return response_text

    def _handle_command(self, cmd: str) -> str:
        parts = cmd.strip().split()
        if not parts:
            return "Empty command"
        head = parts[0].lower()

        def _bool(val: str) -> bool:
            return val.lower() in {"on", "true", "1"}

        if head in (":retain", ":r"):
            if len(parts) == 1:
                return f"retain={'on' if self.retain_responses else 'off'}"
            self.retain_responses = _bool(parts[1])
            return f"retain set to {'on' if self.retain_responses else 'off'}"
        if head in (":retrieval", ":rt"):
            if len(parts) == 1:
                return f"retrieval={'on' if self.retrieval_enabled else 'off'} collection={self.collection}"
            self.retrieval_enabled = _bool(parts[1])
            return f"retrieval set to {'on' if self.retrieval_enabled else 'off'}"
        if head in (":collection", ":col"):
            if len(parts) == 1:
                return f"collection={self.collection}"
            self.collection = parts[1]
            return f"collection set to {self.collection}"
        if head in (":collections", ":cols"):
            if len(parts) == 1 or parts[1] == "list":
                return f"active_collections={self.active_collections} (empty→single {self.collection})"
            sub = parts[1].lower()
            if sub == "add" and len(parts) >= 3:
                name = parts[2]
                if name not in self.active_collections:
                    self.active_collections.append(name)
                return f"collections={self.active_collections}"
            if sub == "remove" and len(parts) >= 3:
                name = parts[2]
                self.active_collections = [c for c in self.active_collections if c != name]
                return f"collections={self.active_collections}"
            if sub == "clear":
                self.active_collections = []
                return "collections cleared"
            return "Usage: :collections [list|add <name>|remove <name>|clear]"
        if head in (":k", ":topk"):
            if len(parts) == 1 or not parts[1].isdigit():
                return f"k={self.retrieve_k}"
            self.retrieve_k = max(1, int(parts[1]))
            return f"k set to {self.retrieve_k}"
        if head in (":context", ":ctx"):
            if len(parts) == 1:
                return f"context_block={'on' if self.context_block_enabled else 'off'}"
            self.context_block_enabled = _bool(parts[1])
            return f"context_block set to {'on' if self.context_block_enabled else 'off'}"
        if head in (":weights", ":wts"):
            if len(parts) == 1 or parts[1] == 'list':
                return f"weights={self.collection_weights or {}}"
            sub = parts[1].lower()
            if sub == 'set' and len(parts) >= 4:
                coll = parts[2]
                try:
                    self.collection_weights[coll] = max(0.0, float(parts[3]))
                except ValueError:
                    return "Usage: :weights set <collection> <weight>"
                return f"weights={self.collection_weights}"
            if sub == 'clear':
                self.collection_weights = {}
                return "weights cleared"
            return "Usage: :weights [list|set <collection> <weight>|clear]"
        if head in (":mode", ":m"):
            if len(parts) == 1:
                return f"mode={'auto' if not getattr(self, 'forced_mode', None) else self.forced_mode}"
            if parts[1].lower() == 'set' and len(parts) >= 3:
                val = parts[2]
                if val.lower() == 'auto':
                    self.forced_mode = None
                    return "mode set to auto"
                self.forced_mode = val
                return f"mode forced to {val}"
            return "Usage: :mode [set <QAeMode>|auto]"
        if head in (":depth", ":d"):
            if len(parts) == 1:
                cur = getattr(self, 'forced_depth', None)
                return f"depth={'auto' if not cur else cur}"
            val = parts[1].lower()
            if val in {"surface","intermediate","deep","transcendent"}:
                self.forced_depth = val
                return f"depth forced to {val}"
            if val == 'auto':
                self.forced_depth = None
                return "depth set to auto"
            return "Usage: :depth [surface|intermediate|deep|transcendent|auto]"
        if head in (":state", ":s"):
            return self.state.model_dump_json(indent=2)
        if head in (":focus", ":f"):
            if len(parts) == 1:
                return f"focus_topic={self.state.focus_topic!r}"
            topic = cmd.split(" ", 1)[1].strip()
            if not topic:
                return "Usage: :focus <topic>"
            self.state.focus_topic = topic[:200]
            self.state.save()
            return f"focus set to {self.state.focus_topic!r}"
        if head in (":insight", ":i"):
            if len(parts) == 1:
                return "Usage: :insight <summary>"
            summary = cmd.split(" ", 1)[1].strip()
            if not summary:
                return "Usage: :insight <summary>"
            self.state.register_insight(summary=summary)
            self.state.save()
            return f"insight registered (total={len(self.state.insight_candidates)})"
        if head in (":session", ":sess"):
            if len(parts) == 1:
                return f"thread_id={self.state.thread_id!r}"
            sess = cmd.split(" ", 1)[1].strip()
            if not sess:
                return "Usage: :session <id>"
            self.state.thread_id = sess[:100]
            self.state.save()
            return f"session set to {self.state.thread_id!r}"
        if head in (":autoembed", ":ae"):
            if len(parts) == 1:
                return f"autoembed={'on' if self.autoembed_enabled else 'off'} collection={self.conv_collection}"
            if _bool(parts[1]):
                self.autoembed_enabled = True
                return f"autoembed set to on (collection={self.conv_collection})"
            if parts[1].lower() in {"off","false","0"}:
                self.autoembed_enabled = False
                return "autoembed set to off"
            return "Usage: :autoembed [on|off]"
        if head in (":embed_last", ":el"):
            n = 2
            if len(parts) >= 2 and parts[1].isdigit():
                n = max(1, int(parts[1]))
            turns = self.history[-n:]
            if not turns:
                return "No turns to embed."
            if len(parts) >= 3:
                self.conv_collection = parts[2]
            self._embed_turns(turns)
            return f"embedded {len(turns)} turns into {self.conv_collection}"
        if head in (":search", ":q"):
            if len(parts) < 2:
                return "Usage: :search your query..."
            query = cmd.split(" ", 1)[1].replace(":search", "", 1).replace(":q", "", 1).strip()
            try:
                from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.search_text import search_text
                coll_list = self.active_collections if self.active_collections else [self.collection]
                merged = []
                for coll in coll_list:
                    try:
                        hits = search_text(query, collection=coll, k=self.retrieve_k)
                        for score, payload in hits:
                            merged.append((score, payload, coll))
                    except Exception as e:
                        merged.append((0.0, {"error": str(e)}, coll))
                merged.sort(key=lambda x: x[0], reverse=True)
                if not merged:
                    return "No results."
                lines = [f"Top {min(len(merged), self.retrieve_k)} across {coll_list}:"]
                for score, payload, coll in merged[: self.retrieve_k]:
                    path = payload.get("rel_path") or payload.get("path")
                    lines.append(f"- [{score:.3f}] ({coll}) {path}")
                return "\n".join(lines)
            except Exception as e:
                return f"Search error: {e}"
        if head in (":expand", ":x"):
            if len(parts) < 2 or not parts[1].isdigit():
                return "Usage: :expand <n>"
            idx = int(parts[1]) - 1
            if not self.last_retrieval or idx < 0 or idx >= len(self.last_retrieval):
                return "No such item in last retrieval."
            try:
                import json
                score, payload, coll = self.last_retrieval[idx]
                return json.dumps({"score": score, "collection": coll, "payload": payload}, indent=2)
            except Exception as e:
                return f"Expand error: {e}"
        return "Unknown command. Available: :retain, :retrieval, :collection, :collections, :k, :context, :weights, :state, :focus, :insight, :search, :expand"
