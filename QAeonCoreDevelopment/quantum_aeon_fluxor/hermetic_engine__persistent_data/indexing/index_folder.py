from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Iterable, Any, Dict
import time
import json
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
    get_qdrant_client,
    ensure_collection,
    upsert_chunks,
)
from quantum_aeon_fluxor.utils.hash import chunk_uuid
from quantum_aeon_fluxor.utils.metrics import log_event, time_block, log_counter, log_latency

# Simple text file matcher (you can expand as needed)
TEXT_EXTS = {".md", ".txt", ".py", ".json"}


def read_text_files(root: Path) -> List[Tuple[Path, str]]:
    docs: List[Tuple[Path, str]] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # skip very small files
            if len(txt.strip()) < 16:
                continue
            docs.append((p, txt))
    return docs


def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
    return chunks


def _batched(seq: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i:i+size]


DISABLE_TUNING_ENV = "QAECORE_DISABLE_TUNING"
DRIFT_THRESHOLD_DEFAULT = 0.10  # 10%


def _load_tuning(path: Path) -> tuple[int, int, Dict[str, Any]] | None:
    try:
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            b = int(data.get('batch_size'))
            w = int(data.get('workers'))
            if b > 0 and w > 0:
                return b, w, data
    except Exception:
        pass
    return None


