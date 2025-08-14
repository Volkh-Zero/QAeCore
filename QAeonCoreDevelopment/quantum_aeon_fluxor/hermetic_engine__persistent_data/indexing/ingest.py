from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure env for GOOGLE_API_KEY, QDRANT_* if needed downstream
try:
    from dotenv import load_dotenv, find_dotenv
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
except Exception:
    pass

from quantum_aeon_fluxor.hermetic_engine__persistent_data.indexing.index_folder import chunk_text
from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
    get_qdrant_client,
    ensure_collection,
    upsert_chunks,
)
from qdrant_client.http.models import VectorParams, Distance
from quantum_aeon_fluxor.utils.hash import chunk_uuid
try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **kwargs):
        return x

SUPPORTED_EXTS = {".pdf", ".epub", ".txt", ".md"}
DEFAULT_COLLECTION = "qaecore_library_v1"
DEFAULT_PARSED_DIRNAME = "parsed_corpus"


def parse_pdf(path: Path) -> Tuple[str, Dict]:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    meta = {}
    try:
        info = reader.metadata or {}
        meta["title"] = getattr(info, "title", None) or info.get("/Title")
        meta["author"] = getattr(info, "author", None) or info.get("/Author")
    except Exception:
        pass
    text = "\n\n".join(t.strip() for t in texts if t and t.strip())
    return text, meta


def parse_epub(path: Path) -> Tuple[str, Dict]:
    from ebooklib import epub
    try:
        book = epub.read_epub(str(path))
    except Exception as e:
        raise RuntimeError(f"EPUB parse failed: {e}")
    parts: List[str] = []
    for item in book.get_items():
        if item.get_type() == epub.ITEM_DOCUMENT:
            content = item.get_content()
            try:
                from bs4 import BeautifulSoup  # type: ignore
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator=" ")
            except Exception:
                text = content.decode(errors="ignore")
            parts.append(text)
    # metadata
    meta = {}
    try:
        titles = book.get_metadata("DC", "title")
        if titles:
            meta["title"] = titles[0][0]
        authors = book.get_metadata("DC", "creator")
        if authors:
            meta["author"] = authors[0][0]
    except Exception:
        pass
    text = "\n\n".join(p.strip() for p in parts if p and p.strip())
    return text, meta


def parse_text_like(path: Path) -> Tuple[str, Dict]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore"), {}
    except Exception as e:
        raise RuntimeError(f"Text read failed: {e}")


def parse_file(path: Path) -> Tuple[str, Dict]:
    ext = path.suffix.lower()
    meta: Dict = {
        "source_path": str(path),
        "ext": ext,
    }
    if ext == ".pdf":
        text, extra = parse_pdf(path)
    elif ext == ".epub":
        text, extra = parse_epub(path)
    elif ext in {".txt", ".md"}:
        text, extra = parse_text_like(path)
    else:
        raise ValueError(f"Unsupported extension: {ext}")
    meta.update(extra)
    return text, meta


def gather_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            files.append(p)
    return files


