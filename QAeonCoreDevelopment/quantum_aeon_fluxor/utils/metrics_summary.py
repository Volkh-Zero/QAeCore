"""Metrics summary CLI for Quantum Aeon Fluxor.

Reads JSONL metric streams (default ./metrics or QAECORE_METRICS_DIR) and outputs
aggregated latency stats, counts, and recent events.

Usage:
qaf-metrics                     # default summary
qaf-metrics --streams archon gemini ingest --last 50
qaf-metrics --raw archon        # dump raw lines for a stream
qaf-metrics --since '2025-08-15T10:00:00Z'

Design:
- Pure stdlib
- Defensive parsing (skips malformed lines)
- Basic statistics: count, min, p50, p90, p95, max, mean for duration_ms
- Groups per event (compose_prompt:end, model_query:end, etc.)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import List, Dict, Any, Iterable
from datetime import datetime, timezone
import os
import json as _json

DEFAULT_DIR = Path(os.getenv("QAECORE_METRICS_DIR", Path.cwd() / "metrics"))


@dataclass
class StatBucket:
    durations: List[float] = field(default_factory=list)

    def add(self, v: float):
        self.durations.append(v)

    def summary(self) -> Dict[str, Any]:
        if not self.durations:
            return {"count": 0}
        data = sorted(self.durations)
        def pct(p: float) -> float:
            if not data:
                return 0.0
            idx = min(len(data)-1, int(p * (len(data)-1)))
            return data[idx]
        return {
            "count": len(data),
            "min": round(data[0], 2),
            "p50": round(pct(0.5), 2),
            "p90": round(pct(0.9), 2),
            "p95": round(pct(0.95), 2),
            "max": round(data[-1], 2),
            "mean": round(mean(data), 2),
        }


def iter_lines(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                yield obj
            except Exception:
                continue


def parse_since(s: str | None):
    if not s:
        return None
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except Exception:
        raise SystemExit(f"Invalid --since value: {s}")


def summarize_stream(stream: str, since: datetime | None, last: int | None, raw: bool):
    file_path = DEFAULT_DIR / f"{stream}.jsonl"
    lines = list(iter_lines(file_path))
    if since:
        lines = [rec for rec in lines if 'ts' in rec and _ts_dt(rec['ts']) >= since]
    if raw:
        seq = lines[-(last or len(lines)):] if last else lines
        for rec in seq:
            print(json.dumps(rec, ensure_ascii=False))
        return

    # Group durations by event name where duration_ms present
    buckets: Dict[str, StatBucket] = {}
    count_events: Dict[str, int] = {}

    tail = lines[-(last or 25):] if lines else []

    for rec in lines:
        ev = rec.get('event')
        if not ev:
            continue
        if 'duration_ms' in rec:
            buckets.setdefault(ev, StatBucket()).add(float(rec['duration_ms']))
        # generic counter events (value field) accumulate
        if 'value' in rec:
            count_events[ev] = count_events.get(ev, 0) + int(rec.get('value', 0))

    print(f"\nStream: {stream}")
    if not lines:
        print("  (no data)")
        return
    print(f"  Records: {len(lines)}  File: {file_path}")

    if buckets:
        print("  Timed Events:")
        for ev, bucket in sorted(buckets.items()):
            stats = bucket.summary()
            print(f"    - {ev}: count={stats['count']} min={stats.get('min')} p50={stats.get('p50')} p90={stats.get('p90')} p95={stats.get('p95')} max={stats.get('max')} mean={stats.get('mean')}")
    if count_events:
        print("  Counter Events:")
        for ev, total in sorted(count_events.items()):
            print(f"    - {ev}: total={total}")

    if tail:
        print("  Recent Events:")
        for rec in tail:
            ev = rec.get('event')
            dur = rec.get('duration_ms')
            status = rec.get('status')
            msg = f"    - {rec.get('ts')} {ev}"
            if dur is not None:
                msg += f" {dur:.1f}ms"
            if status:
                msg += f" status={status}"
            err = rec.get('error')
            if err:
                msg += f" error={err}"
            print(msg)


def _ts_dt(ts: str) -> datetime:
    try:
        if ts.endswith('Z'):
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.now(timezone.utc)


def cli():
    global DEFAULT_DIR  # must appear before first use/assignment
    parser = argparse.ArgumentParser(description="Summarize QAeCore metrics JSONL streams.")
    parser.add_argument('--dir', default=str(DEFAULT_DIR), help='Metrics directory')
    parser.add_argument('--streams', nargs='*', default=['archon','gemini','ingest'], help='Stream names (files <name>.jsonl)')
    parser.add_argument('--since', help='ISO timestamp (e.g. 2025-08-15T10:00:00Z)')
    parser.add_argument('--last', type=int, help='Limit recent lines/events displayed')
    parser.add_argument('--raw', action='store_true', help='Raw JSON lines output for each stream')
    parser.add_argument('--show-tuning-only', action='store_true', help='Only display current tuning recommendation info and exit')
    args = parser.parse_args()

    DEFAULT_DIR = Path(args.dir).expanduser().resolve()

    since_dt = parse_since(args.since)

    if not args.show_tuning_only:
        for stream in args.streams:
            summarize_stream(stream, since_dt, args.last, args.raw)
    # Show tuning info (even if show-tuning-only) unless raw requested
    if (not args.raw):
        # Look in configs for tuning file
        tuning_path = Path(args.dir).parent / 'configs' / '.qaf_tuning.json'
        # Normalize path resolution (metrics dir may be relative)
        try:
            tuning_path = tuning_path.resolve()
            if tuning_path.exists():
                with tuning_path.open('r', encoding='utf-8') as f:
                    tuning = _json.load(f)
                print("\nTuning Recommendation:")
                gen_at = tuning.get('generated_at')
                age_days = None
                if gen_at:
                    try:
                        gen_dt = datetime.fromisoformat(gen_at.replace('Z', '+00:00'))
                        age_days = (datetime.now(timezone.utc) - gen_dt).total_seconds() / 86400.0
                    except Exception:
                        pass
                print(f"  batch_size={tuning.get('batch_size')} workers={tuning.get('workers')} sample={tuning.get('sample')} chunk_size={tuning.get('chunk_size')} overlap={tuning.get('overlap')} generated_at={gen_at} age_days={round(age_days,2) if age_days is not None else 'n/a'}")
                # Extra fields if present
                extras = {
                    'throughput_chunks_per_s': tuning.get('throughput_chunks_per_s'),
                    'strategy': tuning.get('strategy'),
                    'run_id': tuning.get('run_id'),
                    'dataset_hash': tuning.get('dataset_hash'),
                    'age_days_previous': tuning.get('age_days_previous'),
                    'force_retune': tuning.get('force_retune'),
                }
                print("  details:" + " ".join(f"{k}={v}" for k, v in extras.items() if v is not None))
            else:
                pass
        except Exception:
            pass

if __name__ == '__main__':
    cli()
