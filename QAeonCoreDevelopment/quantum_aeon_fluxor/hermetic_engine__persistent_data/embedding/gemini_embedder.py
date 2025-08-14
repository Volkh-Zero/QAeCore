from __future__ import annotations
from typing import List
import os
import google.generativeai as genai

DEFAULT_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")


class GeminiEmbedder:
    def __init__(self, model: str | None = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not set in environment.")
        genai.configure(api_key=api_key)
        self.model = model or DEFAULT_MODEL
        # Set expected dimensionality for collection setup (known for gemini-embedding-001)
        # If Google changes dims in future, we can fetch metadata; for now we hardcode 3072 per your plan
        self.dim = 3072

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Batch embed; google-generativeai supports batching via embed_content individually; we'll loop for now
        # For better performance, consider the batch API if/when available.
        vectors: List[List[float]] = []
        for t in texts:
            res = genai.embed_content(model=self.model, content=t)
            vec = res.get("embedding") or res.get("embedding", None)
            if vec is None and hasattr(res, "embedding"):
                vec = res.embedding
            if vec is None:
                raise RuntimeError("Gemini embedding response missing 'embedding'.")
            vectors.append(list(vec))
        return vectors
