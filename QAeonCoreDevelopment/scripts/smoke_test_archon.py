import os
from pathlib import Path

print('--- Import smoke tests ---')
try:
    import quantum_aeon_fluxor
    from quantum_aeon_fluxor.archon__supervisor_agent.archon import Archon
    from quantum_aeon_fluxor.hermetic_engine__persistent_data.conduits__clients.Gemini.GeminiClient import GeminiClient
    from quantum_aeon_fluxor.syzygy__conversational_framework.bridge import compose_prompt
    print('Imports OK')
except Exception as e:
    print('Import failure:', e)
    raise SystemExit(1)

print('\n--- Patch GeminiClient.query ---')
GeminiClient.query = lambda self, prompt: '[MOCKED RESPONSE] archon received prompt len=' + str(len(prompt))

print('\n--- Archon run_turn test (retrieval disabled) ---')
a = Archon()
a.retrieval_enabled = False
out = a.run_turn('Test inquiry about emergence and consciousness')
print('Archon output:', out[:120] + ('...' if len(out)>120 else ''))

state_dir = Path(__file__).resolve().parents[1] / 'quantum_aeon_fluxor' / 'hermetic_engine__persistent_data' / 'state'
print('State dir:', state_dir)
print('State files:', list(state_dir.glob('*.json')))

print('\n--- Indexer helpers test ---')
from quantum_aeon_fluxor.hermetic_engine__persistent_data.indexing.index_folder import chunk_text
from quantum_aeon_fluxor.utils.hash import chunk_id
sample = 'ABCDE'*1000
chunks = chunk_text(sample, max_chars=1000, overlap=100)
print('Chunks:', len(chunks), 'First chunk len:', len(chunks[0]))
print('cid example:', chunk_id(Path('X.txt'), 0, chunks[0])[:16])

print('\nALL TESTS COMPLETED')
