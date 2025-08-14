from __future__ import annotations
from typing import List, Tuple

from quantum_aeon_fluxor.hermetic_engine__persistent_data.embedding.gemini_embedder import GeminiEmbedder
from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import (
    get_qdrant_client,
    search_by_vector,
)

DEFAULT_COLLECTION = "qaecore_longterm_v1"


def search_text(query: str, collection: str = DEFAULT_COLLECTION, k: int = 5) -> List[Tuple[float, dict]]:
    """Embed a query string and search Qdrant. Returns (score, payload) list."""
    embedder = GeminiEmbedder()
    vec = embedder.embed_texts([query])[0]
    client = get_qdrant_client()
    results = search_by_vector(client, collection, vec, limit=k)
    out: List[Tuple[float, dict]] = []
    for r in results:
        payload = r.payload or {}
        out.append((float(r.score), payload))
    return out
