from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import os
import re

from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
    get_qdrant_client,
    ensure_collection,
    upsert_chunks,
)

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


def index_folder(
    folder: str,
    collection: str = "qaecore_longterm_v1",
    max_chars: int = 2000,
    overlap: int = 200,
) -> None:
    root = Path(folder).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    embedder = GeminiEmbedder()
    client = get_qdrant_client()
    ensure_collection(client, collection, embedder.dim)

    docs = read_text_files(root)
    all_chunks: List[str] = []
    payloads: List[dict] = []

    for path, text in docs:
        chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
        for i, ch in enumerate(chunks):
            all_chunks.append(ch)
            payloads.append({
                "path": str(path),
                "chunk_index": i,
                "rel_path": str(path.relative_to(root)),
            })

    if not all_chunks:
        print("No chunks to index.")
        return

    vectors = embedder.embed_texts(all_chunks)
    upsert_chunks(get_qdrant_client(), collection, vectors, payloads)
    print(f"Indexed {len(all_chunks)} chunks from {len(docs)} files into collection '{collection}'.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Index a folder into Qdrant using Gemini embeddings.")
    parser.add_argument("folder", help="Folder path to index")
    parser.add_argument("--collection", default="qaecore_longterm_v1")
    parser.add_argument("--max-chars", type=int, default=2000)
    parser.add_argument("--overlap", type=int, default=200)
    args = parser.parse_args()

    index_folder(args.folder, collection=args.collection, max_chars=args.max_chars, overlap=args.overlap)