def index_folder(
    folder: str,
    collection: str = "qaecore_longterm_v1",
    max_chars: int = 2500,
    overlap: int = 200,
    dry_run: bool = False,
    batch_size: int = 16,
    workers: int = 4,
    embed_retries: int = 2,
    retry_backoff: float = 2.0,
) -> None:
    root = Path(folder).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    # Ensure env is loaded (for GOOGLE_API_KEY and QDRANT_*)
    try:
        from dotenv import load_dotenv, find_dotenv
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path)
    except Exception:
        pass

    embedder = GeminiEmbedder()
    client = get_qdrant_client()
    ensure_collection(client, collection, embedder.dim)

    docs = read_text_files(root)
    all_chunks: List[str] = []
    payloads: List[dict] = []
    ids: List[str] = []

    for path, text in docs:
        chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
        for i, ch in enumerate(chunks):
            cid = chunk_uuid(path, i, ch)
            ids.append(cid)
            all_chunks.append(ch)
            payloads.append({
                "path": str(path),
                "chunk_index": i,
                "rel_path": str(path.relative_to(root)),
                "text": ch[:1000]
            })

    log_event("ingest", "scan_complete", files=len(docs), chunks=len(all_chunks), collection=collection, dry_run=dry_run)

    if dry_run:
        print(f"[DRY-RUN] Would index {len(all_chunks)} chunks from {len(docs)} files into collection '{collection}'.")
        return

    if not all_chunks:
        print("No chunks to index.")
        return

    total_start = time.perf_counter()
    vectors: List[List[float]] = []

    def embed_batch(batch: List[str], attempt: int = 0) -> List[List[float]]:
        start = time.perf_counter()
        try:
            res = embedder.embed_texts(batch)
            dur_ms = (time.perf_counter() - start) * 1000.0
            log_latency("ingest", "embed_batch", dur_ms, batch_size=len(batch))
            return res
        except Exception as e:
            log_event("ingest", "embed:error", error=repr(e), batch_size=len(batch), attempt=attempt)
            if attempt < embed_retries:
                time.sleep(retry_backoff * (attempt + 1))
                return embed_batch(batch, attempt + 1)
            raise

    # Attempt to auto-tune if user didn't override defaults (only when values are defaults)
    tuning_file = Path('configs/.qaf_tuning.json')
    if os.getenv(DISABLE_TUNING_ENV):
        print("[TUNING] Auto-tuning disabled via env QAECORE_DISABLE_TUNING.")
    elif batch_size == 16 and workers == 4:  # only auto-tune when user left defaults
        tuned = _load_tuning(tuning_file)
        if tuned:
            tb, tw, meta = tuned
            sig = meta.get('dataset_hash')
            h = hashlib.sha1()
            for p, txt in docs:
                h.update(str(p).encode('utf-8'))
                h.update(str(len(txt)).encode('utf-8'))
            h.update(f"chunk_size={max_chars};overlap={overlap}".encode('utf-8'))
            current_sig = h.hexdigest()
            if sig and sig != current_sig:
                print("[TUNING] Tuning file dataset hash mismatch; ignoring recommendation.")
                log_event("ingest", "tuning_mismatch", tuning_chunk_size=meta.get('chunk_size'), tuning_overlap=meta.get('overlap'), current_chunk_size=max_chars, current_overlap=overlap)
            else:
                # Drift detection: if current chunk params differ > threshold from tuned values
                tuned_chunk = meta.get('chunk_size')
                tuned_overlap = meta.get('overlap')
                drift_threshold = float(os.getenv("QAECORE_TUNING_DRIFT_THRESHOLD", DRIFT_THRESHOLD_DEFAULT))
                needs_retune = False
                drift_reasons = []
                if isinstance(tuned_chunk, int) and tuned_chunk > 0:
                    rel = abs(max_chars - tuned_chunk) / tuned_chunk
                    if rel > drift_threshold:
                        needs_retune = True
                        drift_reasons.append(f"chunk_size rel_drift={rel:.2f}")
                if isinstance(tuned_overlap, int) and tuned_overlap > 0:
                    rel = abs(overlap - tuned_overlap) / tuned_overlap
                    if rel > drift_threshold:
                        needs_retune = True
                        drift_reasons.append(f"overlap rel_drift={rel:.2f}")
                batch_size, workers = tb, tw
                # Compute age_days from generated_at
                age_days = None
                gen = meta.get('generated_at')
                if gen:
                    try:
                        from datetime import datetime, timezone as _tz
                        gen_dt = datetime.fromisoformat(gen.replace('Z', '+00:00'))
                        age_days = (datetime.now(_tz.utc) - gen_dt).total_seconds() / 86400.0
                    except Exception:
                        pass
                print(f"[TUNING] Applied recommended batch_size={batch_size} workers={workers} (age_days={age_days:.2f} if age_days else 'n/a') from {tuning_file}")
                log_event("ingest", "tuning_applied", batch_size=batch_size, workers=workers, age_days=round(age_days,2) if age_days is not None else None)
                if needs_retune:
                    msg = "; ".join(drift_reasons) if drift_reasons else "param drift"
                    print(f"[TUNING] Retune suggested: {msg} (threshold {drift_threshold:.2f})")
                    log_event("ingest", "tuning_retune_recommended", reason=msg, threshold=drift_threshold, current_chunk_size=max_chars, current_overlap=overlap, tuned_chunk_size=tuned_chunk, tuned_overlap=tuned_overlap)

    with time_block("ingest", "embed", chunks=len(all_chunks), batch_size=batch_size, workers=workers):
        batches = list(_batched(all_chunks, batch_size))
        # Parallelize across batches
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                future_map = {ex.submit(embed_batch, b): idx for idx, b in enumerate(batches)}
                for fut in as_completed(future_map):
                    vectors.extend(fut.result())
        else:
            for b in batches:
                vectors.extend(embed_batch(b))

    with time_block("ingest", "upsert", chunks=len(all_chunks)):
        upsert_chunks(get_qdrant_client(), collection, vectors, payloads, ids=ids)
    log_counter("ingest", "chunks_indexed", value=len(all_chunks), collection=collection)

    total_dur_ms = (time.perf_counter() - total_start) * 1000.0
    throughput = (len(all_chunks) / (total_dur_ms / 1000.0)) if all_chunks else 0.0
    log_event("ingest", "ingest_summary", total_chunks=len(all_chunks), files=len(docs), total_ms=round(total_dur_ms,3), throughput_chunks_per_s=round(throughput,2), batch_size=batch_size, workers=workers)
    print(f"Indexed {len(all_chunks)} chunks from {len(docs)} files into collection '{collection}'. Throughput: {throughput:.2f} chunks/s")


def cli():
    import argparse

    parser = argparse.ArgumentParser(description="Index a folder into Qdrant using Gemini embeddings.")
    parser.add_argument("folder", help="Folder path to index")
    parser.add_argument("--collection", default="qaecore_longterm_v1")
    parser.add_argument("--max-chars", type=int, default=2500)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true", help="Scan & report counts without embedding/upserting")
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding batch size")
    parser.add_argument("--workers", type=int, default=4, help="Parallel embedding worker threads")
    parser.add_argument("--embed-retries", type=int, default=2, help="Retries per batch on failure")
    parser.add_argument("--retry-backoff", type=float, default=2.0, help="Backoff multiplier (seconds * attempt)")
    args = parser.parse_args()

    index_folder(
        args.folder,
        collection=args.collection,
        max_chars=args.max_chars,
        overlap=args.overlap,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        workers=args.workers,
        embed_retries=args.embed_retries,
        retry_backoff=args.retry_backoff,
    )


if __name__ == "__main__":
    cli()
