from context7_persistent_docs.server import Context7PersistentDocsServer

srv = Context7PersistentDocsServer()
# Minimal smoke call to upstream Context7 via npx
resp = srv._call_context7_sync("resolve-library-id", {"libraryName": "qdrant"})
print("OK", isinstance(resp, dict), "keys", list(resp.keys())[:3])
