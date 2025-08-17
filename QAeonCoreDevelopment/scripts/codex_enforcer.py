"""
codex_enforcer.py
Doctrine enforcement middleware for Archon runtime
Quantum Aeon Fluxor — Volkh/Archon Edition
"""

from typing import Dict, Any, Tuple

class CodexEnforcer:
    def __init__(self, codex_bindings):
        """
        codex_bindings: instance of CodexBindings
        """
        self.codex = codex_bindings

    def validate_turn(self, turn_labels: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate a turn against Codex doctrine.
        turn_labels: { 'mandate': str, 'mode': str, 'domain': str }
        Returns: (is_valid, feedback_message)
        """
        # --- Mandate Check ---
        mandate_data = self.codex.apply_mandate(turn_labels.get('mandate', ''))
        if turn_labels.get('mandate') and not mandate_data:
            return False, f"[Codex Alert] Unknown Mandate: '{turn_labels['mandate']}'. Consider doctrine alignment."

        # --- Mode Check ---
        mode_data = self.codex.execute_mode(turn_labels.get('mode', ''))
        if turn_labels.get('mode') and not mode_data:
            return False, f"[Codex Alert] Mode '{turn_labels['mode']}' not found in doctrine map."

        # --- Domain Check ---
        domain_data = self.codex.route_domain(turn_labels.get('domain', ''))
        if turn_labels.get('domain') and not domain_data:
            return False, f"[Codex Alert] Domain '{turn_labels['domain']}' is outside current operational bounds."

        # If all present and valid:
        return True, "[Codex] Alignment confirmed."

    def enforce_and_prompt(self, turn_labels: Dict[str, str], move_payload: Any) -> Any:
        """
        Main call: validates labels; if invalid, returns corrective meta-prompt instead of executing move.
        """
        is_valid, feedback = self.validate_turn(turn_labels)
        if not is_valid:
            # Swap payload with doctrine correction request
            return {
                "type": "meta_prompt",
                "message": feedback + " Submit revised labels or justify exception."
            }
        return move_payload  # Pass through untouched if valid
