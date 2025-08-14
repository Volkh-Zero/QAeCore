from __future__ import annotations
import argparse
import json
from typing import List, Tuple

# Ensure env loads if present
try:
    from dotenv import load_dotenv, find_dotenv
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
except Exception:
    pass

from .search_text import search_text, DEFAULT_COLLECTION  # noqa: E402


def cli():
    parser = argparse.ArgumentParser(description="Search Qdrant collection using Gemini-embedded query.")
    parser.add_argument("text", help="Query text")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Collection name")
    parser.add_argument("--k", type=int, default=5, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    results = search_text(args.text, collection=args.collection, k=args.k)

    if args.json:
        out = [
            {"score": score, **(payload or {})}
            for (score, payload) in results
        ]
        print(json.dumps(out, indent=2))
        return

    if not results:
        print("No results.")
        return

    print(f"Top {len(results)} from collection='{args.collection}':")
    for score, payload in results:
        path = (payload or {}).get("rel_path") or (payload or {}).get("path")
        snippet = (payload or {}).get("text") or ""
        snippet = snippet.replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        print(f"- [{score:.3f}] {path} :: {snippet}")


if __name__ == "__main__":
    cli()
