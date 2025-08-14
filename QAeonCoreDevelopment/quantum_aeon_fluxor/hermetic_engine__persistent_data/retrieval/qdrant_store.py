from __future__ import annotations
from typing import List, Optional, Iterable
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct


def get_qdrant_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_ENDPOINT")
    if not url:
        # Fallback to example
        url = "http://localhost:6333"
    api_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_API_TOKEN")
    return QdrantClient(url=url, api_key=api_key)


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
    ids: Optional[List[int]] = None,
) -> None:
    if ids is None:
        ids = list(range(1, len(vectors) + 1))
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
