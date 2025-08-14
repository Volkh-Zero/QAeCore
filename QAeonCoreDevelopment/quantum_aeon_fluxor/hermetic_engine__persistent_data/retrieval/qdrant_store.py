from __future__ import annotations
from typing import List, Optional, Iterable
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ResponseHandlingException


def _normalize_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url


def _toggle_port(url: str) -> str:
    # if has :6333 remove it, else add :6333
    if ":6333" in url:
        return url.replace(":6333", "")
    # insert :6333 before path (if any)
    if url.startswith("https://"):
        rest = url[len("https://"):]
        return "https://" + rest.split("/", 1)[0] + ":6333" + ("/" + rest.split("/", 1)[1] if "/" in rest else "")
    if url.startswith("http://"):
        rest = url[len("http://"):]
        return "http://" + rest.split("/", 1)[0] + ":6333" + ("/" + rest.split("/", 1)[1] if "/" in rest else "")
    return url


def get_qdrant_client() -> QdrantClient:
    # Load .env if available
    try:
        from dotenv import load_dotenv, find_dotenv
        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(env_path)
    except Exception:
        pass

    url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_ENDPOINT")
    api_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_API_TOKEN")
    if not url:
        url = "http://localhost:6333"
    url = _normalize_url(url)

    def _try(url_try: str) -> QdrantClient:
        client = QdrantClient(url=url_try, api_key=api_key, timeout=60.0)
        # quick ping to validate connectivity/auth
        client.get_collections()
        return client

    # attempt primary
    try:
        return _try(url)
    except Exception:
        # attempt toggled port
        return _try(_toggle_port(url))


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    exists = False
    try:
        coll = client.get_collection(name)
        exists = True
        # Optionally validate dims
        # if coll.vectors_count != vector_size: ...
    except Exception:
        exists = False
    if not exists:
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(
    client: QdrantClient,
    collection: str,
    vectors: List[List[float]],
    payloads: List[dict],
    ids: Optional[List[str]] = None,
) -> None:
    if ids is None:
        ids = [str(i) for i in range(1, len(vectors) + 1)]
    points = [
        PointStruct(id=i, vector=v, payload=p) for i, v, p in zip(ids, vectors, payloads)
    ]
    client.upsert(collection_name=collection, points=points)


def search_by_vector(
    client: QdrantClient,
    collection: str,
    query_vector: List[float],
    limit: int = 5,
):
    return client.search(collection_name=collection, query_vector=query_vector, limit=limit)
