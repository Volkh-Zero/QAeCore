"""Calibrate optimal embedding batch size.

Empirically measures latency & throughput for several batch sizes using the
current GeminiEmbedder configuration. Writes metrics events (stream 'calibrate')
and prints a summary table.

Usage (example):
python -m scripts.calibrate_embedding --collection qaecore_longterm_v1 --sample 120 --batch-sizes 4 8 16 32 --workers 4

Notes:
- Uses existing index_folder chunking over a single folder to gather text.
- Does NOT upsert to Qdrant (pure embedding benchmark).
- Respects GOOGLE_API_KEY from environment.
"""
from __future__ import annotations

import argparse
import random
import time
import csv
import json as _json
from math import sqrt
import hashlib
import uuid
from pathlib import Path
from statistics import mean

from quantum_aeon_fluxor.hermetic_engine__persistent_data.indexing.index_folder import read_text_files, chunk_text
from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.utils.metrics import log_event, log_latency


def sample_chunks(folder: Path, max_chars: int, overlap: int, limit: int) -> list[str]:
    docs = read_text_files(folder)
    chunks: list[str] = []
    # We also gather doc metadata to build a dataset signature.
    for _, txt in docs:
        for ch in chunk_text(txt, max_chars=max_chars, overlap=overlap):
            chunks.append(ch)
            if len(chunks) >= limit:
                break
        if len(chunks) >= limit:
            break
    return chunks


def dataset_signature(docs, chunk_size: int, overlap: int) -> str:
    h = hashlib.sha1()
    # Use path + length of text for stability; ignore text content for speed
    for p, txt in docs:
        h.update(str(p).encode('utf-8'))
        h.update(str(len(txt)).encode('utf-8'))
    h.update(f"chunk_size={chunk_size};overlap={overlap}".encode('utf-8'))
    return h.hexdigest()


