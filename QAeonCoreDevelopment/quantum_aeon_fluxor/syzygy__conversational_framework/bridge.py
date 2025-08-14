from __future__ import annotations
from typing import List, Optional

from . import QuantumPromptGenerator


def compose_prompt(user_input: str, focus_topic: Optional[str] = None, depth_level: str = "intermediate") -> str:
    """Thin adapter from Archon state+input to Syzygy prompt.

    For now, use the consciousness inquiry generator.
    """
    q = QuantumPromptGenerator()
    domain = focus_topic or "consciousness"
    return q.generate_consciousness_inquiry(domain=domain, question=user_input, depth_level=depth_level)
