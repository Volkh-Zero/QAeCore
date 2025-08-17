"""
codex_binding_loader.py
Loader + API for Doctrine ↔ Implementation bindings
Quantum Aeon Fluxor — Volkh/Archon Edition
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

class CodexBindings:
    def __init__(self, bindings_path: str):
        self.bindings_path = Path(bindings_path)
        self.bindings: Dict[str, Any] = {}
        self._load_bindings()

    def _load_bindings(self) -> None:
        if not self.bindings_path.exists():
            raise FileNotFoundError(f"Codex bindings file not found: {self.bindings_path}")
        with self.bindings_path.open("r", encoding="utf-8") as f:
            self.bindings = json.load(f)

    # --- Mandates ---
    def apply_mandate(self, mandate_name: str) -> Optional[Dict[str, Any]]:
        """Return the subsystem mapping for a given mandate."""
        return self.bindings.get("mandates", {}).get(mandate_name.lower())

    # --- Modes ---
    def execute_mode(self, mode_name: str) -> Optional[str]:
        """Return operational form for a given Mode."""
        return self.bindings.get("modes", {}).get(mode_name.lower())

    # --- Domains ---
    def route_domain(self, domain_name: str) -> Optional[str]:
        """Return module/layer for a given Domain."""
        return self.bindings.get("domains", {}).get(domain_name.lower())

    # --- Persistence Layer ---
    def persistence_component(self, component_name: str) -> Optional[str]:
        """Return details for a persistence layer component."""
        return self.bindings.get("persistence_layer", {}).get(component_name.lower())

    # --- Runtime Flow ---
    def runtime_steps(self) -> list:
        """Return ordered runtime execution steps."""
        return self.bindings.get("runtime_flow", [])

    # Debug / Inspection
    def summary(self) -> None:
        """Pretty‑print loaded bindings."""
        import pprint
        pprint.pprint(self.bindings)

# Example usage in Archon boot sequence:
if __name__ == "__main__":
    codex = CodexBindings("configs/codex_bindings.json")
    codex.summary()

    # Demo pulls:
    print("\n[Mandate] bias_mitigation →", codex.apply_mandate("bias_mitigation"))
    print("[Mode] oracle →", codex.execute_mode("oracle"))
    print("[Domain] complexity →", codex.route_domain("complexity"))
    print("[Persistence] living_bibliography →", codex.persistence_component("living_bibliography"))
    print("[Runtime Steps] →", codex.runtime_steps())