def benchmark(embedder: GeminiEmbedder, texts: list[str], batch_size: int, workers: int, progress: bool, progress_every: int = 5) -> dict:
    # Simple sequential vs parallel worker threads similar to indexer logic
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def batches(seq):
        for i in range(0, len(seq), batch_size):
            yield seq[i:i+batch_size]

    latencies = []
    start_total = time.perf_counter()

    completed = 0

    def embed_batch(batch):
        start = time.perf_counter()
        res = embedder.embed_texts(batch)
        dur_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(dur_ms)
        log_latency('calibrate', 'embed_batch', dur_ms, batch_size=len(batch))
        nonlocal completed
        completed += 1
        if progress and completed % progress_every == 0:
            print(f"  batch {completed} ({len(batch)} items) avg_batch_ms={sum(latencies)/len(latencies):.1f}", flush=True)
        return res

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(embed_batch, b) for b in batches(texts)]
            for f in as_completed(futures):
                f.result()
    else:
        for b in batches(texts):
            embed_batch(b)

    total_ms = (time.perf_counter() - start_total) * 1000.0
    throughput = len(texts) / (total_ms / 1000.0)
    # Additional stats
    median = sorted(latencies)[len(latencies)//2] if latencies else 0.0
    mean_v = mean(latencies) if latencies else 0.0
    var = sum((x-mean_v)**2 for x in latencies)/len(latencies) if latencies else 0.0
    stddev = sqrt(var)

    return {
        'batch_size': batch_size,
        'workers': workers,
        'batches': len(latencies),
        'total_ms': round(total_ms, 2),
        'mean_batch_ms': round(mean_v, 2),
        'median_batch_ms': round(median, 2),
        'p95_batch_ms': round(sorted(latencies)[max(0, int(0.95 * (len(latencies)-1)))], 2) if latencies else 0.0,
        'throughput_chunks_per_s': round(throughput, 2),
        'stddev_batch_ms': round(stddev, 2),
    }


def main():
    ap = argparse.ArgumentParser(description='Calibrate embedding batch size & workers.')
    ap.add_argument('folder', help='Folder with raw text files')
    ap.add_argument('--sample', type=int, default=200, help='Total chunks to sample')
    ap.add_argument('--max-chars', type=int, default=2500)
    ap.add_argument('--overlap', type=int, default=200)
    ap.add_argument('--batch-sizes', type=int, nargs='+', default=[4,8,16,32])
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--progress', action='store_true', help='Show progress every N batches')
    ap.add_argument('--progress-every', type=int, default=5, help='Progress batch interval')
    ap.add_argument('--csv', help='Write CSV summary to file')
    ap.add_argument('--json', dest='json_out', help='Write JSON summary to file')
    ap.add_argument('--quiet', action='store_true', help='Suppress table output (use with --csv/--json)')
    ap.add_argument('--tuning-file', default='configs/.qaf_tuning.json', help='Path to write recommended settings (JSON)')
    ap.add_argument('--force-retune', action='store_true', help='Ignore existing tuning file (overwrite)')
    args = ap.parse_args()

    folder = Path(args.folder).resolve()
    docs = read_text_files(folder)
    chunks = sample_chunks(folder, args.max_chars, args.overlap, args.sample)
    if not chunks:
        raise SystemExit('No chunks sampled.')

    random.shuffle(chunks)
    # keep exactly sample size
    chunks = chunks[:args.sample]

    embedder = GeminiEmbedder()

    results = []
    log_event('calibrate', 'start', sample=len(chunks), folder=str(folder))
    for bs in args.batch_sizes:
        r = benchmark(embedder, chunks, bs, args.workers, progress=args.progress, progress_every=args.progress_every)
        log_event('calibrate', 'result', **r)
        results.append(r)
    log_event('calibrate', 'end')

    # Print summary table (map display labels to result keys)
    columns = [
        ("batch", "batch_size"),
        ("workers", "workers"),
        ("batches", "batches"),
        ("total_ms", "total_ms"),
        ("mean_batch_ms", "mean_batch_ms"),
        ("median_batch_ms", "median_batch_ms"),
        ("p95_batch_ms", "p95_batch_ms"),
        ("stddev_batch_ms", "stddev_batch_ms"),
        ("throughput_chunks_per_s", "throughput_chunks_per_s"),
    ]
    if not results:
        print("No calibration results collected.")
        return

    widths = {}
    for label, key in columns:
        max_val_len = max((len(str(r.get(key, ''))) for r in results), default=0)
        widths[label] = max(len(label), max_val_len)

    def fmt_header():
        return '  '.join(label.rjust(widths[label]) for label, _ in columns)

    def fmt_row(res_dict):
        return '  '.join(str(res_dict.get(key, '')).rjust(widths[label]) for label, key in columns)

    if not args.quiet:
        print('Calibration Results:')
        print(fmt_header())
        for r in results:
            print(fmt_row(r))

    # Recommendation selection: maximize throughput, then minimize stddev
    if results:
        rec = max(results, key=lambda r: (r.get('throughput_chunks_per_s', 0), -r.get('stddev_batch_ms', 1e9)))
        d_sig = dataset_signature(docs, args.max_chars, args.overlap)
        # If tuning file exists and not forcing, load to compute age_days
        age_days = None
        tuning_path = Path(args.tuning_file)
        if tuning_path.exists() and not args.force_retune:
            try:
                with tuning_path.open('r', encoding='utf-8') as f:
                    existing = _json.load(f)
                old_ts = existing.get('generated_at')
                if old_ts:
                    from datetime import datetime, timezone as _tz
                    try:
                        old_dt = datetime.fromisoformat(old_ts.replace('Z', '+00:00'))
                        age_days = (datetime.now(_tz.utc) - old_dt).total_seconds() / 86400.0
                    except Exception:
                        pass
            except Exception:
                pass
        run_id = uuid.uuid4().hex[:12]
        recommendation = {
            'batch_size': rec['batch_size'],
            'workers': rec['workers'],
            'throughput_chunks_per_s': rec['throughput_chunks_per_s'],
            'mean_batch_ms': rec['mean_batch_ms'],
            'stddev_batch_ms': rec['stddev_batch_ms'],
            'median_batch_ms': rec.get('median_batch_ms'),
            'p95_batch_ms': rec.get('p95_batch_ms'),
            'sample': len(chunks),
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'strategy': 'throughput_then_stability',
            'chunk_size': args.max_chars,
            'overlap': args.overlap,
            'dataset_hash': d_sig,
            'success': True,
            'age_days_previous': round(age_days, 2) if age_days is not None else None,
            'force_retune': bool(args.force_retune),
            'run_id': run_id,
        }
        # Write tuning file
        try:
            tuning_path.parent.mkdir(parents=True, exist_ok=True)
            with open(args.tuning_file, 'w', encoding='utf-8') as f:
                _json.dump(recommendation, f, ensure_ascii=False, indent=2)
            if not args.quiet:
                print(f"Wrote recommendation to {args.tuning_file}: batch_size={rec['batch_size']} workers={rec['workers']}")
            log_event('calibrate', 'recommendation', **recommendation)
        except Exception as e:
            log_event('calibrate', 'recommendation:error', error=repr(e))

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([label for label, _ in columns])
            for r in results:
                writer.writerow([r.get(key, '') for _, key in columns])
        print(f"Wrote CSV: {args.csv}")

    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            _json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Wrote JSON: {args.json_out}")


if __name__ == '__main__':
    main()
