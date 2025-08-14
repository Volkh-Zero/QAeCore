"""
Syzygy - Framework Integration for Quantum Aeon Core.

This package handles the integration of various frameworks and external systems
with the QAeCore architecture, including prompt engineering and model interfaces.
"""

__display_name__ = "Syzygy (ConversationalFramework)"

# Import key components
from .Integration_Prototyping.qacore_prompt_engine import (
    QuantumPromptGenerator,
    QAeMode,
    PlausibilityLevel,
    QAeCorePromptLibrary
)
