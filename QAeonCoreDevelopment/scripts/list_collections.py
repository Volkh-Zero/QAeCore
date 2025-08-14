import os
import sys
from typing import Optional

try:
    from quantum_aeon_fluxor.hermetic_engine__persistent_data.retrieval.qdrant_store import get_qdrant_client
except Exception as e:
    print("Import error:", e)
    sys.exit(1)

# Load .env from current or parent directories
try:
    from dotenv import load_dotenv, find_dotenv
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
except Exception:
    pass


def main(details: bool = False) -> int:
    url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_ENDPOINT")
    key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_API_TOKEN")
    print(f"QDRANT_URL={url}")
    client = get_qdrant_client()

    # Ping (lists collections implicitly in our helper, but call explicitly again)
    try:
        cols = client.get_collections()
    except Exception as e:
        print("Error calling get_collections():", e)
        return 2

    names = [c.name for c in getattr(cols, "collections", [])]
    if not names:
        print("No collections found.")
        return 0

    print("Collections:")
    for name in names:
        print(f"- {name}")

    if details:
        print("\nDetails:")
        for name in names:
            try:
                info = client.get_collection(name)
                # info should have vectors config etc.
                vectors = getattr(info, "vectors_count", None)
                cfg = getattr(info, "config", None)
                vsize = None
                if cfg and hasattr(cfg, "params") and getattr(cfg.params, "vectors_config", None):
                    vcfg = cfg.params.vectors_config
                    # vcfg can be mapping or single
                    if hasattr(vcfg, "size"):
                        vsize = vcfg.size
                print(f"- {name}: vectors={vectors}, vector_size={vsize}")
            except Exception as e:
                print(f"- {name}: error retrieving info: {e}")

    return 0


if __name__ == "__main__":
    details = "--details" in sys.argv
    sys.exit(main(details=details))
