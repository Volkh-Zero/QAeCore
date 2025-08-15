"""Lightweight metrics & structured event logging utility.

Writes newline-delimited JSON (JSONL) records under a metrics directory so we can
retrofit analysis (throughput, latency, cache hits, mode selections, etc.) without
introducing heavy deps.

Design goals:
- Zero external dependencies (pure stdlib)
- Non-blocking best-effort (swallow IO errors)
- Simple public API: log_event(name, **fields); time_block(name)(context manager)
- Automatic ISO timestamp + monotonic duration for timed blocks

Future extensions:
- In-memory ring buffer w/ flush
- Aggregations (rolling averages)
- Export to Prometheus / OpenTelemetry bridge
"""
from __future__ import annotations

from pathlib import Path
from time import perf_counter
from datetime import datetime, timezone
import json
import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator

METRICS_DIR_ENV = "QAECORE_METRICS_DIR"
ROTATE_ENV = "QAECORE_METRICS_ROTATE_DAILY"  # set to any non-empty value to enable daily rotation
DEFAULT_SUBDIR = "metrics"
_lock = threading.Lock()


def _metrics_dir() -> Path:
    base = os.getenv(METRICS_DIR_ENV)
    if base:
        p = Path(base).expanduser().resolve()
    else:
        # project root heuristic: current working directory
        p = Path.cwd() / DEFAULT_SUBDIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def _file_for(name: str) -> Path:
    """Return path for a metrics stream file.

    If daily rotation is enabled via env var QAECORE_METRICS_ROTATE_DAILY, files are named
    <stream>-YYYYMMDD.jsonl, else <stream>.jsonl
    """
    safe = name.replace("/", "_")
    if os.getenv(ROTATE_ENV):
        date_str = datetime.utcnow().strftime("%Y%m%d")
        fname = f"{safe}-{date_str}.jsonl"
    else:
        fname = f"{safe}.jsonl"
    return _metrics_dir() / fname


def log_event(stream: str, event: str, **fields: Any) -> None:
    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    path = _file_for(stream)
    try:
        line = json.dumps(record, ensure_ascii=False)
        with _lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        # best-effort; never raise during core flow
        pass


@contextmanager
def time_block(stream: str, event: str, **fields: Any) -> Iterator[None]:
    """Context manager to time a code block and emit start/stop events with duration_ms."""
    start = perf_counter()
    log_event(stream, event + ":start", **fields)
    status = "ok"
    err: str | None = None
    try:
        yield
    except Exception as e:  # pragma: no cover - we still log
        status = "error"
        err = repr(e)
        raise
    finally:
        dur_ms = (perf_counter() - start) * 1000.0
        log_event(stream, event + ":end", duration_ms=round(dur_ms, 3), status=status, **({"error": err} if err else {}))


def log_latency(stream: str, event: str, duration_ms: float, **fields: Any) -> None:
    log_event(stream, event, duration_ms=round(duration_ms, 3), **fields)


def log_counter(stream: str, event: str, value: int = 1, **fields: Any) -> None:
    log_event(stream, event, value=value, **fields)
