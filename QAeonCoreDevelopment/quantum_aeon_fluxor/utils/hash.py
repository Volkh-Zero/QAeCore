from __future__ import annotations
import hashlib
import uuid
from pathlib import Path


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_id(path: Path, chunk_index: int, text: str) -> str:
    base = f"{str(path)}::{chunk_index}::" + text
    return sha256_text(base)


def chunk_uuid(path: Path, chunk_index: int, text: str) -> str:
    """Generate a stable UUID v5 for Qdrant point IDs.

    Uses NAMESPACE_URL with a deterministic name based on path, index, and sha256 of text.
    """
    h = chunk_id(path, chunk_index, text)
    name = f"{path}::{chunk_index}::{h}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
