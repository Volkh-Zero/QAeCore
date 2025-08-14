"""
Hermetic Engine - Persistent Data Management for Quantum Aeon Core.

This package handles data persistence, storage, and retrieval for the QAeCore system,
including knowledge bases, conversation history, and agent states.
"""

__display_name__ = "Hermetic Engine (Persistent Data)"

# Re-exports of common components
from .emergent_chironomicon__coherent_vectors.memory_logger import log_interaction as episodic_log_interaction
from .conduits__clients.Gemini.GeminiClient import GeminiClient

