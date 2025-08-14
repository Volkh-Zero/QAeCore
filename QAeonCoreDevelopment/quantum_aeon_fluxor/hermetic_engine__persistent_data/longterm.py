from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import json

LONGTERM_DIR = Path(__file__).resolve().parent / "longterm_memory"
LONGTERM_DIR.mkdir(parents=True, exist_ok=True)


def write_blob(blob: str, tags: Optional[List[str]] = None, meta: Optional[Dict] = None) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    blob_id = f"blob-{ts}"
    (LONGTERM_DIR / f"{blob_id}.bin").write_text(blob, encoding="utf-8")
    meta_payload = {
        "id": blob_id,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat(),
        "meta": meta or {},
    }
    (LONGTERM_DIR / f"{blob_id}.json").write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    return blob_id


def read_blob(blob_id: str) -> Optional[str]:
    p = LONGTERM_DIR / f"{blob_id}.bin"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return None


def find_by_tag(tag: str) -> List[Dict]:
    results = []
    for meta_file in LONGTERM_DIR.glob("*.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if tag in meta.get("tags", []):
            results.append(meta)
    return sorted(results, key=lambda m: m.get("created_at", ""), reverse=True)