def ingest(
    folder: str,
    collection: str = DEFAULT_COLLECTION,
    max_chars: int = 2000,
    overlap: int = 200,
    dry_run: bool = False,
    write_parsed: bool = False,
    parsed_dir: Optional[str] = None,
    recreate: bool = False,
    embed_batch_size: int = 32,
    upsert_batch_size: int = 500,
    workers: int = 4,
    embed_concurrency: int = 4,
    use_cache: bool = True,
    profile: Optional[str] = None,
) -> None:
    root = Path(folder).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {root}")

    # Apply profile presets
    if profile:
        p = profile.lower()
        if p == "aggressive":
            max_chars = 2600
            overlap = 220
            embed_batch_size = max(embed_batch_size, 48)
            upsert_batch_size = max(upsert_batch_size, 800)
            workers = max(workers, 8)
            embed_concurrency = max(embed_concurrency, 6)
        elif p == "books":
            max_chars = 2800
            overlap = 250
            embed_batch_size = max(embed_batch_size, 48)
            upsert_batch_size = max(upsert_batch_size, 1000)
            workers = max(workers, 8)
            embed_concurrency = max(embed_concurrency, 6)
        elif p == "conservative":
            max_chars = 2000
            overlap = 200
            embed_batch_size = 32
            upsert_batch_size = 500
            workers = max(workers, 4)
            embed_concurrency = max(embed_concurrency, 4)

    out_dir = None
    if write_parsed:
        out_dir = Path(parsed_dir).resolve() if parsed_dir else (root.parent / DEFAULT_PARSED_DIRNAME)
        out_dir.mkdir(parents=True, exist_ok=True)

    paths = gather_files(root)
    if not paths:
        print("No supported files found.")
        return

    # Dry-run summary
    if dry_run:
        print(f"[Dry Run] Found {len(paths)} files. Estimating chunk counts:")
        total = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(parse_file, p): p for p in paths}
            for fut in tqdm(as_completed(futs), total=len(futs), desc="parse"):
                p = futs[fut]
                try:
                    text, _ = fut.result()
                    chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
                    print(f"- {p} :: {len(chunks)} chunks")
                    total += len(chunks)
                except Exception as e:
                    print(f"- {p} :: parse error: {e}")
        print(f"[Dry Run] Total estimated chunks: {total}")
        return

    embedder = GeminiEmbedder()
    client = get_qdrant_client()
    if recreate:
        print(f"[Recreate] {collection}")
        client.recreate_collection(collection_name=collection, vectors_config=VectorParams(size=embedder.dim, distance=Distance.COSINE))
    else:
        ensure_collection(client, collection, embedder.dim)

    # Cache manifest
    cache_dir = root.parent / ".ingest_cache"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"{collection}.json"
    cached_ids: set[str] = set()
    if use_cache and cache_file.exists():
        try:
            import json
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_ids = set(data.get("ids", []))
        except Exception:
            cached_ids = set()

    total_chunks = 0

    # Parallel parse files
    parsed: List[Tuple[Path, str, Dict]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(parse_file, p): p for p in paths}
        for fut in tqdm(as_completed(futs), total=len(futs), desc="parse"):
            p = futs[fut]
            try:
                text, meta = fut.result()
                parsed.append((p, text, meta))
            except Exception as e:
                print(f"[Parse error] {p}: {e}")

    for p, text, meta in tqdm(parsed, desc="ingest"):
        if write_parsed and out_dir is not None:
            try:
                out_path = out_dir / (p.stem + ".txt")
                out_path.write_text(text, encoding="utf-8")
            except Exception as e:
                print(f"[Write parsed error] {p}: {e}")

        chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)
        if not chunks:
            continue

        # prepare batch buffers
        texts: List[str] = []
        payloads: List[Dict] = []
        ids: List[str] = []
        for i, ch in enumerate(chunks):
            pid = chunk_uuid(p, i, ch)
            if use_cache and pid in cached_ids:
                continue
            texts.append(ch)
            ids.append(pid)
            payloads.append({
                "source_path": str(p),
                "rel_path": str(p.relative_to(root)),
                "chunk_index": i,
                "ext": meta.get("ext"),
                "title": meta.get("title"),
                "author": meta.get("author"),
                "text": ch[:1000],
            })
            # flush by embed batch size
            if len(texts) >= embed_batch_size:
                # concurrent embedding for this batch
                vecs = []
                with ThreadPoolExecutor(max_workers=embed_concurrency) as ex:
                    futs = [ex.submit(embedder.embed_texts, [t]) for t in texts]
                    for fut in futs:
                        vecs.append(fut.result()[0])
                # upsert in smaller batches if needed
                for s in range(0, len(vecs), upsert_batch_size):
                    e = s + upsert_batch_size
                    upsert_chunks(client, collection, vecs[s:e], payloads[s:e], ids=ids[s:e])
                total_chunks += len(texts)
                # update cache
                if use_cache:
                    cached_ids.update(ids)
                print(f"[Upserted] {len(texts)} chunks from {p}")
                texts, payloads, ids = [], [], []
        # flush remainder
        if texts:
            vecs = []
            with ThreadPoolExecutor(max_workers=embed_concurrency) as ex:
                futs = [ex.submit(embedder.embed_texts, [t]) for t in texts]
                for fut in futs:
                    vecs.append(fut.result()[0])
            for s in range(0, len(vecs), upsert_batch_size):
                e = s + upsert_batch_size
                upsert_chunks(client, collection, vecs[s:e], payloads[s:e], ids=ids[s:e])
            total_chunks += len(texts)
            if use_cache:
                cached_ids.update(ids)
            print(f"[Upserted] {len(texts)} chunks from {p}")

    # Persist cache
    if use_cache:
        try:
            import json
            cache_file.write_text(json.dumps({"ids": sorted(list(cached_ids))}, indent=2), encoding="utf-8")
        except Exception:
            pass

    print(f"Ingest complete. Total chunks: {total_chunks} into collection '{collection}'.")


def cli():
    parser = argparse.ArgumentParser(description="Ingest PDFs/EPUBs/TXT/MD into Qdrant using Gemini embeddings.")
    parser.add_argument("folder", help="Folder path to ingest")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--max-chars", type=int, default=2000)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-parsed", action="store_true", help="Write parsed text files for inspection")
    parser.add_argument("--parsed-dir", default=None, help="Directory to write parsed text (default: <folder>/../parsed_corpus)")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the target collection before ingesting")
    parser.add_argument("--embed-batch-size", type=int, default=32)
    parser.add_argument("--upsert-batch-size", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4, help="Parallel parse workers")
    parser.add_argument("--embed-concurrency", type=int, default=4, help="Parallel embedding requests per batch")
    parser.add_argument("--no-cache", action="store_true", help="Disable local ingest cache (re-embed all)")
    parser.add_argument("--profile", choices=["aggressive", "books", "conservative"], default=None)
    args = parser.parse_args()

    ingest(
        folder=args.folder,
        collection=args.collection,
        max_chars=args.max_chars,
        overlap=args.overlap,
        dry_run=args.dry_run,
        write_parsed=args.write_parsed,
        parsed_dir=args.parsed_dir,
        recreate=args.recreate,
        embed_batch_size=args.embed_batch_size,
        upsert_batch_size=args.upsert_batch_size,
        workers=args.workers,
        embed_concurrency=args.embed_concurrency,
        use_cache=not args.no_cache,
        profile=args.profile,
    )


if __name__ == "__main__":
    cli()
