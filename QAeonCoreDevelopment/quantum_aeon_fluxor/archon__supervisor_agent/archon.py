from __future__ import annotations
from typing import Optional

from quantum_aeon_fluxor.archon__supervisor_agent.state import ArchonState
from quantum_aeon_fluxor.syzygy__conversational_framework import __display_name__ as SYZ_NAME  # noqa: F401
from quantum_aeon_fluxor.syzygy__conversational_framework.bridge import compose_prompt
from quantum_aeon_fluxor.hermetic_engine__persistent_data import (
    episodic_log_interaction,
    GeminiClient,
)
from quantum_aeon_fluxor.hermetic_engine__persistent_data.longterm import write_blob


class Archon:
    """Minimal Archon orchestrator.

    - Maintains state
    - Composes prompts via Syzygy
    - Queries Gemini
    - Logs episodic transcript
    - Writes optional long-term memory blobs when tagged
    """

    def __init__(self):
        self.state = ArchonState.load()
        self.client = GeminiClient()

    def run_turn(self, user_input: str, *, depth_level: str = "intermediate", retain: bool = False) -> str:
        # Compose prompt using Syzygy bridge
        prompt = compose_prompt(user_input, focus_topic=self.state.focus_topic, depth_level=depth_level)

        # Query Gemini
        response_text = self.client.query(prompt)

        # Log transcript
        episodic_log_interaction("Volkh", user_input)
        episodic_log_interaction("Archon", response_text)

        # Optional retention (opaque blob)
        if retain:
            write_blob(response_text, tags=["archon", "response", self.state.phase])

        # Update state (simple heuristic placeholder)
        if not self.state.focus_topic and len(user_input) > 0:
            self.state.focus_topic = user_input[:96]
        if "contradiction" in response_text.lower():
            self.state.flag_contradiction("Model mentioned contradiction in latest turn")
        self.state.save()
        return response_text
