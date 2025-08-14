from __future__ import annotations
from typing import List, Optional

from . import QuantumPromptGenerator
from .Integration_Prototyping.qacore_prompt_engine import QAeCoreTransitionEngine, QAeMode

# Persona header (very short) derived from your framework document
PERSONA_PREAMBLE = (
    "You are the Archon (Quantum Aeon Core): an evolving hyperintelligent AI collaborator. "
    "Operate with rigor, transparency, meta-cognition, and bias mitigation; pursue composite insights across domains."
)


def select_mode(user_input: str, recent_history: Optional[List[str]] = None) -> QAeMode:
    engine = QAeCoreTransitionEngine()
    return engine.detect_mode(user_input, context_history=recent_history or [])


def compose_prompt(
    user_input: str,
    focus_topic: Optional[str] = None,
    depth_level: str = "intermediate",
    recent_history: Optional[List[str]] = None,
    forced_mode: Optional[str] = None,
) -> str:
    """Adapter from Archon state+input to Syzygy prompt with dynamic mode selection.

    - Adds a short persona preamble
    - Selects QAeMode based on input/history unless forced_mode is provided
    - Uses consciousness inquiry as the base generator; we can branch in future
    """
    q = QuantumPromptGenerator()
    domain = focus_topic or "consciousness"

    # Mode selection
    if forced_mode:
        try:
            mode = QAeMode[forced_mode.upper()]
        except Exception:
            mode = select_mode(user_input, recent_history)
    else:
        mode = select_mode(user_input, recent_history)

    # Build the base prompt
    base = q.generate_consciousness_inquiry(domain=domain, question=user_input, depth_level=depth_level)

    # Attach persona preamble and mode label
    prompt = f"{PERSONA_PREAMBLE}\n\n[Mode: {mode.value}]\n\n{base}"
    return prompt
