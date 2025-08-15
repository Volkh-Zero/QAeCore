from pathlib import Path
import json
import tempfile
import subprocess
import sys

# We invoke the installed console script via python -m to exercise CLI parsing.

METRICS_SAMPLE = [
    {"ts": "2025-08-15T00:00:00+00:00", "event": "embed:end", "duration_ms": 100.0, "status": "ok"},
    {"ts": "2025-08-15T00:00:01+00:00", "event": "embed:end", "duration_ms": 300.0, "status": "ok"},
    {"ts": "2025-08-15T00:00:02+00:00", "event": "upsert:end", "duration_ms": 50.0, "status": "ok"},
    {"ts": "2025-08-15T00:00:03+00:00", "event": "chunks_indexed", "value": 42},
]


def write_stream(tmpdir: Path, name: str, records):
    p = tmpdir / f"{name}.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return p


def run_cli(tmpdir: Path, extra_args=None):
    # Use module invocation; adjust path to metrics_summary module.
    cmd = [sys.executable, "-m", "quantum_aeon_fluxor.utils.metrics_summary", "--dir", str(tmpdir), "--streams", "ingest"]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_summary_basic():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write_stream(tmp, "ingest", METRICS_SAMPLE)
        res = run_cli(tmp)
        out = res.stdout
        # Basic assertions
        assert "Stream: ingest" in out
        assert "embed:end" in out  # timed event
        assert "chunks_indexed" in out  # counter event
        assert "count=2" in out  # two embed:end events
        assert "total=42" in out  # counter total


def test_raw_mode():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write_stream(tmp, "ingest", METRICS_SAMPLE)
        res = run_cli(tmp, ["--raw"])
    out_lines = [line for line in res.stdout.strip().splitlines() if line]
    # Raw mode should output JSON lines only (no 'Stream:' header)
    assert out_lines[0].startswith('{')
    assert any('"embed:end"' in line or 'embed:end' in line for line in out_lines)


if __name__ == "__main__":  # pragma: no cover
    test_summary_basic()
    test_raw_mode()
    print("Tests ran standalone.")
