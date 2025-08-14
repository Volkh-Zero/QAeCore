from quantum_aeon_fluxor.utils.hash import chunk_uuid
from pathlib import Path
print(chunk_uuid(Path('X.md'), 0, 'hello world'))
